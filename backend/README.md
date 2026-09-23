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

## Prototype 2 authentication foundation

The backend now includes a supporting authentication layer alongside the five report-domain tables.

Authentication features include:

- User registration with username and password validation
- Argon2 password hashing
- Signed JWT access tokens
- Bearer-token validation
- Active-account and soft-delete checks
- Protected current-user retrieval

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

## Run the complete backend with Docker

Build and start both PostgreSQL and FastAPI:

```bash
docker compose up -d --build
```

Check container status:

```bash
docker compose ps
```

The PostgreSQL health check must pass before the API starts. The API container automatically applies pending Alembic migrations and then starts Uvicorn.

Open:

```text
API documentation: http://127.0.0.1:8000/docs
Health check:      http://127.0.0.1:8000/health
```

View API logs:

```bash
docker compose logs api
```

The local setup below remains available when developers want to run FastAPI from a Python virtual environment while PostgreSQL runs through Docker.

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

Generate a local JWT signing secret:

```bash
openssl rand -hex 32
```

Add the generated value and authentication settings to the private `.env` file:

```text
JWT_SECRET_KEY=replace_with_generated_secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_MINUTES=30
ENABLE_USER_REGISTRATION=true
```

Set `ENABLE_USER_REGISTRATION=false` after the required accounts have been created to disable public registration.

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

Stores possible threat detections produced by camera or OSINT pipelines.

Fields:

- `event_id`
- `timestamp`
- `source_id` (optional)
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

Stores the current operating state of each registered camera. Each `camera_id` is unique.
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

### Supporting `users` table

Stores authentication accounts separately from the five report-domain tables.

Fields:

- `user_id`
- `username`
- `password_hash`
- `is_active`
- `created_at`
- `deleted_at`

Passwords are stored only as Argon2 hashes. `deleted_at` supports soft deletion without destroying account records.

## API endpoints

| Method | Endpoint | Access | Purpose |
|---|---|---|---|
| `GET` | `/health` | Public | Verify the API and PostgreSQL connection |
| `POST` | `/sources` | Bearer token | Store an OSINT source |
| `GET` | `/sources` | Public | Retrieve OSINT sources |
| `POST` | `/threat-events` | Bearer token | Store a threat event |
| `GET` | `/threat-events` | Public | Retrieve threat events |
| `POST` | `/alert-logs` | Bearer token | Store an alert for a threat |
| `GET` | `/alert-logs` | Public | Retrieve alert logs |
| `POST` | `/camera-states` | Bearer token | Register a camera state |
| `GET` | `/camera-states` | Public | Retrieve camera states |
| `GET` | `/camera-states/{camera_id}` | Public | Retrieve one registered camera state |
| `PUT` | `/camera-states/{camera_id}` | Bearer token | Update a registered camera state |
| `POST` | `/system-logs` | Bearer token | Store a system log |
| `GET` | `/system-logs` | Public | Retrieve system logs |
| `POST` | `/auth/register` | Public when enabled | Register a user with a hashed password |
| `POST` | `/auth/login` | Public | Validate credentials and return a JWT |
| `GET` | `/auth/me` | Bearer token | Retrieve the authenticated user |
Protected requests must include an `Authorization: Bearer <access_token>` header. Missing, malformed, expired, or invalid tokens return HTTP 401.

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
## Database relationships

The five report tables are connected through the following relationships:

- One OSINT source can contribute to many threat events.
- `threat_events.source_id` is optional because camera detections may not originate from OSINT.
- Deleting an OSINT source sets related threat-event `source_id` values to `NULL`.
- One registered camera can produce many threat events.
- Every threat event must reference an existing unique `camera_states.camera_id`.
- A camera state cannot be deleted while threat events still reference it.
- One threat event can produce many alert logs.
- One threat event can be referenced by many optional system logs.

## Validation

FastAPI and Pydantic reject invalid requests before database records are created.

Current examples include:

- Confidence and reliability scores must be from `0.0` to `1.0`.
- Camera IDs must be positive.
- FPS must be positive.
- Camera mode must be `Dormant` or `Active`.
- Required text fields cannot be empty.
- Duplicate OSINT source names return a conflict response.
- Duplicate camera IDs return a conflict response.
- Threat events cannot reference missing cameras.
- Threat events with a source ID cannot reference missing OSINT sources.
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


```markdown
Roll back the latest authentication migration:

```bash
(cd backend && alembic downgrade c61901464e7c)
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
## Seed sample data

After migrations are applied, load fake demo rows for local development:

```bash
(cd backend && python -m app.seed)
```

The seeder is idempotent. Running it again skips rows that already exist and does not violate unique constraints.

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
Run the Prototype 2 coverage gate:

```bash
python -m pytest backend/tests \
  --cov=backend.app \
  --cov-report=term-missing \
  --cov-fail-under=60
```

The current backend test suite contains 48 tests and reaches 97.45% coverage.

The current suite contains 48 tests covering:

- Database-connected health checks
- Creating and retrieving all five record types
- Duplicate OSINT source handling
- Duplicate camera ID handling
- Reliability-score validation
- Confidence-score validation
- Camera ID, mode, and FPS validation
- Threat-to-source and threat-to-camera relationships
- Missing source and camera handling for threat events
- Missing threat handling for alert logs
- System logs with and without threat events
- Missing threat handling for system logs
- Seeder idempotency with existing unique camera IDs
- Retrieving and updating individual camera states
- Missing-camera responses
- Vision-client camera registration and update behavior
- User registration and duplicate-username handling
- Argon2 password-hash storage
- Login and JWT generation
- Protected-route authentication
- Invalid-token and inactive-user rejection
- Minimum 60% backend coverage enforcement

The tests use real PostgreSQL transactions and roll back their changes so local demo data is preserved.
## Stop local services

Stop the API with `Control+C`.

Stop PostgreSQL while preserving its data:

```bash
docker compose stop postgres
```