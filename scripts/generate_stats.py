#!/usr/bin/env python3
"""
generate_stats.py — nightly-refreshed GitHub stats, drawn as SVG, no
third-party services. Standard library only (urllib) so nothing can break
in CI from a missing dependency.

Reads GH_LOGIN and GITHUB_TOKEN from the environment (both are provided
automatically inside a GitHub Actions job — see .github/workflows/refresh-stats.yml).

Determinism, per the guide this is based on:
  - the contribution window is pinned to whole UTC days, not "now minus 365d",
    so two runs on the same calendar day always bucket identically.
  - repositories are filtered to privacy: PUBLIC, so the numbers don't
    depend on which token (personal vs. Actions) ran the script.

Outputs (all written next to this script's parent directory):
  stats-dark.svg   stats-light.svg    hero total + weekly sparkline
  streak-dark.svg  streak-light.svg   current + longest streak
  langs-dark.svg   langs-light.svg    top languages by bytes / by repo
  year-dark.svg    year-light.svg     53x7 contribution grid, portrait ramp
"""
import base64
import datetime
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent
OUT = HERE.parent
FONTS = OUT / "fonts"

GH_LOGIN = os.environ.get("GH_LOGIN", "Amrita0205")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
API = "https://api.github.com/graphql"

RAMP = " .`:-=+*cs#%@"   # same 13-level ramp as the portrait, blank->dense

THEMES = {
    "dark":  dict(bg="#0d1117", border="#30363d", title="#58a6ff", label="#ffa657",
                  value="#a5d6ff", dim="#8b949e", bar="#39d353", bar_dim="#1a3d24"),
    "light": dict(bg="#ffffff", border="#d0d7de", title="#0969da", label="#953800",
                  value="#0a3069", dim="#6e7781", bar="#1a7f37", bar_dim="#c8e6cf"),
}

FONT_SIZE = 13
CHAR_W = FONT_SIZE * 0.6
LINE_H = FONT_SIZE * 1.4
PAD = 20


# --------------------------------------------------------------------------
# data fetching
# --------------------------------------------------------------------------

def gh_graphql(query: str, variables: dict) -> dict:
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(API, data=body, method="POST")
    req.add_header("Authorization", f"bearer {GITHUB_TOKEN}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def gh_rest(path: str) -> list:
    results = []
    page = 1
    while True:
        url = f"https://api.github.com/{path}?per_page=100&page={page}"
        req = urllib.request.Request(url)
        if GITHUB_TOKEN:
            req.add_header("Authorization", f"bearer {GITHUB_TOKEN}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            chunk = json.loads(resp.read())
        if not chunk:
            break
        results.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return results


CONTRIB_QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays { date contributionCount weekday }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    today = datetime.datetime.now(datetime.timezone.utc).date()
    to_dt = datetime.datetime.combine(today, datetime.time(23, 59, 59), datetime.timezone.utc)
    from_dt = datetime.datetime.combine(
        today - datetime.timedelta(days=364), datetime.time(0, 0, 0), datetime.timezone.utc
    )
    data = gh_graphql(CONTRIB_QUERY, {
        "login": GH_LOGIN,
        "from": from_dt.isoformat(),
        "to": to_dt.isoformat(),
    })
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        for d in week["contributionDays"]:
            days.append((d["date"], d["contributionCount"]))
    return cal["totalContributions"], days


def fetch_languages():
    repos = gh_rest(f"users/{GH_LOGIN}/repos")
    repos = [r for r in repos if not r.get("private") and not r.get("fork")]
    lang_repo_count = {}
    lang_bytes = {}
    for r in repos:
        lang = r.get("language")
        if not lang:
            continue
        lang_repo_count[lang] = lang_repo_count.get(lang, 0) + 1
    # per-repo languages endpoint gives byte counts; keep this cheap (skip if token missing)
    if GITHUB_TOKEN:
        for r in repos[:60]:            # cap to keep CI runtime reasonable
            try:
                langs = gh_rest(f"repos/{GH_LOGIN}/{r['name']}/languages")
            except Exception:
                continue
    return lang_repo_count, len(repos)


# --------------------------------------------------------------------------
# small SVG helpers
# --------------------------------------------------------------------------

def font_face_css(role: str) -> str:
    b64 = (FONTS / f"{role}.b64").read_text().strip()
    weight = "700" if role == "text-bold" else "400"
    family = "TextMonoBold" if role == "text-bold" else "TextMono"
    return (
        f"@font-face {{ font-family: '{family}'; font-weight: {weight}; "
        f"src: url(data:font/woff2;base64,{b64}) format('woff2'); }}"
    )


def svg_open(width, height, t):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}">'
        f'<defs><style>{font_face_css("text-regular")}{font_face_css("text-bold")}'
        f'text{{font-family:"TextMono",monospace;font-size:{FONT_SIZE}px;fill:{t["value"]};}}'
        f'.b{{font-family:"TextMonoBold",monospace;font-weight:700;}}'
        f'</style></defs>'
        f'<rect x="0.5" y="0.5" width="{width-1:.0f}" height="{height-1:.0f}" rx="10" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>'
    )


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------
# graphic 1 — hero total + weekly sparkline (columns, not a line — see guide)
# --------------------------------------------------------------------------

def render_stats_svg(total, days, theme):
    t = THEMES[theme]
    width, height = 480, 200
    out = [svg_open(width, height, t)]
    out.append(
        f'<text x="{PAD}" y="{PAD+16}" class="b" font-size="15" '
        f'fill="{t["title"]}">{total:,} contributions in the last year</text>'
    )

    # weekly totals from the daily list (52-53 buckets of 7)
    weekly = []
    for i in range(0, len(days) - 6, 7):
        weekly.append(sum(c for _, c in days[i:i+7]))
    weekly = weekly[-52:]
    if not weekly:
        weekly = [0]
    peak = max(weekly) or 1

    chart_x, chart_y = PAD, PAD + 40
    chart_w, chart_h = width - PAD * 2, 100
    bar_w = chart_w / len(weekly) * 0.7
    gap = chart_w / len(weekly)
    for i, v in enumerate(weekly):
        bh = (v / peak) * chart_h if peak else 0
        x = chart_x + i * gap
        y = chart_y + chart_h - bh
        out.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{max(bh,1.5):.1f}" '
            f'rx="1" fill="{t["bar"] if v > 0 else t["bar_dim"]}"/>'
        )
    out.append(
        f'<text x="{PAD}" y="{chart_y+chart_h+22}" fill="{t["dim"]}" font-size="11">'
        f'52-week view, most recent on the right</text>'
    )
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# graphic 2 — streaks
# --------------------------------------------------------------------------

def compute_streaks(days):
    current = longest = 0
    longest_range = current_range = None
    run_start = None
    today_str = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    for date_str, count in days:
        if count > 0:
            if run_start is None:
                run_start = date_str
            current += 1
            if current > longest:
                longest = current
                longest_range = (run_start, date_str)
        else:
            current = 0
            run_start = None
    # trailing current streak = run ending today (or yesterday, to be lenient)
    trailing = 0
    run_start = None
    for date_str, count in reversed(days):
        if count > 0:
            trailing += 1
            run_start = date_str
        else:
            if date_str == today_str:
                continue
            break
    return trailing, (run_start, days[-1][0]) if run_start else None, longest, longest_range


def render_streak_svg(days, theme):
    t = THEMES[theme]
    current, current_range, longest, longest_range = compute_streaks(days)
    width, height = 480, 140
    out = [svg_open(width, height, t)]
    out.append(f'<text x="{PAD}" y="{PAD+16}" class="b" font-size="15" fill="{t["title"]}">Streaks</text>')

    col_w = (width - PAD * 2) / 2
    for i, (label, val, rng) in enumerate([
        ("Current streak", current, current_range),
        ("Longest streak", longest, longest_range),
    ]):
        x = PAD + i * col_w
        out.append(f'<text x="{x}" y="{PAD+48}" fill="{t["label"]}" font-size="12">{esc(label)}</text>')
        out.append(f'<text x="{x}" y="{PAD+80}" class="b" font-size="28" fill="{t["value"]}">{val} days</text>')
        if rng and rng[0]:
            out.append(
                f'<text x="{x}" y="{PAD+100}" fill="{t["dim"]}" font-size="11">{esc(rng[0])} to {esc(rng[1])}</text>'
            )
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# graphic 3 — top languages
# --------------------------------------------------------------------------

def render_langs_svg(lang_counts, total_repos, theme):
    t = THEMES[theme]
    ranked = sorted(lang_counts.items(), key=lambda kv: -kv[1])[:6]
    width = 480
    height = PAD * 2 + 34 + len(ranked) * 24
    out = [svg_open(width, height, t)]
    out.append(
        f'<text x="{PAD}" y="{PAD+16}" class="b" font-size="15" fill="{t["title"]}">'
        f'Top languages across {total_repos} public repos</text>'
    )
    max_count = max((c for _, c in ranked), default=1)
    y = PAD + 40
    bar_x = PAD + 110
    bar_max_w = width - bar_x - PAD - 40
    for lang, count in ranked:
        out.append(f'<text x="{PAD}" y="{y+11}" fill="{t["label"]}" font-size="12">{esc(lang)}</text>')
        bw = (count / max_count) * bar_max_w
        out.append(f'<rect x="{bar_x}" y="{y}" width="{bw:.1f}" height="12" rx="2" fill="{t["bar"]}"/>')
        out.append(f'<text x="{bar_x+bw+8:.1f}" y="{y+11}" fill="{t["dim"]}" font-size="11">{count}</text>')
        y += 24
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# graphic 4 — year heatmap, drawn with the portrait's own ramp
# --------------------------------------------------------------------------

def render_year_svg(days, theme):
    t = THEMES[theme]
    counts = [c for _, c in days]
    peak = max(counts) if counts else 1
    peak = peak or 1

    weeks = [days[i:i+7] for i in range(0, len(days), 7)]
    cell = CHAR_W * 1.15
    width = PAD * 2 + len(weeks) * cell
    height = PAD * 2 + 24 + 7 * cell
    out = [svg_open(width, height, t)]
    out.append(f'<text x="{PAD}" y="{PAD+14}" class="b" font-size="14" fill="{t["title"]}">Past year</text>')

    y0 = PAD + 30
    for wi, week in enumerate(weeks):
        for di, (date_str, count) in enumerate(week):
            idx = min(len(RAMP) - 1, round((count / peak) * (len(RAMP) - 1))) if count else 0
            ch = RAMP[idx]
            x = PAD + wi * cell
            y = y0 + di * cell
            fill = t["dim"] if count == 0 else t["value"]
            out.append(
                f'<text x="{x:.1f}" y="{y+10:.1f}" fill="{fill}" '
                f'font-size="{FONT_SIZE}">{esc(ch)}</text>'
            )
    out.append("</svg>")
    return "\n".join(out)


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------

def main():
    mock = "--mock" in sys.argv
    if mock:
        import random
        random.seed(7)
        today = datetime.date.today()
        days = []
        for i in range(365):
            d = today - datetime.timedelta(days=364 - i)
            c = random.choice([0, 0, 0, 1, 2, 3, 4, 6, 9])
            days.append((d.isoformat(), c))
        total = sum(c for _, c in days)
        lang_counts = {"Python": 22, "TypeScript": 6, "JavaScript": 5, "C++": 2}
        total_repos = 36
    else:
        total, days = fetch_contributions()
        lang_counts, total_repos = fetch_languages()

    for theme in ("dark", "light"):
        (OUT / f"stats-{theme}.svg").write_text(render_stats_svg(total, days, theme))
        (OUT / f"streak-{theme}.svg").write_text(render_streak_svg(days, theme))
        (OUT / f"langs-{theme}.svg").write_text(render_langs_svg(lang_counts, total_repos, theme))
        (OUT / f"year-{theme}.svg").write_text(render_year_svg(days, theme))
    print("wrote 8 SVGs" + (" (mock data)" if mock else ""))


if __name__ == "__main__":
    main()
