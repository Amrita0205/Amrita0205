#!/usr/bin/env python3
"""Generate the profile statistics for the repository owner."""

from collections import defaultdict
from datetime import date, timedelta
import json
import os
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
    for day in days:
        run = run + 1 if day["contributionCount"] else 0
        longest = max(longest, run)
    return current, longest


def languages(user):
    totals = defaultdict(int)
    colors = {}
    for repository in user["repositories"]["nodes"]:
        for edge in repository["languages"]["edges"]:
            name = edge["node"]["name"]
            totals[name] += edge["size"]
            colors[name] = edge["node"]["color"] or "#a3e635"
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)[:6], colors


def svg_start(height):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="620" height="{height}" '
            f'viewBox="0 0 620 {height}" fill="none" font-family="ui-monospace,Consolas,monospace">'
            '<style>text{fill:#d7e4d0} .muted{fill:#8da18a} .accent{fill:#bef264}</style>')


def write_stats(total, current, longest, top_languages, colors, days):
    max_count = max((day["contributionCount"] for day in days), default=1)
    cells = []
    for index, day in enumerate(days):
        x = 34 + (index % 53) * 10
        y = 78 + (index // 53) * 10
        level = min(4, round(day["contributionCount"] / max_count * 4)) if day["contributionCount"] else 0
        cells.append(f'<rect x="{x}" y="{y}" width="7" height="7" rx="1" fill="{COLORS[level]}"/>')
    stats = svg_start(148)
    stats += f'<text x="34" y="36" font-size="28" font-weight="700" class="accent">{total:,}</text>'
    stats += '<text x="34" y="55" font-size="12" class="muted">contributions in the last year</text>'
    stats += f'<text x="330" y="36" font-size="16" class="accent">{current}</text><text x="330" y="55" font-size="11" class="muted">current streak</text>'
    stats += f'<text x="455" y="36" font-size="16" class="accent">{longest}</text><text x="455" y="55" font-size="11" class="muted">longest streak</text>'
    stats += "".join(cells) + "</svg>"
    (ROOT / "stats.svg").write_text(stats, encoding="utf-8")

    streak = svg_start(96) + '<text x="34" y="18" font-size="10" class="muted">CONTRIBUTION STREAKS</text>'
    streak += f'<text x="34" y="52" font-size="28" class="accent">{current}</text><text x="34" y="72" font-size="11" class="muted">current streak</text>'
    streak += f'<text x="260" y="52" font-size="28" class="accent">{longest}</text><text x="260" y="72" font-size="11" class="muted">longest streak</text></svg>'
    (ROOT / "streak.svg").write_text(streak, encoding="utf-8")

    lang = svg_start(142) + '<text x="34" y="22" font-size="10" class="muted">LANGUAGES IN OWNED REPOSITORIES</text>'
    total_bytes = max(sum(value for _, value in top_languages), 1)
    for index, (name, value) in enumerate(top_languages):
        y = 48 + index * 14
        width = round(value / total_bytes * 350)
        lang += f'<text x="34" y="{y}" font-size="11">{escape(name)}</text><rect x="160" y="{y - 9}" width="350" height="8" fill="#263525"/><rect x="160" y="{y - 9}" width="{width}" height="8" fill="{colors[name]}"/><text x="525" y="{y}" font-size="10" class="muted">{value / total_bytes:.0%}</text>'
    (ROOT / "langs.svg").write_text(lang + "</svg>", encoding="utf-8")

    year = svg_start(80) + f'<text x="34" y="22" font-size="10" class="muted">THE YEAR</text><text x="34" y="42" font-size="12">{sum(bool(day["contributionCount"]) for day in days)} of {len(days)} days had a contribution</text></svg>'
    (ROOT / "year.svg").write_text(year, encoding="utf-8")


def main():
    user = fetch_data()
    total, days = flatten_days(user)
    current, longest = streaks(days)
    top_languages, colors = languages(user)
    write_stats(total, current, longest, top_languages, colors, days)
    print(f"generated stats for {LOGIN}")


if __name__ == "__main__":
    main()
