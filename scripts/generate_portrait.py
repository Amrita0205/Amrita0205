#!/usr/bin/env python3
"""
generate_portrait.py — turn a pre-computed ASCII portrait (plain text, one
row per line) into a self-typing SVG, in the same visual language as the
stats graphics.

This is a ONE-TIME step, not part of the nightly refresh: your face doesn't
change every day. Re-run it only when you want a new source photo.

Usage:
    python3 generate_portrait.py <ascii.txt> <out.svg> --theme dark|light
"""
import argparse
import base64
from pathlib import Path

HERE = Path(__file__).parent
CHAR_W_EM = 0.600          # JetBrains Mono's advance width — see fonts/README
FONT_SIZE = 12.9
CHAR_W = FONT_SIZE * CHAR_W_EM
LINE_H = FONT_SIZE * 1.32
PAD = 18
STAGGER = 0.09              # seconds between each row starting its wipe
WIPE_DUR = 0.5

THEMES = {
    "dark":  dict(bg="#0d1117", ink="#c9d1d9", cursor="#58a6ff"),
    "light": dict(bg="#ffffff", ink="#24292f", cursor="#0969da"),
}


def load_font_b64(name: str) -> str:
    return (HERE.parent / "fonts" / f"{name}.b64").read_text().strip()


def build(ascii_path: str, theme: str) -> str:
    lines = Path(ascii_path).read_text().rstrip("\n").split("\n")
    cols = max(len(l) for l in lines)
    rows = len(lines)
    t = THEMES[theme]

    width = PAD * 2 + cols * CHAR_W
    height = PAD * 2 + rows * LINE_H
    ramp_font_b64 = load_font_b64("ramp")

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" role="img" '
        f'aria-label="ASCII portrait">'
    )
    parts.append(f"""
<defs>
  <style>
    @font-face {{
      font-family: 'RampMono';
      src: url(data:font/woff2;base64,{ramp_font_b64}) format('woff2');
    }}
    text {{
      font-family: 'RampMono', monospace;
      font-size: {FONT_SIZE}px;
      fill: {t['ink']};
      white-space: pre;
    }}
  </style>
</defs>""")
    parts.append(f'<rect width="{width:.0f}" height="{height:.0f}" fill="{t["bg"]}"/>')

    for i, line in enumerate(lines):
        y = PAD + (i + 1) * LINE_H - LINE_H * 0.28
        row_w = len(line) * CHAR_W
        clip_id = f"wipe{i}"
        begin = round(i * STAGGER, 3)
        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(
            f'  <rect x="{PAD}" y="{PAD + i*LINE_H}" height="{LINE_H:.2f}" width="0">'
            f'<animate attributeName="width" from="0" to="{row_w:.2f}" '
            f'begin="{begin}s" dur="{WIPE_DUR}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.2 0 0.2 1"/></rect>'
        )
        parts.append('</clipPath>')
        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(
            f'  <text x="{PAD}" y="{y:.2f}" xml:space="preserve">{escape(line)}</text>'
        )
        # cursor block riding the wipe edge
        parts.append(
            f'  <rect y="{PAD + i*LINE_H + 1:.2f}" width="{CHAR_W:.2f}" height="{LINE_H-2:.2f}" '
            f'fill="{t["cursor"]}" opacity="0.85">'
            f'<animate attributeName="x" from="{PAD}" to="{PAD+row_w:.2f}" '
            f'begin="{begin}s" dur="{WIPE_DUR}s" fill="freeze" calcMode="spline" '
            f'keySplines="0.2 0 0.2 1"/>'
            f'<animate attributeName="opacity" from="0.85" to="0" '
            f'begin="{begin+WIPE_DUR}s" dur="0.15s" fill="freeze"/>'
            f'</rect>'
        )
        parts.append('</g>')

    parts.append("</svg>")
    return "\n".join(parts)


def escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("ascii_path")
    ap.add_argument("out_path")
    ap.add_argument("--theme", choices=["dark", "light"], required=True)
    args = ap.parse_args()
    svg = build(args.ascii_path, args.theme)
    Path(args.out_path).write_text(svg)
    print(f"wrote {args.out_path}  ({len(svg)} bytes)")
