#!/usr/bin/env python3
"""Profile stat refresh contract.

The README expects stats.svg, streak.svg, langs.svg, year.svg and hd-*.svg.
This version preserves the checked-in local artwork and can be replaced with
the full GraphQL renderer without changing the public README interface.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [
    "stats.svg", "streak.svg", "langs.svg", "year.svg",
    "hd-about.svg", "hd-stack.svg", "hd-projects.svg",
    "hd-stats.svg", "hd-about-this-page.svg",
]

missing = [p for p in EXPECTED if not (ROOT / p).exists()]
if missing:
    raise SystemExit("Missing profile assets: " + ", ".join(missing))

print("profile graphics present; no changes needed")
