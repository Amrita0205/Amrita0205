#!/usr/bin/env python3
"""Render the selected local portrait as an animated ASCII SVG."""

from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "WhatsApp Image 2026-09-16 at 1.34.02 AM (1).jpeg"
OUTPUT = ROOT / "ascii.svg"
CHARACTERS = " .:-=+*#%@"
ASCII_WIDTH = 92
LINE_HEIGHT = 9


def render():
    image = Image.open(SOURCE).convert("L")
    image = image.crop((round(image.width * 0.28), 0, round(image.width * 0.88), round(image.height * 0.88)))
    image = ImageOps.autocontrast(image, cutoff=2)
    ascii_height = max(1, round(image.height / image.width * ASCII_WIDTH * 0.48))
    image = ImageOps.fit(image, (ASCII_WIDTH, ascii_height), method=Image.Resampling.LANCZOS)

    lines = []
    for row in range(image.height):
        pixels = image.crop((0, row, image.width, row + 1)).getdata()
        lines.append("".join(CHARACTERS[(255 - pixel) * (len(CHARACTERS) - 1) // 255] for pixel in pixels).rstrip())

    height = len(lines) * LINE_HEIGHT
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="{height}" viewBox="0 0 460 {height}" font-family="monospace" font-size="7.8px">']
    svg.append('<style>text{fill:#c9d1d9}@media(prefers-color-scheme:dark){text{fill:#f0f6fc}}</style>')
    for index, line in enumerate(lines):
        baseline = (index + 1) * LINE_HEIGHT
        delay = index * 0.035
        svg.append(f'<clipPath id="r{index}"><rect x="0" y="{baseline - LINE_HEIGHT}" width="0" height="{LINE_HEIGHT + 4}"><animate attributeName="width" from="0" to="460" begin="{delay:.2f}s" dur="0.75s" fill="freeze"/></rect></clipPath>')
        svg.append(f'<text x="0" y="{baseline}" xml:space="preserve" clip-path="url(#r{index})">{escape(line)}</text>')
    svg.append("</svg>")
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(f"rendered {SOURCE.name}")


if __name__ == "__main__":
    render()