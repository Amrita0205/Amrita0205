#!/usr/bin/env python3
"""Render the selected local portrait as an animated ASCII SVG."""

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    ROOT / "images" / "Gemini_Generated_Image_b5vlv4b5vlv4b5vl.png",
)
OUTPUT = ROOT / "ascii.svg"


def render():
    encoded = []
    for source in SOURCES:
        image = Image.open(source).convert("RGB")
        width, height = image.size
        image = image.crop((round(width * 0.25), 0, round(width * 0.75), height))
        image.thumbnail((460, 352), Image.Resampling.LANCZOS)
        buffer = BytesIO()
        image.save(buffer, format="PNG", optimize=True)
        payload = base64.b64encode(buffer.getvalue()).decode("ascii")
        encoded.append(payload)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="460" height="352" viewBox="0 0 460 352">']
    svg.append('<style>image{image-rendering:auto}</style>')
    svg.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" dur="1.4s" fill="freeze"/><image x="0" y="0" width="460" height="352" preserveAspectRatio="xMidYMid meet" href="data:image/png;base64,{encoded[0]}"/></g>')
    svg.append('</svg>')
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print("rendered one supplied ASCII PNG frame")


if __name__ == "__main__":
    render()