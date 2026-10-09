# Project Heimdall

Heimdall is a prototype for an edge-to-cloud surveillance workflow: open-source reports are classified into threat events, a vision pipeline posts object detections, and an operations console reads the shared record store. The modules in this repository talk to one FastAPI service and one PostgreSQL database. They do not call each other.

This tree includes the core API, database migrations, authenticated OSINT ingestion from local mock alerts, YOLOv8 detection on still images, and a Streamlit operations console. OSINT classification does not switch the camera pipeline on or off. The vision pipeline uses files in `vision/test_media/` and does not open a hardware camera.

More detail lives in [docs/](docs/):

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — components, schema, and login flow
- [docs/DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md) — setup, tests, and troubleshooting
- [docs/OWASP_AUDIT.md](docs/OWASP_AUDIT.md) — OWASP Top 10 (2021) review of this code

## Architecture

```text
                    +-------------+
                    |  frontend/  |  Streamlit console (browser calls the API)
                    +------+------+
                           | HTTP
                    +------v------+
   +-----------+    |             |    +------------+
   | ai-brain/ +--->|  backend/   |<---+  vision/   |
   | (OSINT)   |    |  FastAPI +  |    |  YOLOv8    |
   +-----------+    |  Postgres   |    +------------+
                    +-------------+
```

- **`backend/`** — FastAPI service and Alembic migrations. Domain tables: `osint_sources`, `threat_events`, `alert_logs`, `camera_states`, `system_logs`. Authentication uses a separate `users` table. Data routes require a bearer token. `GET /health` is public.
- **`ai-brain/`** — LangGraph pipeline. It logs in, registers mock sources, classifies mock alert text with Groq, and posts a threat event (`source_id` set, no camera id) plus a system log.
- **`vision/`** — YOLOv8n over still images from `vision/test_media/`. It logs in, sets camera `1` to `Active`, posts detections as threat events and system logs, then sets that camera to `Dormant`.
- **`frontend/`** — Streamlit host for `frontend/heimdall_console.html`. After login the page polls `/sources`, `/threat-events`, `/alert-logs`, `/camera-states`, and `/system-logs`.

`docker-compose.yml` starts PostgreSQL, the API, and the Streamlit console. OSINT and vision run on the host. `frontend/demo_backend/main.py` is an in-memory mock used by tests. It is not a Compose service, and the console does not call it.

## Features in this prototype

- User registration (when enabled), login, and `GET /auth/me`
- Argon2 password hashes and signed JWT access tokens
- Create, list, and fetch OSINT sources; soft-delete a source
- Create, list, fetch, update, and soft-delete threat events (status and corroboration time)
- Create, list, fetch, acknowledge, and soft-delete alert logs
- Register and update camera state (`Dormant` or `Active`)
- Create and list system logs
- Mock OSINT ingestion and still-image detection posting into that API
- Operations console with login, registration, and a five-second refresh of those collections
- Idempotent demo seed (`backend/app/seed.py`)

## Tech stack

| Piece | Used here |
| --- | --- |
| Language | Python 3.11 in the Dockerfiles and in CI |
| API | FastAPI, Uvicorn, Pydantic, SQLAlchemy 2, Alembic, psycopg2 |
| Database | PostgreSQL 17 (`postgres:17-alpine`) |
| Auth | pwdlib with the Argon2 extra, PyJWT |
| Console | Streamlit, static HTML/CSS/JS |
| OSINT | LangGraph, `langchain-groq`, Groq model `openai/gpt-oss-20b` |
| Vision | Ultralytics YOLOv8n, OpenCV |
| Local runtime | Docker Compose |
| Checks | pytest, Ruff, complexipy, pip-audit, TruffleHog, Dependabot |

## Quick start

Prerequisites: Docker Desktop (or another Docker Compose v2 install) and a copy of this repo.

```bash
cp .env.example .env
docker compose down -v
docker compose up
```

`docker compose down -v` deletes the local `postgres_data` volume so the next start migrates a clean database. `docker compose up` builds the API and the console, waits for PostgreSQL, runs `alembic upgrade head`, and starts Uvicorn.

Then check the API:

```bash
curl http://localhost:8000/health
```

A healthy process returns JSON with `"status": "ok"` and `"database": "connected"`. Interactive API docs are at <http://localhost:8000/docs>. The console is at <http://localhost:8501>.

Replace the placeholder `JWT_SECRET_KEY` in `.env` before you use the stack for anything beyond a throwaway demo. `openssl rand -hex 32` is enough for a local value. Set `ENABLE_USER_REGISTRATION` to `false` after the accounts you need exist.

Seed data, module setup, and test commands are in [docs/DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md).

## Environment variables

Names only. Put values in gitignored `.env` files, not in git.

Root `.env` (Compose, API, and console), from `.env.example`:

- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `HEIMDALL_API_URL`
- `HEIMDALL_WS_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `JWT_ACCESS_TOKEN_MINUTES`
- `ENABLE_USER_REGISTRATION`

`backend/app/database.py` also reads `POSTGRES_HOST` and `POSTGRES_PORT`. Compose sets those on the API service. On the host they default to `localhost` and `5432`.

`ai-brain/.env`, from `ai-brain/.env.example`:

- `GROQ_API_KEY`
- `BASE_URL`
- `OSINT_API_USERNAME`
- `OSINT_API_PASSWORD`

`vision/.env`, from `vision/.env.example`:

- `BASE_URL`
- `VISION_API_USERNAME`
- `VISION_API_PASSWORD`

`HEIMDALL_WS_URL` is read by `frontend/app.py`. The console HTML does not open a WebSocket, and `backend/app/main.py` does not define `/ws/events`. The core UI uses HTTP.

## Tests and linting

From the repository root, with dependencies installed (see [docs/DEVELOPER_SETUP.md](docs/DEVELOPER_SETUP.md)):

```bash
# Backend. PostgreSQL must be migrated. Export the same POSTGRES_* and JWT_* variables CI uses.
pytest backend/tests --cov=backend.app --cov-report=term-missing --cov-fail-under=60

# OSINT unit tests (HTTP and Groq are mocked)
pytest ai-brain/tests -q

# Vision has no vision/tests directory yet. CI skips pytest in that case.
pytest vision/tests -q

# Streamlit host and console source checks
pytest tests/

# Browser-side console checks (Node)
npm ci --prefix tests/frontend-console
npm test --prefix tests/frontend-console
```

`pyproject.toml` sets pytest `testpaths` to `tests/`, so a bare `pytest` does not collect `backend/tests` or `ai-brain/tests`. Pass those paths.

Lint and complexity, matching CI:

```bash
ruff check backend/
ruff check ai-brain/
ruff check vision/
complexipy backend --max-complexity-allowed 15
complexipy ai-brain --max-complexity-allowed 15
complexipy vision --max-complexity-allowed 15
```

Ruff selects `E`, `F`, `I`, and `C901` in `pyproject.toml`, with McCabe `max-complexity` 10. `backend/ruff.toml` and `vision/ruff.toml` extend that file. Backend Ruff excludes `backend/alembic`.

Dependency audit, including the ignores currently encoded in CI:

```bash
pip-audit -r backend/requirements-dev.txt \
  --ignore-vuln PYSEC-2026-1845 \
  --ignore-vuln PYSEC-2026-161 \
  --ignore-vuln PYSEC-2026-248 \
  --ignore-vuln PYSEC-2026-249 \
  --ignore-vuln PYSEC-2026-2280 \
  --ignore-vuln PYSEC-2026-2281
pip-audit -r ai-brain/requirements.txt
pip-audit -r vision/requirements.txt
```

## CI

`.github/workflows/ci.yml` runs on pull requests to `main`:

| Job | Checks |
| --- | --- |
| `backend` | Ruff (including C901), complexipy (max 15), Alembic upgrade, pytest with coverage floor 60, `pip-audit` with the ignores listed above |
| `osint` | Ruff, complexipy, pytest, `pip-audit` |
| `vision` | Ruff, complexipy, pytest only if `vision/tests` exists, `pip-audit` |
| `frontend` | `pytest tests/`, then Node 22 `npm test` in `tests/frontend-console` |
| `secret-scan` | TruffleHog with `--only-verified` on full git history |

`.github/dependabot.yml` opens weekly update PRs for pip, GitHub Actions, and the backend and frontend Dockerfiles.

## Branches and commits

- `feature/*` for product changes
- `chore/*` for maintenance that is not a user-facing feature
- `docs/*` for documentation
- Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `ci:`)
- A pull request links the Issue it closes

## Layout

```text
.
├── ai-brain/                 OSINT ingestion (LangGraph + Groq)
├── backend/                  FastAPI, Alembic, seed, backend tests
├── frontend/                 Streamlit console
├── vision/                   YOLOv8 still-image pipeline
├── tests/                    Console and demo-backend tests
├── docs/                     Architecture, setup, OWASP audit
├── docker-compose.yml
└── .github/workflows/ci.yml
```

Module notes: `backend/README.md`, `ai-brain/README.md`, `vision/README.md`, `frontend/README.md`.

## AI usage

See `AI_USAGE_LOG.md` for the team's record of AI-assisted development.
