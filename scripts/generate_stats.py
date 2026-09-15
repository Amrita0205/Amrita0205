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
          contributionCalendar {
            totalContributions
            weeks { contributionDays { date contributionCount } }
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
    print(f"generated stats for {LOGIN}")


if __name__ == "__main__":
    main()
