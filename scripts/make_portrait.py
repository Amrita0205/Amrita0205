#!/usr/bin/env python3
"""Crop the colour ASCII portrait and type it out one row at a time."""

import html
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "portrait-source.svg"
OUTPUT = ROOT / "ascii.svg"
CELL = 6.0   # the source grid assumes a 0.600 em advance at 10px
MARGIN = 1   # blank columns kept either side of the artwork
STEP = 0.09  # seconds to type each row
FONT = "font-family:Consolas,Menlo,'Liberation Mono',monospace;font-size:10px"


def visible(fill):
    return sum(int(fill[i:i + 2], 16) for i in (1, 3, 5)) > 0x60


def render():
    source = SOURCE.read_text(encoding="utf-8")
    height = float(re.search(r'height="([\d.]+)"', source).group(1))
    rows = re.findall(r'<text ([^>]*)>(.*?)</text>', source)

    left, right = 10 ** 6, 0
    ends = []
    for _, body in rows:
        column, end = 0, 0
        for fill, text in re.findall(r'<tspan fill="(#[0-9a-f]{6})">(.*?)</tspan>', body):
            for _ in html.unescape(text):
                if visible(fill):
                    left, right = min(left, column), max(right, column)
                    end = column + 1
                column += 1
        ends.append(end)
    left, right = left - MARGIN, right + 1 + MARGIN
    x0, width = left * CELL, (right - left) * CELL

    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
           f'viewBox="{x0:.0f} 0 {width:.0f} {height:.0f}" style="{FONT}">']
    svg.append(f'<rect x="{x0:.0f}" width="{width:.0f}" height="{height:.0f}" fill="#0d1117"/>')
    row = 0
    for (attributes, body), end in zip(rows, ends):
        top = float(re.search(r'y="([\d.]+)"', attributes).group(1)) - 8.5
        columns = sum(len(html.unescape(t)) for t in re.findall(r'<tspan[^>]*>(.*?)</tspan>', body))
        # pin every row to the grid so narrower fonts (Consolas is 0.55 em) don't squeeze it
        text = f'<text {attributes} textLength="{columns * CELL:.0f}" lengthAdjust="spacing">{body}</text>'
        if end <= left:
            svg.append(text)
            continue
        begin, reach = row * STEP, end * CELL - x0
        svg.append(f'<clipPath id="c{row}"><rect x="{x0:.0f}" y="{top:.1f}" height="10" width="0">'
                   f'<animate attributeName="width" from="0" to="{reach:.1f}" begin="{begin:.2f}s" '
                   f'dur="{STEP}s" fill="freeze"/></rect></clipPath>')
        svg.append(f'<g clip-path="url(#c{row})">{text}</g>')
        # the cursor block that runs ahead of each row as it types
        svg.append(f'<rect y="{top + 0.5:.1f}" width="6" height="9" fill="#c9d1d9" opacity="0">'
                   f'<animate attributeName="x" from="{x0:.0f}" to="{x0 + reach:.1f}" begin="{begin:.2f}s" '
                   f'dur="{STEP}s" fill="freeze"/>'
                   f'<set attributeName="opacity" to="0.8" begin="{begin:.2f}s"/>'
                   f'<set attributeName="opacity" to="0" begin="{begin + STEP:.2f}s"/></rect>')
        row += 1
    svg.append('</svg>')
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"rendered {len(rows)} rows ({row} typed), columns {left}-{right}")


if __name__ == "__main__":
    render()
