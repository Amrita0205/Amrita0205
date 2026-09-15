#!/usr/bin/env python3
import base64
from pathlib import Path

HERE = Path(__file__).parent
FONTS = HERE.parent / "fonts"

THEMES = {
    "dark":  dict(bg="#0d1117", ink="#d2a8ff", rule="#30363d"),
    "light": dict(bg="#ffffff", ink="#6639ba", rule="#d0d7de"),
}


def font_face_css():
    b64 = (FONTS / "text-bold.b64").read_text().strip()
    return (
        "@font-face { font-family: 'HeadMono'; "
        f"src: url(data:font/woff2;base64,{b64}) format('woff2'); }}"
    )


def build(label: str, theme: str, width: int = 872) -> str:
    t = THEMES[theme]
    height = 40
    text_w = len(label) * 13 * 0.6 + 4
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{label}">'
        f'<defs><style>{font_face_css()}'
        f'text{{font-family:"HeadMono",monospace;font-size:15px;font-weight:700;'
        f'fill:{t["ink"]};letter-spacing:0.5px;}}</style></defs>'
        f'<rect width="{width}" height="{height}" fill="{t["bg"]}"/>'
        f'<text x="0" y="25" xml:space="preserve">{label.lower()}</text>'
        f'<line x1="{text_w:.0f}" y1="22" x2="{width}" y2="22" '
        f'stroke="{t["rule"]}" stroke-width="1"/>'
        f'</svg>'
    )


if __name__ == "__main__":
    headings = ["now building", "contact", "gitHub stats"]
    slugs = ["now-building", "contact", "stats-heading"]
    for label, slug in zip(headings, slugs):
        for theme in ("dark", "light"):
            out = HERE.parent / f"heading-{slug}-{theme}.svg"
            out.write_text(build(label, theme))
            print("wrote", out.name)
