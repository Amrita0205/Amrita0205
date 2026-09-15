#!/usr/bin/env python3
"""Render the selected local portrait as an animated ASCII SVG."""

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "images" / "portrait-2.jpeg"
OUTPUT = ROOT / "ascii.svg"
WIDTH = 460
HEIGHT = 352


def render():
    image = Image.open(SOURCE).convert("L")
    image = image.crop((round(image.width * 0.28), 0, round(image.width * 0.88), round(image.height * 0.88)))
    image = ImageOps.fit(image, (WIDTH, HEIGHT), method=Image.Resampling.LANCZOS)
    image = ImageOps.autocontrast(image, cutoff=2)
    encoded = BytesIO()
    image.save(encoded, format="JPEG", quality=84, optimize=True)
    payload = base64.b64encode(encoded.getvalue()).decode("ascii")
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<defs><clipPath id="portrait-reveal"><rect x="0" y="0" width="0" height="{HEIGHT}"><animate attributeName="width" from="0" to="{WIDTH}" begin="0.2s" dur="1.4s" fill="freeze"/></rect></clipPath></defs>
<rect width="{WIDTH}" height="{HEIGHT}" fill="#0d1117"/>
<image width="{WIDTH}" height="{HEIGHT}" preserveAspectRatio="none" href="data:image/jpeg;base64,{payload}" clip-path="url(#portrait-reveal)"/>
</svg>'''
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"rendered {SOURCE.name}")


if __name__ == "__main__":
    render()