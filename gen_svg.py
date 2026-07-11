#!/usr/bin/env python3
"""Generate neofetch-style GitHub profile SVGs (dark + light) for Amrita Kadam."""
import html

ASCII_NAME = r"""                        _ __
  ____ _____ ___  _____(_) /_____ _
 / __ `/ __ `__ \/ ___/ / __/ __ `/
/ /_/ / / / / / / /  / / /_/ /_/ /
\__,_/_/ /_/ /_/_/  /_/\__/\__,_/""".split("\n")

ASCII_NET = r"""
    o     o     o     o
    |\   /|\   /|\   /|
    | \ / | \ / | \ / |
    |  X  |  X  |  X  |
    | / \ | / \ | / \ |
    |/   \|/   \|/   \|
    o     o     o     o
     \    |     |    /
      \   |     |   /
       \  |     |  /
        \ |     | /
         \|     |/
          o     o
           \   /
            \ /
             o
             |
           [ y^ ]""".split("\n")

# (label, value) — label None means blank line; label "" means raw colored value line
KEY_W = 19
INFO = [
    ("TITLE", "amrita@github"),
    ("SEP", "-" * 46),
    ("OS:", "Ubuntu (WSL2), Windows"),
    ("Host:", "IIIT Raichur — B.Tech CSE '27, CGPA 8.51"),
    ("Kernel:", "AI/ML Engineering"),
    ("Uptime:", "Final year — graduating Jan 2027"),
    ("IDE:", "VS Code, Jupyter"),
    (None, ""),
    ("Stack.Languages:", "Python, SQL, TypeScript, JavaScript, C++"),
    ("Stack.AI/ML:", "PyTorch, TensorFlow, Deep Learning, NLP"),
    ("Stack.Agentic:", "LangChain, LangGraph, CrewAI, RAG, ChromaDB"),
    ("Stack.MLOps:", "MLflow, FastAPI, Model Registry, Uvicorn"),
    ("Stack.Backend:", "Node.js, Express, PostgreSQL, MongoDB"),
    (None, ""),
    ("Projects.Agentic:", "AI Career Advisor — LangGraph + Groq agents"),
    ("Projects.MLOps:", "E2E ML pipeline — MLflow + FastAPI, 97.5% acc"),
    ("Projects.Crew:", "Blog-writing pipeline — 4 CrewAI agents"),
    ("Projects.Now:", "Anoniz"),
    ("Programs:", "Summer of Bitcoin '26 — Bit Lens, Coin Smith"),
    (None, ""),
    ("Contact.Email:", "amrita0205kadam@gmail.com"),
    ("Contact.LinkedIn:", "in/amrita-kadam-2a293b287"),
    ("Contact.Portfolio:", "amrita-kadam.vercel.app"),
    (None, ""),
    ("TITLE2", "GitHub Stats"),
    ("Repos:", "36 (public)   Followers: 4"),
    ("Top Languages:", "Python · TypeScript · JavaScript"),
]

THEMES = {
    "dark": dict(
        bg="#0d1117", border="#30363d",
        title="#58a6ff", sep="#8b949e",
        label="#ffa657", value="#a5d6ff", plain="#c9d1d9",
        ascii_name=["#d2a8ff", "#bc8cff", "#a371f7", "#8957e5", "#79c0ff"],
        ascii_net="#56d364",
        net_out="#ff7b72",
    ),
    "light": dict(
        bg="#ffffff", border="#d0d7de",
        title="#0969da", sep="#6e7781",
        label="#953800", value="#0a3069", plain="#24292f",
        ascii_name=["#8250df", "#8250df", "#6639ba", "#6639ba", "#0969da"],
        ascii_net="#1a7f37",
        net_out="#cf222e",
    ),
}

CHAR_W = 7.8          # approx monospace advance at 13px
LINE_H = 18
PAD_X, PAD_Y = 26, 30
LEFT_X = PAD_X
RIGHT_X = 320
WIDTH = 872


def esc(s):
    return html.escape(s, quote=False)


def build(theme_name):
    t = THEMES[theme_name]
    n_right = len(INFO)
    n_left = len(ASCII_NAME) + len(ASCII_NET) + 1
    n_lines = max(n_right, n_left)
    height = PAD_Y * 2 + n_lines * LINE_H + 8

    out = []
    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="\'SFMono-Regular\',Consolas,\'Liberation Mono\',Menlo,monospace" font-size="13px">'
    )
    out.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH-1}" height="{height-1}" rx="10" fill="{t["bg"]}" stroke="{t["border"]}"/>'
    )

    # ---- left column: ascii name + neural net ----
    y = PAD_Y + 14
    for i, line in enumerate(ASCII_NAME):
        c = t["ascii_name"][min(i, len(t["ascii_name"]) - 1)]
        out.append(f'<text x="{LEFT_X}" y="{y}" xml:space="preserve" fill="{c}">{esc(line)}</text>')
        y += LINE_H
    y += LINE_H // 2
    for i, line in enumerate(ASCII_NET):
        c = t["net_out"] if ("y^" in line) else t["ascii_net"]
        out.append(f'<text x="{LEFT_X + 40}" y="{y}" xml:space="preserve" fill="{c}">{esc(line)}</text>')
        y += LINE_H

    # ---- right column: info ----
    y = PAD_Y + 14
    for key, val in INFO:
        if key is None:
            y += LINE_H
            continue
        if key in ("TITLE", "TITLE2"):
            out.append(
                f'<text x="{RIGHT_X}" y="{y}" xml:space="preserve" font-weight="bold" fill="{t["title"]}">{esc(val)}</text>'
            )
        elif key == "SEP":
            out.append(f'<text x="{RIGHT_X}" y="{y}" xml:space="preserve" fill="{t["sep"]}">{esc(val)}</text>')
        else:
            padded = key.ljust(KEY_W)
            out.append(
                f'<text x="{RIGHT_X}" y="{y}" xml:space="preserve">'
                f'<tspan fill="{t["label"]}">{esc(padded)}</tspan>'
                f'<tspan fill="{t["value"]}">{esc(val)}</tspan></text>'
            )
        y += LINE_H

    out.append("</svg>")
    return "\n".join(out)


for name in THEMES:
    path = f"/home/claude/{name}_mode.svg"
    with open(path, "w") as f:
        f.write(build(name))
    print("wrote", path)
