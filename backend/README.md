# Heimdall Core API

Initial FastAPI and PostgreSQL backend for receiving, classifying, storing, and retrieving OSINT threat events and their downstream alert actions.

## Current data flow

```text
OSINT source
→ POST /threat-events
→ FastAPI validates the request
→ backend assigns a threat level
→ PostgreSQL stores the event
→ POST /alert-actions records a downstream response
→ GET endpoints return prioritized threats and actions
```

The current prototype records alert actions but does not yet communicate with the real computer-vision system.

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

## Database tables

### `osint_sources`

Stores the OSINT components that produce threat information.

Main fields:

- `id`
- `name`
- `source_type`
- `is_active`
- `created_at`

### `threat_events`

Stores detected threats and references the OSINT source that produced each threat.

Main fields:

- `id`
- `source_id`
- `threat_score`
- `threat_level`
- `summary`
- `metadata`
- `created_at`

### `alert_actions`

Stores downstream actions connected to threat events.

Main fields:

- `id`
- `threat_event_id`
- `action_type`
- `status`
- `details`
- `created_at`
- `completed_at`

The relationships are:

```text
One OSINT source
→ many threat events

One threat event
→ many alert actions
```

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Verify the API and PostgreSQL connection |
| `POST` | `/sources` | Create an OSINT source |
| `GET` | `/sources` | Retrieve OSINT sources |
| `POST` | `/threat-events` | Validate, classify, and store a threat |
| `GET` | `/threat-events` | Retrieve threats ordered by highest score |
| `POST` | `/alert-actions` | Create a pending action for a threat |
| `GET` | `/alert-actions` | Retrieve alert actions |

## Example source request

```json
{
  "name": "Mock OSINT Agent",
  "source_type": "OSINT",
  "is_active": true
}
```

The database generates:

- `id`
- `created_at`

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

The backend and database generate:

- `id`
- `threat_level`
- `created_at`

## Example alert-action request

```json
{
  "threat_event_id": 1,
  "action_type": "PRIORITIZE_CAMERA_SCAN",
  "details": {
    "priority": "highest",
    "mock": true
  }
}
```

The backend and database generate:

- `id`
- `status` with an initial value of `PENDING`
- `created_at`
- `completed_at` with an initial value of `null`

The action records what Heimdall should do because of a threat. Actually sending commands to the computer-vision system is future integration work.

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

Roll back only the alert-actions migration:

```bash
(cd backend && alembic downgrade 1157e48637ae)
```

Reapply the latest migration:

```bash
(cd backend && alembic upgrade head)
```

Roll back the entire project schema:

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

The current suite covers:

- Database-connected health checks
- Creating and retrieving OSINT sources
- Duplicate source rejection
- Creating and retrieving threat events
- Threat-score validation
- Missing and inactive source handling
- Highest-score-first threat ordering
- Threat-level boundary rules
- Creating and retrieving alert actions
- Missing threat handling for alert actions

## Stop local services

Stop the API with `Control+C`.

Stop PostgreSQL while preserving its data:

```bash
docker compose stop postgres
```