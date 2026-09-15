#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = ["stats.svg", "streak.svg", "langs.svg", "year.svg"]
missing = [p for p in required if not (ROOT / p).exists()]
if missing:
    raise SystemExit("Missing profile assets: " + ", ".join(missing))

# Kept intentionally side-effect free until the full GitHub GraphQL renderer
# is installed. This avoids rewriting checked-in snapshots with fake data.
print("profile stat assets present; no refresh performed")
