#!/usr/bin/env python3
"""Render the selected local portrait as an animated ASCII SVG."""

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "images" / "Gemini_Generated_Image_b5vlv4b5vlv4b5vl.png",
    ROOT / "images" / "Gemini_Generated_Image_mol45vmol45vmol4.png",
)
OUTPUT = ROOT / "ascii.svg"


def render():
    encoded = []
    for source in SOURCES:
        image = Image.open(source).convert("RGB")
        image.thumbnail((460, 352), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        payload = base64.b64encode(buffer.getvalue()).decode("ascii")
        encoded.append(payload)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="460" height="352" viewBox="0 0 460 352">']
    svg.append('<style>image{image-rendering:auto}</style>')
    for index, payload in enumerate(encoded):
        svg.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1;1;0;0" keyTimes="0;.04;.30;.34;1" dur="6s" begin="-{index * 3}s" repeatCount="indefinite"/><image x="0" y="0" width="460" height="352" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{payload}"/></g>')
    svg.append('</svg>')
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print("rendered two supplied ASCII PNG frames; each displays for about 3 seconds")


if __name__ == "__main__":
    render()