#!/usr/bin/env python3
"""Crop the colour ASCII portrait and give it a fade-in."""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "portrait-source.svg"
OUTPUT = ROOT / "ascii.svg"
CELL = 6.0   # the source grid assumes a 0.600 em advance at 10px
MARGIN = 1   # blank columns kept either side of the artwork


def visible(fill):
    return sum(int(fill[i:i + 2], 16) for i in (1, 3, 5)) > 0x60


def render():
    source = SOURCE.read_text(encoding="utf-8")
    height = float(re.search(r'height="([\d.]+)"', source).group(1))
    rows = re.findall(r'<text ([^>]*)>(.*?)</text>', source)

    left, right = 10 ** 6, 0
    for _, body in rows:
        column = 0
        for fill, text in re.findall(r'<tspan fill="(#[0-9a-f]{6})">(.*?)</tspan>', body):
            for _ in html.unescape(text):
                if visible(fill):
                    left, right = min(left, column), max(right, column)
                column += 1
    left, right = left - MARGIN, right + 1 + MARGIN
    x0, width = left * CELL, (right - left) * CELL

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
           f'viewBox="{x0:.0f} 0 {width:.0f} {height:.0f}">']
    svg.append(f'<rect x="{x0:.0f}" width="{width:.0f}" height="{height:.0f}" fill="#0d1117"/>')
    svg.append('<g opacity="0" style="font-family:Consolas,Menlo,\'Liberation Mono\',monospace;font-size:10px">'
               '<animate attributeName="opacity" values="0;1" dur="1.4s" fill="freeze"/>')
    for attributes, body in rows:
        columns = sum(len(html.unescape(t)) for t in re.findall(r'<tspan[^>]*>(.*?)</tspan>', body))
        # pin every row to the grid so narrower fonts (Consolas is 0.55 em) don't squeeze it
        svg.append(f'<text {attributes} textLength="{columns * CELL:.0f}" lengthAdjust="spacing">{body}</text>')
    svg.append('</g></svg>')
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"rendered {len(rows)} rows, columns {left}-{right}")


if __name__ == "__main__":
    render()
