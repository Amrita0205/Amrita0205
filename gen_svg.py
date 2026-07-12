#!/usr/bin/env python3
"""Neofetch-style GitHub profile SVG — Andrew6rant layout: ASCII portrait left,
dot-leader key/value info right, values right-aligned."""
import html

LINE_W = 66          # characters per info line (label + dots + value)
CHAR_W = 7.8
LINE_H = 17
PAD_Y = 28
LEFT_X = 24
RIGHT_X = 408
WIDTH = 952

# ---- info content -------------------------------------------------------
# tuples: ("kv", label, value) | ("head", text) | ("gap",) | ("stats", [(txt,color),...])
INFO = [
    ("title", "amrita@github"),
    ("rule",),
    ("kv", "OS", "Ubuntu (WSL2), Windows"),
    ("kv", "Uptime", "Final year, graduating Jan 2027"),
    ("kv", "Host", "IIIT Raichur - B.Tech CSE"),
    ("kv", "Kernel", "AI/ML Engineering, CGPA 8.51"),
    ("kv", "IDE", "VS Code, Jupyter"),
    ("gap",),
    ("kv", "Languages.Programming", "Python, SQL, TypeScript, C++"),
    ("kv", "Languages.AI/ML", "PyTorch, TensorFlow, NLP"),
    ("kv", "Languages.Agentic", "LangChain, LangGraph, CrewAI"),
    ("kv", "Languages.Data", "RAG, ChromaDB, Vector Search"),
    ("kv", "Languages.Backend", "FastAPI, Node.js, PostgreSQL"),
    ("gap",),
    ("kv", "Projects.Agentic", "AI Career Advisor (LangGraph)"),
    ("kv", "Projects.MLOps", "MLflow + FastAPI, 97.5% acc"),
    ("kv", "Projects.Crew", "Blog-writing agents (CrewAI)"),
    ("kv", "Projects.Building", "Anoniz"),
    ("kv", "Programs", "Summer of Bitcoin '26"),
    ("gap",),
    ("head", "Contact"),
    ("kv", "Email.Personal", "amrita0205kadam@gmail.com"),
    ("kv", "LinkedIn", "amrita-kadam-2a293b287"),
    ("kv", "Portfolio", "amrita-kadam.vercel.app"),
    ("kv", "GitHub", "Amrita0205"),
    ("gap",),
    ("head", "GitHub Stats"),
    ("stats", [("Repos", "label"), (": ", "dot"), ("36 (public)", "value"),
               ("  |  ", "dot"), ("Top Language", "label"), (": ", "dot"), ("Python", "green")]),
    ("stats", [("Followers", "label"), (": ", "dot"), ("4", "value"),
               ("  |  ", "dot"), ("Focus", "label"), (": ", "dot"),
               ("Agentic AI + MLOps", "cyan")]),
]

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", title="#58a6ff", rule="#8b949e",
                 label="#ffa657", dot="#484f58", value="#a5d6ff", head="#d2a8ff",
                 green="#56d364", cyan="#79c0ff", portrait="#c9d1d9"),
    "light": dict(bg="#ffffff", border="#d0d7de", title="#0969da", rule="#6e7781",
                  label="#953800", dot="#afb8c1", value="#0a3069", head="#6639ba",
                  green="#1a7f37", cyan="#0969da", portrait="#24292f"),
}


def esc(s):
    return html.escape(s, quote=False)


def build(theme, ascii_lines):
    t = THEMES[theme]
    n = max(len(INFO), len(ascii_lines))
    height = PAD_Y * 2 + n * LINE_H + 10
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" '
        f'font-family="\'SFMono-Regular\',Consolas,\'Liberation Mono\',Menlo,monospace" font-size="12.5px">',
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1}" rx="10" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>',
    ]

    # portrait, vertically centered
    y = PAD_Y + 14 + max(0, (len(INFO) - len(ascii_lines)) * LINE_H // 2)
    for line in ascii_lines:
        out.append(f'<text x="{LEFT_X}" y="{y}" xml:space="preserve" '
                   f'fill="{t["portrait"]}">{esc(line)}</text>')
        y += LINE_H

    # info column
    y = PAD_Y + 14
    for row in INFO:
        kind = row[0]
        if kind == "gap":
            y += LINE_H
            continue
        if kind == "title":
            out.append(f'<text x="{RIGHT_X}" y="{y}" font-weight="bold" '
                       f'fill="{t["title"]}">{esc(row[1])}</text>')
        elif kind == "rule":
            out.append(f'<text x="{RIGHT_X}" y="{y}" xml:space="preserve" '
                       f'fill="{t["rule"]}">{esc("-" * LINE_W)}</text>')
        elif kind == "head":
            txt = f'{row[1]} ' + "-" * (LINE_W - len(row[1]) - 1)
            out.append(f'<text x="{RIGHT_X}" y="{y}" xml:space="preserve">'
                       f'<tspan fill="{t["head"]}" font-weight="bold">{esc(row[1])}</tspan>'
                       f'<tspan fill="{t["rule"]}"> {esc("-" * (LINE_W - len(row[1]) - 1))}</tspan>'
                       f'</text>')
        elif kind == "kv":
            label, value = row[1], row[2]
            ndots = max(1, LINE_W - len(label) - len(value) - 3)
            out.append(f'<text x="{RIGHT_X}" y="{y}" xml:space="preserve">'
                       f'<tspan fill="{t["label"]}">{esc(label)}</tspan>'
                       f'<tspan fill="{t["dot"]}">: {"." * ndots} </tspan>'
                       f'<tspan fill="{t["value"]}">{esc(value)}</tspan></text>')
        elif kind == "stats":
            spans = "".join(f'<tspan fill="{t[c]}">{esc(txt)}</tspan>' for txt, c in row[1])
            out.append(f'<text x="{RIGHT_X}" y="{y}" xml:space="preserve">{spans}</text>')
        y += LINE_H
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    for theme, path in (("dark", "/tmp/ascii_dark.txt"), ("light", "/tmp/ascii_light.txt")):
        art = open(path).read().split("\n")
        with open(f"/home/claude/{theme}_mode.svg", "w") as f:
            f.write(build(theme, art))
        print("wrote", theme)
