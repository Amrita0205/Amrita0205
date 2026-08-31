<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="dark_mode.svg">
    <source media="(prefers-color-scheme: light)" srcset="light_mode.svg">
    <img alt="Amrita Kadam — AI/ML engineer. Stack: Python, PyTorch, LangChain, LangGraph, CrewAI, RAG, MLflow, FastAPI." src="dark_mode.svg">
  </picture>
</div>

<p align="center">
  <a href="https://amrita-kadam.vercel.app/">Portfolio</a> ·
  <a href="https://www.linkedin.com/in/amrita-kadam-2a293b287">LinkedIn</a> ·
  <a href="mailto:amrita0205kadam@gmail.com">Email</a>
</p>

<!--
To update the numbers (repos, followers, etc.), edit the INFO list in gen_svg.py
and regenerate, or edit the text inside dark_mode.svg / light_mode.svg directly.
-->
<!-- One long line on purpose: <br> = line break, &nbsp; = spacing, so it survives a paste that flattens newlines. Do not add real line breaks inside the pre. -->

Hi, I'm Amrita 👋

Final-year CS student at IIIT Raichur and a mechanistic interpretability research intern at Moleculyst. I build AI systems and then try to break them — most of what I ship has tests, an eval, or a deployment attached, not just a notebook.

What I work on

Multi-agent systems — CrewAI, LangGraph, agent hand-off and task routing
RAG — ChromaDB, local and hosted LLMs, retrieval quality over vibes
MLOps — MLflow experiment tracking and model registry, FastAPI serving
Interpretability — probing what models actually represent internally
Python — plus the boring parts: CI, packaging, releases
What I'm building

GhostRead — a transparent, always-on-top PDF reader for Windows, in under 2,000 lines of Python. Read a textbook over your terminal at any opacity, with click-through and a ghost mode that keeps text sharp. Download the .exe · PyPI · CI: 108 tests

Blog Writing Crew — a four-agent CrewAI pipeline on Groq (llama-3.3-70b). A researcher gathers sources, a writer drafts the post, an editor takes it to publication quality, and a social media manager turns it into a Twitter thread and a LinkedIn post.

Local RAG API — a fully offline retrieval-augmented QA service. FastAPI endpoint → ChromaDB semantic search → prompt augmentation → local LLM via Ollama. No external API calls, no per-query cost.

Iris Prediction API — an end-to-end MLOps pipeline: MLflow tracks every run and registers the model, multiple solvers are compared from the tracking UI, and FastAPI serves the registered version behind a REST endpoint.

Currently

Doing interpretability research at Moleculyst, and building out evaluation for my RAG and agent projects — retrieval accuracy, latency, and cost per query, measured rather than guessed.
