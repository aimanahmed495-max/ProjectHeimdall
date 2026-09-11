# Heimdall OSINT Ingestion

Prototype LangGraph agent that turns mock open-source alerts into Heimdall threat events.

The pipeline loads a few fake OSINT sources and raw alert strings, registers the sources with the existing FastAPI backend, then runs each alert through a three-node LangGraph: ingest the text, classify a likely visual object with Groq's GPT-OSS 20B model, and post a threat event plus a system log to `http://localhost:8000`. This module talks only to the real `/sources`, `/threat-events`, and `/system-logs` endpoints; it does not start Docker or the API itself.

## Requirements

- Python 3.10+
- A running Heimdall Core API at `http://localhost:8000` (see `backend/README.md`)
- A Groq API key

## Install

From the repository root:

```bash
cd ai-brain
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

```bash
cp .env.example .env
```

Edit `.env` and set:

```text
GROQ_API_KEY=your_groq_api_key
BASE_URL=http://localhost:8000
```

## Run

Make sure the API is up, then from `ai-brain/`:

```bash
python main.py
```

The process prints a live summary of each alert, its Groq classification, and the API response. If the backend is not running, it exits with a clear error instead of crashing.
