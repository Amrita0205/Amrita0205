#!/usr/bin/env python3
"""Generate the profile statistics for the repository owner."""

from collections import defaultdict
from datetime import date, timedelta
import json
import os
import re
from pathlib import Path
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
LOGIN = os.environ.get("GH_LOGIN", "Amrita0205")
TOKEN = os.environ.get("GITHUB_TOKEN")
API_URL = "https://api.github.com/graphql"
COLORS = ["#d9f99d", "#a3e635", "#65a30d", "#3f6212", "#254b08"]


def graphql(query, variables):
    if not TOKEN:
        raise SystemExit("GITHUB_TOKEN is required")
    payload = json.dumps({"query": query, "variables": variables}).encode()
    request = Request(API_URL, data=payload, headers={
        "Authorization": f"bearer {TOKEN}",
        "Content-Type": "application/json",
        "User-Agent": "Amrita0205-profile-stats",
    })
    with urlopen(request, timeout=30) as response:
        result = json.load(response)
    if result.get("errors"):
        raise SystemExit("GitHub GraphQL error: " + result["errors"][0]["message"])
    return result["data"]


def fetch_data():
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          totalCommitContributions
          totalPullRequestContributions
          totalIssueContributions
          totalPullRequestReviewContributions
          totalRepositoryContributions
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount contributionLevel } }
          }
        }
                repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {
                    totalCount
          nodes { languages(first: 10, orderBy: {field: SIZE, direction: DESC})
            { edges { size node { name color } } } }
        }
      }
    }
    """
    end = date.today()
    start = end - timedelta(days=365)
    return graphql(query, {
        "login": LOGIN,
        "from": f"{start.isoformat()}T00:00:00Z",
        "to": f"{end.isoformat()}T23:59:59Z",
    })["user"]


def flatten_days(user):
    calendar = user["contributionsCollection"]["contributionCalendar"]
    days = [day for week in calendar["weeks"] for day in week["contributionDays"]]
    return calendar["totalContributions"], sorted(days, key=lambda item: item["date"])


def streaks(days):
    active = {day["date"] for day in days if day["contributionCount"]}
    current = 0
    cursor = date.today()
    while cursor.isoformat() in active:
        current += 1
        cursor -= timedelta(days=1)
    longest = run = 0
    best_start = best_end = None
    run_start = None
    for day in days:
        if day["contributionCount"]:
            run_start = run_start or date.fromisoformat(day["date"])
            run += 1
            if run > longest:
                longest = run
                best_start = run_start
                best_end = date.fromisoformat(day["date"])
        else:
            run = 0
            run_start = None
    return current, longest, best_start, best_end


def languages(user):
    totals = defaultdict(int)
    colors = {}
    for repository in user["repositories"]["nodes"]:
        for edge in repository["languages"]["edges"]:
            name = edge["node"]["name"]
            totals[name] += edge["size"]
            colors[name] = edge["node"]["color"] or "#a3e635"
    top = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    repo_counts = defaultdict(int)
    for repository in user["repositories"]["nodes"]:
        for edge in repository["languages"]["edges"]:
            repo_counts[edge["node"]["name"]] += 1
    return top[:5], colors, repo_counts


def replace_text(svg, marker, value):
    pattern = rf'(<text[^>]*{re.escape(marker)}[^>]*>)[^<]*(</text>)'
    return re.sub(pattern, rf'\g<1>{value}\g<2>', svg, count=1)


def line_path(days):
    weeks = [sum(day["contributionCount"] for day in days[index:index + 7]) for index in range(0, len(days), 7)]
    weeks += [0] * (53 - len(weeks))
    peak = max(weeks) or 1
    points = [(index * 620 / 52, 138 - value / peak * 48) for index, value in enumerate(weeks[:53])]
    return "M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in points)


def year_grid(days):
    levels = " :+#@"
    peak = max((day["contributionCount"] for day in days), default=1)
    cells = {(day["date"]): levels[min(4, round(day["contributionCount"] / peak * 4))]
             for day in days}
    first = date.fromisoformat(days[0]["date"])
    rows = []
    for row in range(7):
        row_chars = []
        for week in range(53):
            current = first + timedelta(days=week * 7 + row)
            row_chars.append(cells.get(current.isoformat(), " ") * 2)
        rows.append("".join(row_chars))
    return rows


LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]
HEAT_LIGHT = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
HEAT_DARK = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def shared_style():
    """Reuse the inlined JetBrains Mono and text colours from stats.svg."""
    stats = (ROOT / "stats.svg").read_text(encoding="utf-8")
    return re.search(r"<style>.*?</style>", stats, re.S).group(0)


def svg_open(width, height):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" fill="none" font-family="JBMono,ui-monospace,'
            f'SFMono-Regular,Menlo,Consolas,&apos;Liberation Mono&apos;,monospace">', shared_style()]


def write_heatmap(days):
    """GitHub-style contribution calendar: one square per day, weeks as columns."""
    left, top, pitch, cell = 30, 20, 11, 9
    first = date.fromisoformat(days[0]["date"])
    sunday = first - timedelta(days=(first.weekday() + 1) % 7)
    weeks = ((date.fromisoformat(days[-1]["date"]) - sunday).days // 7) + 1
    width, height = 620, top + 7 * pitch + 26
    light = "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(HEAT_LIGHT))
    dark = "".join(f".l{i}{{fill:{c}}}" for i, c in enumerate(HEAT_DARK))
    svg = svg_open(width, height)
    svg.append(f"<style>{light}@media(prefers-color-scheme:dark){{{dark}}}</style>")
    for row, label in ((1, "mon"), (3, "wed"), (5, "fri")):
        svg.append(f'<text x="0" y="{top + row * pitch + cell - 1}" class="m-f" font-size="9">{label}</text>')
    month = None
    labels = []
    columns = defaultdict(list)
    for day in days:
        current = date.fromisoformat(day["date"])
        column = (current - sunday).days // 7
        row = (current.weekday() + 1) % 7
        if row == 0 and current.month != month:
            month = current.month
            # a new month crowding the previous label wins, like GitHub drops the partial first month
            if labels and column - labels[-1][0] < 3:
                labels.pop()
            if column <= weeks - 2:
                labels.append((column, f"{current:%b}".lower()))
        level = LEVELS.index(day.get("contributionLevel", "NONE"))
        title = f'{day["contributionCount"]} on {current:%b %d}'.lower()
        columns[column].append(f'<rect x="{left + column * pitch}" y="{top + row * pitch}" width="{cell}" '
                               f'height="{cell}" rx="2" class="l{level}"><title>{title}</title></rect>')
    for column, name in labels:
        svg.append(f'<text x="{left + column * pitch}" y="10" class="m-f" font-size="9">{name}</text>')
    for column in sorted(columns):
        # sweep the weeks in left to right, once
        svg.append(f'<g opacity="0"><animate attributeName="opacity" from="0" to="1" '
                   f'begin="{0.1 + column * 0.02:.2f}s" dur="0.3s" fill="freeze"/>{"".join(columns[column])}</g>')
    legend_y = top + 7 * pitch + 12
    x = width - 5 * pitch - 30
    svg.append(f'<text x="{x - 6}" y="{legend_y + cell - 1}" class="m-f" font-size="9" text-anchor="end">less</text>')
    for level in range(5):
        svg.append(f'<rect x="{x + level * pitch}" y="{legend_y}" width="{cell}" height="{cell}" rx="2" class="l{level}"/>')
    svg.append(f'<text x="{x + 5 * pitch + 4}" y="{legend_y + cell - 1}" class="m-f" font-size="9">more</text>')
    svg.append("</svg>")
    (ROOT / "heatmap.svg").write_text("".join(svg), encoding="utf-8")


def write_activity(user):
    """Share of commits, pull requests, issues and reviews, like GitHub's activity overview."""
    collection = user["contributionsCollection"]
    kinds = [
        ("commits", collection["totalCommitContributions"]),
        ("pull requests", collection["totalPullRequestContributions"]),
        ("issues", collection["totalIssueContributions"]),
        ("code review", collection["totalPullRequestReviewContributions"]),
    ]
    total = max(sum(count for _, count in kinds), 1)
    width, row_height, bar_x, bar_w = 620, 22, 130, 400
    svg = svg_open(width, 12 + len(kinds) * row_height)
    svg.append("<style>.g{fill:#40c463}.t{fill:#6e7681;opacity:.13}"
               "@media(prefers-color-scheme:dark){.g{fill:#39d353}.t{fill:#c9d1d9;opacity:.16}}</style>")
    for index, (label, count) in enumerate(kinds):
        y = 12 + index * row_height
        share = count / total
        begin = 0.1 + index * 0.12
        svg.append(f'<text x="0" y="{y + 8}" class="d-f" font-size="12">{label}</text>')
        svg.append(f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="10" rx="2" class="t"/>')
        svg.append(f'<rect x="{bar_x}" y="{y}" width="0" height="10" rx="2" class="g">'
                   f'<animate attributeName="width" from="0" to="{bar_w * share:.1f}" begin="{begin:.2f}s" '
                   f'dur="0.6s" fill="freeze"/></rect>')
        svg.append(f'<text x="{width}" y="{y + 8}" class="e-f" font-size="12" text-anchor="end">'
                   f'{count:,} <tspan class="m-f">{share:.0%}</tspan></text>')
    svg.append("</svg>")
    (ROOT / "activity.svg").write_text("".join(svg), encoding="utf-8")


def write_stats(total, current, longest, best_start, best_end, top_languages, colors, repo_counts, days):
    stats_path = ROOT / "stats.svg"
    stats = stats_path.read_text(encoding="utf-8")
    stats = replace_text(stats, 'x="0" y="50"', f"{total:,}")
    stats = replace_text(stats, 'x="620" y="30"', str(sum(bool(day["contributionCount"]) for day in days)))
    best_week = max((sum(day["contributionCount"] for day in days[index:index + 7]) for index in range(0, len(days), 7)), default=0)
    stats = replace_text(stats, 'x="620" y="70"', str(best_week))
    path = line_path(days)
    stats = re.sub(r'(<path d=")[^"]+(" class="w")', rf'\g<1>{path}\g<2>', stats, count=1)
    stats = re.sub(r'(<path d=")[^"]+(" class="d-s")', rf'\g<1>{path}\g<2>', stats, count=1)
    stats_path.write_text(stats, encoding="utf-8")

    streak_path = ROOT / "streak.svg"
    streak = streak_path.read_text(encoding="utf-8")
    streak = replace_text(streak, 'x="34" y="44"', str(current))
    streak = replace_text(streak, 'x="344.0" y="44"', str(longest))
    streak_dates = "&#8212;"
    if best_start and best_end:
        streak_dates = f"{best_start:%b %d} &#8211; {best_end:%b %d}".lower()
    streak = replace_text(streak, 'x="344.0" y="80"', streak_dates)
    streak_path.write_text(streak, encoding="utf-8")

    lang_path = ROOT / "langs.svg"
    lang = lang_path.read_text(encoding="utf-8")
    lang = re.sub(r'\s(?:textLength|lengthAdjust)="[^"]*"', "", lang)
    total_bytes = max(sum(value for _, value in top_languages), 1)
    for index in range(5):
        name, value = top_languages[index] if index < len(top_languages) else ("", 0)
        y = 34 + index * 22
        lang = replace_text(lang, f'x="34" y="{y}"', escape(name))
        lang = replace_text(lang, f'x="306.0" y="{y}"', f"{value / total_bytes:.0%}" if value else "")
        lang = replace_text(lang, f'x="342.0" y="{y}"', escape(name))
        lang = replace_text(lang, f'x="614.0" y="{y}"', str(repo_counts[name]) if name else "")
        if len(name) > 12:
            for x in ("34", "342.0"):
                lang = re.sub(
                    rf'(<text x="{x}" y="{y}"[^>]*)(>)',
                    rf'\1 textLength="78" lengthAdjust="spacingAndGlyphs"\2',
                    lang,
                    count=1,
                )
    lang_path.write_text(lang, encoding="utf-8")

    year_path = ROOT / "year.svg"
    year = year_path.read_text(encoding="utf-8")
    year = replace_text(year, 'x="34" y="32"', f"{sum(bool(day['contributionCount']) for day in days)} of {len(days)} days had a contribution")
    for index, row in enumerate(year_grid(days)):
        year = replace_text(year, f'y="{52.6 + index * 11}"', row)
    year_path.write_text(year, encoding="utf-8")


def main():
    user = fetch_data()
    total, days = flatten_days(user)
    current, longest, best_start, best_end = streaks(days)
    top_languages, colors, repo_counts = languages(user)
    write_stats(total, current, longest, best_start, best_end, top_languages, colors, repo_counts, days)
    write_heatmap(days)
    write_activity(user)
    print(f"generated stats for {LOGIN}")


if __name__ == "__main__":
    main()
