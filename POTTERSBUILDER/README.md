# POTTERSBUILDER — Kenyan History AI

POTTERSBUILDER is a developer scaffold for building an AI assistant focused purely on Kenyan history. The project provides ingestion, semantic search (FAISS + sentence-transformers), and a minimal API and CLI to query a corpus of Kenyan history documents.

Goals
- Collect and normalize Kenyan history content (documents, books, articles, oral histories).
- Build a searchable vector store of the corpus.
- Provide a simple API and CLI that return context-aware answers; optionally use OpenAI for synthesis (configurable).

Quick start (Windows PowerShell)

1) Create and activate a virtual environment

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
pip install -r requirements.txt
```

3) Add your documents to `data/` (see `data/README.md`).

4) Ingest data (build FAISS index)

```powershell
python src\ingest.py --data-dir data --index-path vector_index.faiss --meta-path docs.pkl
```

5) Query interactively

```powershell
python src\query.py --query "Who was Jomo Kenyatta and why is he important?" --index-path vector_index.faiss --meta-path docs.pkl
```

6) Run the API

```powershell
pip install uvicorn fastapi
uvicorn src.api:app --reload --port 8000
```

Notes
- You can optionally set `OPENAI_API_KEY` in the environment to use OpenAI for answer synthesis. If no key is present, queries will return retrieved contexts.
- FAISS builds on native libraries. If you have trouble installing `faiss-cpu` on Windows, see the README for alternatives (use `chromadb`, or run in WSL/docker).

Next steps
- Add more Kenyan history content, tag sources and dates, and index.
- Add evaluation tests and example prompts.
- Add data provenance and licensing checks for each source.

License: MIT

PHP interface
---------------
A minimal PHP frontend is provided in the `php/` folder. It posts queries to the local API endpoint (default `http://127.0.0.1:8000/query`) and displays retrieved contexts and synthesized answers (if OpenAI is configured). See `php/README.md` for usage.
