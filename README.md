# Project Heimdall

An autonomous, edge-to-cloud surveillance system that uses a multi-agent OSINT pipeline to dynamically trigger computer vision into high-alert modes, reducing data bloat and alert fatigue compared to always-on camera monitoring.

**Prototype 1 (Foundation & Data Layer)** — this milestone covers repository hygiene, containerized local orchestration, database schema/migrations, core API skeletons, and CI/CD. Full OSINT-to-camera-to-frontend integration is a later milestone.

## Architecture

Heimdall is split into four independent modules, all communicating through one central FastAPI backend and Postgres database:

```
                    +-------------+
                    |  frontend/  |  Streamlit dashboard
                    +------+------+
                           | HTTP
                    +------v------+
   +-----------+    |             |    +------------+
   | ai-brain/ +--->|  backend/   |<---+  vision/   |
   | (OSINT)   |    |  (FastAPI + |    |  (YOLOv8)  |
   +-----------+    |  Postgres)  |    +------------+
                     +-------------+
```

- **`backend/`** — FastAPI service exposing CRUD endpoints for five tables: `osint_sources`, `threat_events`, `alert_logs`, `camera_states`, `system_logs`. Alembic-managed Postgres schema with tested up/down migrations.
- **`ai-brain/`** — LangGraph agent that ingests OSINT alerts (currently mock data), classifies them via Groq, and posts threat events to the backend.
- **`vision/`** — YOLOv8-based detection pipeline with a camera-agnostic frame source (currently static test images; a live camera feed can be swapped in later without changing detection logic), posts detections to the backend.
- **`frontend/`** — Streamlit operations console for viewing system state.

Each module is independently runnable and only depends on the backend's REST API, not on each other.

## Local Setup

### Prerequisites
- Docker Desktop
- Python 3.10+ (for running individual modules outside Docker)

### 1. Environment variables

Copy the example env file and fill in real values:

```bash
cp .env.example .env
```

Required variables (Postgres credentials used by both the database and the API container):

```
POSTGRES_DB=heimdall
POSTGRES_USER=heimdall
POSTGRES_PASSWORD=<your own value>
```

### 2. Start the core stack

```bash
docker compose up
```

This launches Postgres and the FastAPI backend together, running Alembic migrations automatically on startup. Confirm it's up:

```bash
curl http://localhost:8000/health
```

### 3. (Optional) Seed sample data

For a populated demo instead of an empty database:

```bash
cd backend
pip install -r requirements.txt
python -m app.seed
```

See `backend/README.md` for details. Safe to run multiple times, it won't create duplicates.

### 4. Run the OSINT and vision modules (optional, standalone)

Each has its own setup and README:

- `ai-brain/README.md` — requires a free Groq API key
- `vision/README.md` — requires test images in `vision/test_media/`

## Testing & CI

- Backend tests: `pytest backend/tests` (requires `PYTHONPATH=.` from repo root)
- Frontend tests: `pytest tests/`
- A GitHub Actions workflow (`.github/workflows/ci.yml`) runs linting, both test suites, and secret scanning on every pull request into `main`.

## Repository Structure

```
.
├── ai-brain/       OSINT ingestion module (LangGraph + Groq)
├── backend/        FastAPI + Postgres core API, migrations, seeder, tests
├── frontend/       Streamlit dashboard
├── vision/         YOLOv8 detection module
├── tests/          Frontend test suite
├── docker-compose.yml
└── .github/workflows/ci.yml
```

## AI Usage

See `AI_USAGE_LOG.md` for a full record of AI-assisted development across the team.
