#!/usr/bin/env python3
"""Render the selected local portrait as an animated ASCII SVG."""

from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
SOURCE_README = ROOT / "ASCII_Fidelity_AI_Image06_README.md"
OUTPUT = ROOT / "ascii.svg"
LINE_HEIGHT = 6.2
FONT_SIZE = 4.2
CHAR_WIDTH = FONT_SIZE * 0.6


def render():
    content = SOURCE_README.read_text(encoding="utf-8")
    lines = content.split("```text", 1)[1].split("```", 1)[0].splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    occupied = [index for line in lines for index, char in enumerate(line) if not char.isspace()]
    left = min(occupied)
    right = max(occupied) + 1
    lines = [line[left:right].rstrip() for line in lines]
    width = max(len(line) for line in lines)
    height = len(lines) * LINE_HEIGHT
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="{height:.0f}" viewBox="0 0 460 {height:.0f}" font-family="monospace" font-size="{FONT_SIZE}px">']
    svg.append('<style>text{fill:#c9d1d9}@media(prefers-color-scheme:dark){text{fill:#f0f6fc}}</style>')
    svg.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur="1.4s" fill="freeze"/>')
    for index, line in enumerate(lines):
        baseline = (index + 1) * LINE_HEIGHT
        x = max(0, (460 - len(line) * CHAR_WIDTH) / 2)
        svg.append(f'<text x="{x:.1f}" y="{baseline}" xml:space="preserve">{escape(line)}</text>')
    svg.append('</g>')
    svg.append('</svg>')
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"rendered uploaded ASCII artwork: {width} columns x {len(lines)} rows")


if __name__ == "__main__":
    render()