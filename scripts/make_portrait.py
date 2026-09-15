#!/usr/bin/env python3
"""Render the selected local portrait as an animated ASCII SVG."""

from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "images" / "portrait-1.jpeg",
    ROOT / "images" / "portrait-2.jpeg",
)
CROPS = ((0.24, 0.02, 0.84, 0.86), (0.25, 0.02, 0.94, 0.90))
OUTPUT = ROOT / "ascii.svg"
ASCII_WIDTH = 92
LINE_HEIGHT = 9
CHARACTERS = " .:-=+*#%@"


def frame(source, crop_box):
    image = Image.open(source).convert("L")
    left, top, right, bottom = crop_box
    image = image.crop((round(image.width * left), round(image.height * top), round(image.width * right), round(image.height * bottom)))
    height = max(1, round(image.height / image.width * ASCII_WIDTH * 0.48))
    image = ImageOps.fit(image, (ASCII_WIDTH, height), method=Image.Resampling.LANCZOS)
    image = ImageOps.autocontrast(image.filter(ImageFilter.FIND_EDGES), cutoff=4)
    rows = []
    for row in range(image.height):
        pixels = image.crop((0, row, image.width, row + 1)).getdata()
        rows.append("".join(CHARACTERS[(255 - pixel) * (len(CHARACTERS) - 1) // 255] for pixel in pixels).rstrip())
    return rows


def render():
    frames = [frame(source, crop_box) for source, crop_box in zip(SOURCES, CROPS)]
    loop_duration = len(frames) * 3
    height = max(len(rows) for rows in frames) * LINE_HEIGHT
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="460" height="{height}" viewBox="0 0 460 {height}" font-family="monospace" font-size="7.8px">']
    svg.append('<style>text{fill:#c9d1d9}@media(prefers-color-scheme:dark){text{fill:#f0f6fc}}</style>')
    for frame_index, rows in enumerate(frames):
        svg.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.04;.30;.34;1" dur="{loop_duration}s" begin="-{frame_index * 3}s" repeatCount="indefinite"/>')
        for row_index, line in enumerate(rows):
            baseline = (row_index + 1) * LINE_HEIGHT
            svg.append(f'<text x="0" y="{baseline}" xml:space="preserve">{escape(line)}</text>')
        svg.append('</g>')
    svg.append('</svg>')
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print("rendered two portrait frames; each displays for about 3 seconds")


if __name__ == "__main__":
    render()