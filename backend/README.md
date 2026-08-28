# Heimdall Core API

Initial FastAPI and PostgreSQL backend for receiving, classifying, storing, and retrieving OSINT threat events.

## Current data flow

```text
OSINT source
→ POST /threat-events
→ FastAPI validates the request
→ backend assigns a threat level
→ PostgreSQL stores the event
→ GET /threat-events returns prioritized threats
```

## Requirements

- Python 3.9+
- Docker Desktop
- Docker Compose

## Local setup

From the repository root, create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install development dependencies:

```bash
pip install -r backend/requirements-dev.txt
```

Create the local environment file:

```bash
cp .env.example .env
```

Update the values in `.env` if needed.

Start PostgreSQL:

```bash
docker compose up -d postgres
```

Apply database migrations:

```bash
(cd backend && alembic upgrade head)
```

Start the API:

```bash
uvicorn backend.app.main:app --reload
```

Interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Verify the API and PostgreSQL connection |
| `POST` | `/sources` | Create an OSINT source |
| `GET` | `/sources` | Retrieve OSINT sources |
| `POST` | `/threat-events` | Validate, classify, and store a threat |
| `GET` | `/threat-events` | Retrieve threats ordered by highest score |

## Example source request

```json
{
  "name": "Mock OSINT Agent",
  "source_type": "OSINT",
  "is_active": true
}
```

## Example threat request

```json
{
  "source_id": 1,
  "threat_score": 82,
  "summary": "Suspicious activity detected near a monitored location",
  "metadata": {
    "location": "Wichita",
    "keyword": "suspicious activity",
    "mock": true
  }
}
```

The backend generates:

- `id`
- `threat_level`
- `created_at`

## Prototype threat levels

| Score | Level |
|---:|---|
| 0–30 | `NORMAL` |
| 31–50 | `SUSPICIOUS` |
| 51–70 | `ELEVATED` |
| 71–90 | `HIGH_THREAT` |
| 91–100 | `CRITICAL` |

These ranges are prototype defaults and may change after team review.

## Database migrations

Show the current migration:

```bash
(cd backend && alembic current)
```

Apply all migrations:

```bash
(cd backend && alembic upgrade head)
```

Roll back the initial schema:

```bash
(cd backend && alembic downgrade base)
```

Do not roll back a database containing data you need unless it has been backed up.

## Tests

Make sure PostgreSQL is running and migrated:

```bash
docker compose up -d postgres
(cd backend && alembic upgrade head)
```

Run the test suite from the repository root:

```bash
python -m pytest backend/tests -v
```

The tests use real PostgreSQL transactions and roll back their changes, preserving existing local demo data.

## Stop local services

Stop the API with `Control+C`.

Stop PostgreSQL while preserving its data:

```bash
docker compose stop postgres
```