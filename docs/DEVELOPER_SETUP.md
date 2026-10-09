# Developer setup

These steps match the Docker Compose stack and the CI commands in `.github/workflows/ci.yml`. They target macOS or Linux. Windows is untested in this repo.

## 1. Prerequisites

- Git
- Docker with Compose v2 (`docker compose version`)
- Python 3.11 or newer (`python3 --version`). The API and console images use `python:3.11-slim`, and CI uses Python 3.11.
- Node.js 22 if you will run `tests/frontend-console`. That package asks for Node `>=20.19.0`. CI uses Node 22.

OSINT and vision are optional host programs. OSINT needs a Groq API key. Vision downloads `yolov8n.pt` on first detection.

## 2. Clone

```bash
git clone <repository-url> ProjectHeimdall
cd ProjectHeimdall
```

## 3. Environment files

```bash
cp .env.example .env
```

Edit `.env` and set your own `POSTGRES_PASSWORD` and `JWT_SECRET_KEY`. Generate a local signing key with:

```bash
openssl rand -hex 32
```

Leave `JWT_ALGORITHM` as `HS256` and `JWT_ACCESS_TOKEN_MINUTES` as `30` unless you are changing auth on purpose. `ENABLE_USER_REGISTRATION=true` lets `POST /auth/register` create accounts. Set it to `false` after those accounts exist.

The API reads the root `.env` through `load_dotenv` in `backend/app/database.py` and `backend/app/security.py`. Compose reads the same file for variable substitution.

For the optional modules:

```bash
cp ai-brain/.env.example ai-brain/.env
cp vision/.env.example vision/.env
```

Fill `GROQ_API_KEY`, `OSINT_API_USERNAME`, and `OSINT_API_PASSWORD` in `ai-brain/.env`. Fill `VISION_API_USERNAME` and `VISION_API_PASSWORD` in `vision/.env`. Those usernames must already exist in `users` (register them through the API or the console). Both clients default `BASE_URL` to `http://localhost:8000`.

Do not commit `.env` files. `.gitignore` ignores them and keeps `.env.example`.

## 4. Start the stack

From the repository root:

```bash
docker compose down -v
docker compose up
```

`down -v` removes the named volume `postgres_data`. The next `up` creates an empty database, and the API container applies migrations before it serves traffic. The first build installs Python dependencies into the API and frontend images.

Leave that terminal running, or use `docker compose up -d` if you want the stack in the background. Logs:

```bash
docker compose logs api
docker compose ps
```

PostgreSQL must be healthy before the API process starts (`depends_on` in `docker-compose.yml`).

## 5. Seed demo data

Migrations do not insert demo rows. After the API is up, seed from a host virtualenv so the seeder uses `localhost:5432`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
(cd backend && python -m app.seed)
```

`backend/app/seed.py` inserts demo OSINT sources, camera states, threat events, alert logs, and system logs. Running it again skips rows that already match its stable keys.

The API image does not copy the root `.env`. Inside Compose the database host name is `postgres`, which is already in the API container environment, so this also works:

```bash
docker compose exec api python -m backend.app.seed
```

## 6. Health check

```bash
curl http://localhost:8000/health
```

Expect HTTP 200 and a body like:

```json
{"status":"ok","database":"connected"}
```

`GET /health` is unauthenticated. It executes `SELECT 1`. Other data routes return HTTP 401 until you register or log in.

Open the console at <http://localhost:8501> and the API docs at <http://localhost:8000/docs>.

Create an account from the console, or:

```bash
curl -s -X POST http://localhost:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"operator.demo","password":"replace-with-12-plus-chars"}'
```

Usernames are 3–100 characters matching `^[A-Za-z0-9_.-]+$`. Passwords are 12–128 characters. Registration stores the username in lowercase.

## 7. Tests

Activate the virtualenv from step 5. Backend tests need a migrated PostgreSQL. Install dev extras once:

```bash
python -m pip install -r backend/requirements-dev.txt
python -m pip install pytest ruff complexipy pip-audit
```

Export the database and JWT variables the tests import at startup. From the repository root, against the Compose database:

```bash
export POSTGRES_DB=heimdall
export POSTGRES_USER=heimdall
export POSTGRES_PASSWORD='the value in your .env'
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export JWT_SECRET_KEY='the value in your .env'
export JWT_ALGORITHM=HS256
export JWT_ACCESS_TOKEN_MINUTES=30
```

Use the values you put in `.env`. CI uses its own database name `test` and a throwaway JWT secret. It does not read your `.env`.

```bash
pytest backend/tests --cov=backend.app --cov-report=term-missing --cov-fail-under=60
```

Backend tests roll back their PostgreSQL changes (`backend/tests/conftest.py`).

OSINT tests mock HTTP and do not need a running API or a Groq key:

```bash
python -m pip install -r ai-brain/requirements.txt
pytest ai-brain/tests -q
```

Vision tests: there is no `vision/tests` directory. CI prints a notice and skips pytest. After that directory exists:

```bash
python -m pip install -r vision/requirements.txt
pytest vision/tests -q
```

`backend/tests/test_vision_client.py` mocks the vision HTTP client and runs with the backend suite. It does not load YOLOv8.

Console tests:

```bash
python -m pip install -r frontend/requirements.txt
pytest tests/
```

`tests/test_dashboard.py` loads the Streamlit app and checks that the console HTML lists the core API paths. `tests/test_frontend_demo_api.py` starts the in-memory mock in `frontend/demo_backend/main.py`, not the Compose API.

Node checks:

```bash
npm ci --prefix tests/frontend-console
npm test --prefix tests/frontend-console
```

## 8. Linting

From the repository root:

```bash
ruff check backend/
ruff check ai-brain/
ruff check vision/
complexipy backend --max-complexity-allowed 15
complexipy ai-brain --max-complexity-allowed 15
complexipy vision --max-complexity-allowed 15
```

Ruff’s `C901` rule is enabled in `pyproject.toml` with McCabe complexity capped at 10. complexipy’s cap in CI is 15. Backend Ruff does not lint `backend/alembic`.

Optional local dependency audit:

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

The ignore list is the same one in `.github/workflows/ci.yml`. Those advisories are accepted until the pytest 9 and Starlette 1.x upgrades.

## 9. Run OSINT or vision

Start Compose first so `http://localhost:8000` answers, and register the usernames in the module `.env` files.

```bash
cd ai-brain
python main.py
```

```bash
cd vision
python main.py
```

Vision exits 0 with a message if `vision/test_media/` has no images. Supported suffixes are `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, and `.tiff`.

## 10. Troubleshooting

**API container exits immediately.** `docker compose logs api` shows the command `alembic upgrade head` and then Uvicorn. If Alembic throws, Uvicorn never starts. A missing `JWT_SECRET_KEY` or Postgres variable raises `RuntimeError` on import (`backend/app/security.py`, `backend/app/database.py`).

**`ForeignKeyViolation` on `threat_events` during startup.** The API command stops when migrations fail. Revision `c61901464e7c` adds `fk_threat_events_camera_id_camera_states` from `threat_events.camera_id` to `camera_states.camera_id` and does not rewrite existing rows. An old `postgres_data` volume can fail that step. Reset the local volume:

```bash
docker compose down -v
docker compose up
```

That deletes local database data.

**`curl` to `/health` hangs or connection refused.** Check `docker compose ps`. The API waits until `pg_isready` succeeds. Host port 5432 or 8000 already in use will keep the new container from binding.

**401 on every data route.** `GET /health` is the only public data-style route. Send `Authorization: Bearer` with a token from `POST /auth/login`. Expired tokens use the same 401 body as a wrong password.

**403 on `POST /auth/register`.** `ENABLE_USER_REGISTRATION` is off. The check is in `backend/app/auth.py`.

**OSINT or vision says the API is unreachable.** `BASE_URL` should be `http://localhost:8000` when the client runs on the host. The Compose DNS name `postgres` is only valid inside the Docker network.

**OSINT exits on a missing Groq key.** `OsintAgent` raises if `GROQ_API_KEY` is empty (`ai-brain/osint_agent.py`).

**Seed cannot connect.** From the host, `POSTGRES_HOST` must be `localhost` and the published port must be `5432`. From `docker compose exec api`, the host is `postgres`, which Compose already sets.

**Bare `pytest` only runs `tests/`.** `pyproject.toml` sets `testpaths = ["tests"]`. Pass `backend/tests` or `ai-brain/tests` explicitly.
