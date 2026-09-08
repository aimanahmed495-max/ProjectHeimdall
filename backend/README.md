# Heimdall Core API

Prototype FastAPI and PostgreSQL backend for receiving, validating, storing, and retrieving data from Heimdall’s system modules.

The database follows the five-table design from the May 2026 final report.

## Prototype 1 scope

Prototype 1 demonstrates:

- PostgreSQL running through Docker
- Five database tables
- Alembic migrations and rollback
- FastAPI endpoints
- JSON validation
- Automated API tests
- Interactive Swagger documentation

Prototype 1 does not include real OSINT ingestion, camera control, YOLO, LangGraph, WebSockets, or frontend integration.

## Current data flow

```text
A system module sends JSON to an API endpoint
→ FastAPI validates the JSON
→ SQLAlchemy creates a database record
→ PostgreSQL stores the record
→ a GET endpoint returns the stored data as JSON
```

For Prototype 1, requests are submitted manually through Swagger or automated tests. Future modules will send the same requests automatically.

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

Open the interactive API documentation:

```text
http://127.0.0.1:8000/docs
```

## Database decision

The final report proposed SQLite for local prototyping and PostgreSQL for the complete system.

Prototype 1 uses PostgreSQL locally through Docker. This keeps development closer to the intended final database and allows PostgreSQL constraints, foreign keys, and migrations to be tested early.

Docker provides an isolated environment in which PostgreSQL runs. Docker is not the database itself.

## Database tables

### `osint_sources`

Stores approved public information sources.

Fields:

- `source_id`
- `source_name`
- `source_type`
- `url`
- `reliability_score`

### `threat_events`

Stores possible visual threat detections.

Fields:

- `event_id`
- `timestamp`
- `object_class`
- `confidence_score`
- `camera_id`
- `status`

### `alert_logs`

Stores alerts associated with threat events.

Fields:

- `alert_id`
- `event_id`
- `alert_time`
- `alert_level`
- `message`
- `acknowledged`

### `camera_states`

Stores camera operating-state history.

Fields:

- `state_id`
- `camera_id`
- `mode`
- `fps`
- `resolution`
- `timestamp`

These are database records only. Prototype 1 does not control physical cameras.

### `system_logs`

Stores messages produced by Heimdall modules.

Fields:

- `log_id`
- `event_id`
- `log_time`
- `module`
- `message`

`event_id` is optional because some system activity may not belong to a specific threat.

More database details are available in `DATABASE_DESIGN.md`.

## Relationships

- One threat event can have multiple alert logs.
- One threat event can have multiple system logs.
- A system log can exist without a threat event.
- Foreign keys prevent alert and event-related log records from referencing nonexistent threats.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/health` | Verify the API and PostgreSQL connection |
| `POST` | `/sources` | Store an OSINT source |
| `GET` | `/sources` | Retrieve OSINT sources |
| `POST` | `/threat-events` | Store a threat event |
| `GET` | `/threat-events` | Retrieve threat events |
| `POST` | `/alert-logs` | Store an alert for a threat |
| `GET` | `/alert-logs` | Retrieve alert logs |
| `POST` | `/camera-states` | Store a camera-state record |
| `GET` | `/camera-states` | Retrieve camera-state records |
| `POST` | `/system-logs` | Store a system-log record |
| `GET` | `/system-logs` | Retrieve system logs |

## Example requests

### OSINT source

```json
{
  "source_name": "National Weather Service",
  "source_type": "Public API",
  "url": "https://www.weather.gov/",
  "reliability_score": 0.95
}
```

### Threat event

```json
{
  "object_class": "Firearm",
  "confidence_score": 0.92,
  "camera_id": 1,
  "status": "Pending"
}
```

### Alert log

```json
{
  "event_id": 1,
  "alert_level": "Critical",
  "message": "High-confidence firearm detection",
  "acknowledged": false
}
```

### Camera state

```json
{
  "camera_id": 1,
  "mode": "Dormant",
  "fps": 5,
  "resolution": "720p"
}
```

Valid prototype modes are `Dormant` and `Active`.

### System log

```json
{
  "event_id": null,
  "module": "OSINT",
  "message": "OSINT polling started"
}
```

## Validation

FastAPI and Pydantic reject invalid requests before database records are created.

Current examples include:

- Confidence and reliability scores must be from `0.0` to `1.0`.
- Camera IDs must be positive.
- FPS must be positive.
- Camera mode must be `Dormant` or `Active`.
- Required text fields cannot be empty.
- Duplicate OSINT source names return a conflict response.
- Alert logs cannot reference missing threat events.
- System logs with an event ID cannot reference missing threat events.

PostgreSQL also enforces important score ranges and foreign-key relationships.

## Database migrations

Show the current revision:

```bash
(cd backend && alembic current)
```

Check whether the models and database match:

```bash
(cd backend && alembic check)
```

Apply all migrations:

```bash
(cd backend && alembic upgrade head)
```

Roll back the report-alignment migration:

```bash
(cd backend && alembic downgrade 226eb47c96bb)
```

Reapply it:

```bash
(cd backend && alembic upgrade head)
```

Back up important data before destructive migrations:

```bash
mkdir -p backups
docker compose exec -T postgres pg_dump -U heimdall -d heimdall > backups/heimdall_backup.sql
```

Local database backups are ignored by Git.

## Tests

Make sure PostgreSQL is running and migrated:

```bash
docker compose up -d postgres
(cd backend && alembic upgrade head)
```

Run the tests from the repository root:

```bash
python -m pytest backend/tests -v
```

The current suite contains 18 tests covering:

- Database-connected health checks
- Creating and retrieving all five record types
- Duplicate OSINT source handling
- Reliability-score validation
- Confidence-score validation
- Camera ID, mode, and FPS validation
- Missing threat handling for alert logs
- System logs with and without threat events
- Missing threat handling for system logs

The tests use real PostgreSQL transactions and roll back their changes so local demo data is preserved.

## Stop local services

Stop the API with `Control+C`.

Stop PostgreSQL while preserving its data:

```bash
docker compose stop postgres
```