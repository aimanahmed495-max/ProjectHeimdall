# OWASP Top 10 (2021) audit

Audit of the Heimdall prototype as implemented in this repository, reviewed on 2026-10-08. Every control below was checked against the current source. This is a local prototype: Docker Compose publishes plain HTTP, and there is no separate production configuration in the repo.

Scope: `backend/app/`, `backend/alembic/versions/`, `docker-compose.yml`, the `.env.example` files, `ai-brain/`, `vision/`, `frontend/`, `.github/workflows/ci.yml`, and `.github/dependabot.yml`.

| Status | Meaning |
| --- | --- |
| Implemented | The category is addressed by the current code for this prototype. |
| Partial | Some controls exist, and a concrete gap remains. |
| Open | The category applies and the code does not address it. |
| Not applicable | The category has no relevant sink in this repository. |

## A01 Broken Access Control

**Applies.** The API stores and returns operational records, and the browser console calls those routes.

**What the code does.** `backend/app/main.py` attaches `Depends(get_current_user)` to every data route. `GET /health` is public and runs `SELECT 1`. Authentication routes live in `backend/app/auth.py`:

| Route | Access |
| --- | --- |
| `GET /health` | Public |
| `POST /auth/register` | Public when `ENABLE_USER_REGISTRATION` is enabled; otherwise HTTP 403 |
| `POST /auth/login` | Public |
| `GET /auth/me` | Bearer token |
| `POST/GET/DELETE /sources` and `GET /sources/{source_id}` | Bearer token |
| `POST/GET /threat-events`, `GET/PATCH/DELETE /threat-events/{event_id}` | Bearer token |
| `POST/GET /alert-logs`, `GET/PATCH/DELETE /alert-logs/{alert_id}` | Bearer token |
| `POST/GET /camera-states`, `GET/PUT /camera-states/{camera_id}` | Bearer token |
| `POST/GET /system-logs` | Bearer token |

`get_current_user` requires an `Authorization: Bearer` token, decodes it, and loads a row from `users` that is active and has `deleted_at` unset. Missing, malformed, expired, and unknown tokens all return HTTP 401 with `WWW-Authenticate: Bearer`.

There is no role column on `users` in `backend/app/models.py` and no role check in `backend/app/auth.py` or `backend/app/main.py`. Any active account can create, read, update, and soft-delete every record. Records are not scoped to the caller.

CORS is set in `backend/app/main.py` to `http://localhost:8501` and `http://127.0.0.1:8501`, with `allow_credentials=False`, methods `GET`, `POST`, `PUT`, `PATCH`, `DELETE`, and `OPTIONS`, and headers `Authorization` and `Content-Type`.

`ENABLE_USER_REGISTRATION` defaults to `true` in `backend/app/auth.py` and in `docker-compose.yml`. A caller who can reach the API can register and then use every protected route. The FastAPI application constructor does not disable `/docs`, `/redoc`, or `/openapi.json`.

**Status: Partial.**

**Remaining gap.** No roles, no per-record ownership, and self-service registration is on unless the environment variable is set to a false value.

## A02 Cryptographic Failures

**Applies.** Passwords and session tokens are security-sensitive.

**What the code does.** `backend/app/security.py` reads `JWT_SECRET_KEY`, `JWT_ALGORITHM` (default `HS256`), and `JWT_ACCESS_TOKEN_MINUTES` (default `30`) from the environment. Import fails with `RuntimeError` if `JWT_SECRET_KEY` is missing. `create_access_token` signs a payload of `sub` (the user id as a string), `iat`, and `exp` with PyJWT. `decode_access_token` requires those three claims and accepts only the configured algorithm.

`PasswordHash.recommended()` from `pwdlib` hashes and verifies passwords. `backend/requirements.txt` installs `pwdlib[argon2]`. `POST /auth/register` stores `password_hash` and never returns it: `UserRead` in `backend/app/schemas.py` includes `user_id`, `username`, `is_active`, `created_at`, and `deleted_at` only.

Database credentials are also environment variables. `backend/app/database.py` requires `POSTGRES_DB`, `POSTGRES_USER`, and `POSTGRES_PASSWORD`, defaults host and port to `localhost` and `5432`, and URL-encodes the password. `docker-compose.yml` injects the same Postgres variables plus the JWT settings into the API container. `.env.example` files contain names and placeholders. `.gitignore` ignores `.env` and `.env.*` except `.env.example`.

The Compose file publishes `http://localhost:8000` and `http://localhost:8501`. Nothing in the repo terminates TLS. The access token is returned in the JSON body (`TokenResponse` in `backend/app/schemas.py`). The console keeps it in a JavaScript variable (`authState.token` in `frontend/heimdall_console.html`) and does not write it to `localStorage` or `sessionStorage`. There is no refresh token and no server-side session store.

**Status: Partial.**

**Remaining gap.** Local traffic is unencrypted HTTP. A stolen bearer token stays valid until `exp` because the server does not keep a revocation list.

## A03 Injection

**Applies.** Clients send JSON that is written to PostgreSQL, and the console renders API data.

**What the code does.** Request bodies are Pydantic models in `backend/app/schemas.py`. Constraints include string lengths, username pattern `^[A-Za-z0-9_.-]+$`, password length 12–128 on registration, scores bounded from 0 to 1, positive ids and FPS, camera mode `Dormant` or `Active`, and a model validator that requires a threat event to have `source_id`, `camera_id`, or both. Invalid bodies are rejected by FastAPI before a row is inserted.

Queries in `backend/app/main.py` and `backend/app/auth.py` use the SQLAlchemy ORM (`select`, `db.get`, `db.scalar`). The only SQL string in the application is `text("SELECT 1")` on `GET /health`. User text is passed as bound column values, not concatenated into SQL. PostgreSQL check constraints in `backend/app/models.py` repeat the score ranges and the threat-event origin rule.

`osint_sources.url` is a non-empty string. The schema does not require an HTTP URL. The API stores that value and does not pass it to a shell or a database function.

**Status: Implemented.**

**Remaining gap.** `url` is not validated as a URL. That does not create a SQL injection path. See A10 for how that field is used.

## A04 Insecure Design

**Applies.** The prototype is a shared operational store with a single class of user.

**What the code does.** The implemented design is a FastAPI service in front of PostgreSQL, with OSINT and vision as separate HTTP clients and a browser console that polls the API. Threat events must name an OSINT source, a camera, or both (`ck_threat_events_has_origin` in `backend/app/models.py`). Soft-deleted sources, events, and alerts are hidden from normal reads and cannot be referenced by new rows (`backend/app/main.py`). Duplicate usernames, source names, and camera ids return HTTP 409.

The same design gives every registered user full read and write access, leaves registration on by default, and has no abuse throttling (see A07). `ai-brain/main.py` classifies local mock JSON. It does not pull live OSINT feeds, and it does not call the vision module. `vision/main.py` always processes still images for camera id 1. OSINT output does not change camera mode.

**Status: Partial.**

**Remaining gap.** One shared privilege level and open registration are the access-control design, not an unfinished check around a role model. The `users` table has no role to enforce.

## A05 Security Misconfiguration

**Applies.** Local Docker, environment files, and framework defaults are the deployment surface.

**What the code does.** `backend/app/main.py` constructs `FastAPI(...)` without `debug=True`. The API command in `docker-compose.yml` and `backend/Dockerfile` is Uvicorn on `0.0.0.0:8000` without `--reload`. `backend/Dockerfile` and `frontend/Dockerfile` use `python:3.11-slim` and do not set a `USER`, so the containers run as root. Compose publishes PostgreSQL on host port 5432, the API on 8000, and Streamlit on 8501. The database image is `postgres:17-alpine` with a health check that must pass before the API starts. The API command runs `alembic upgrade head` and then Uvicorn.

`.env.example`, `ai-brain/.env.example`, and `vision/.env.example` list variable names and placeholders. Real values are loaded from the environment or from gitignored `.env` files (`backend/app/database.py`, `backend/app/security.py`, `ai-brain/osint_client.py`, `vision/vision_client.py`). CORS is limited to the local Streamlit origins. The interactive docs routes stay at the FastAPI defaults.

**Status: Partial.**

**Remaining gap.** Root containers, a database port published on the host, public API docs, and registration defaulting to on. Those match a local prototype and are not locked down further in this repo.

## A06 Vulnerable and Outdated Components

**Applies.** Python dependencies are installed in CI and in the images.

**What the code does.** `.github/workflows/ci.yml` runs `pip-audit` for `backend/requirements-dev.txt`, `ai-brain/requirements.txt`, and `vision/requirements.txt` on pull requests to `main`. The backend audit ignores these accepted findings because the comments in that workflow say the fixes need major upgrades:

- `PYSEC-2026-1845` — pytest 9. The pin is `pytest==8.4.2` in `backend/requirements-dev.txt` (development and test only).
- `PYSEC-2026-161`, `PYSEC-2026-248`, `PYSEC-2026-249`, `PYSEC-2026-2280`, and `PYSEC-2026-2281` — starlette 1.x. `fastapi==0.128.8` in `backend/requirements.txt` pulls Starlette 0.x.

`.github/dependabot.yml` schedules weekly updates for pip (`/backend`, `/ai-brain`, `/vision`, `/frontend`), GitHub Actions, and Docker (`/backend`, `/frontend`). Backend runtime requirements are version-pinned. `ai-brain/requirements.txt` is not pinned (`langgraph`, `langchain-groq`, `requests`, `python-dotenv`). The frontend CI job installs `frontend/requirements.txt` and does not run `pip-audit`. That job does run `npm ci` and `npm test` for `tests/frontend-console`.

**Status: Partial.**

**Remaining gap.** The six ignored backend advisories, unpinned OSINT requirements, and no `pip-audit` step for the frontend job.

## A07 Identification and Authentication Failures

**Applies.** Operators, the OSINT client, and the vision client all log in with a username and password.

**What the code does.** `POST /auth/register` lowercases the username, enforces the schema rules above, and stores an Argon2 hash. `POST /auth/login` looks up an active, non-deleted user by lowercased username and calls `verify_password`. Failure uses one message, `Invalid or expired authentication credentials.`, for an unknown user and a wrong password (`backend/app/auth.py`). Success returns a signed access token and `token_type` `bearer`.

`GET /auth/me` returns the user for that token. Inactive or soft-deleted users fail both login and later requests. The OSINT client (`ai-brain/osint_client.py`) and the vision client (`vision/vision_client.py`) post to `/auth/login` and send `Authorization: Bearer` on later calls. The console (`frontend/heimdall_console.html`) does the same, then calls `/auth/me`, and clears the password field after the attempt. Logout in the console drops the in-memory token only. There is no logout route.

No module under `backend/app/` implements login rate limiting, an attempt counter, or account lockout. The console maps HTTP 429 to a “too many attempts” string, and the API never returns 429.

**Status: Partial.**

**Remaining gap.** Login rate limiting and account lockout are absent. Tokens cannot be revoked before expiry.

## A08 Software and Data Integrity Failures

**Applies.** Dependencies, migrations, and CI are the integrity controls in this repo.

**What the code does.** `.github/workflows/ci.yml` runs on pull requests to `main`. The backend job checks out the repo, installs pinned requirements, runs Ruff, complexipy, `alembic upgrade head` against PostgreSQL 17, pytest with a coverage floor of 60 percent, and `pip-audit`. The OSINT and vision jobs lint, run complexipy, test (vision tests are skipped when `vision/tests` is missing), and audit. The `secret-scan` job runs TruffleHog (`trufflesecurity/trufflehog@main`) with `fetch-depth: 0` and `--only-verified`.

Alembic revisions in `backend/alembic/versions/` are the schema history. Current models match the head revision `0dafecf04f65`, which adds soft-delete and corroboration columns. `alert_actions` was created in `226eb47c96bb` and dropped in the upgrade path of `017083aec8b1`. It is not in `backend/app/models.py`.

`vision/detector.py` loads Ultralytics weights from `yolov8n.pt` and can download them on first use. The repo does not pin a checksum for that file. `ai-brain/requirements.txt` is unpinned, so OSINT installs are not locked to a hash or version.

**Status: Partial.**

**Remaining gap.** Unpinned OSINT dependencies and an unsigned YOLO weight download. CI secret scanning covers verified secrets in git history, not a signed release artifact.

## A09 Security Logging and Monitoring Failures

**Applies.** Authentication and data changes should be traceable. The repo has an application log table and a CI secret scan, which are different things.

**What the code does.** `system_logs` in `backend/app/models.py` stores `module` and `message`, with an optional `event_id`. Rows are created only when a client calls `POST /system-logs`. The OSINT agent and the vision pipeline post those rows after a successful classification or detection (`ai-brain/osint_agent.py`, `vision/main.py`). List and create both require a bearer token. The table has no `deleted_at` column, and `GET /system-logs` returns every row.

`backend/app/` does not import a logger and does not write login success, login failure, or registration to `system_logs` or anywhere else. Uvicorn is started with no custom log configuration. There is no metrics or alerting service in Compose.

TruffleHog in `.github/workflows/ci.yml` scans git history for verified secrets. That is a CI integrity check, not runtime monitoring of the API.

**Status: Partial.**

**Remaining gap.** No authentication or authorization audit trail. `system_logs` is caller-supplied application text, so any authenticated user can insert a log line. Nothing in the repo alerts on repeated failed logins.

## A10 Server-Side Request Forgery

**Applies to outbound calls.** The API itself does not fetch a URL supplied by the client. The OSINT module does make server-side HTTP requests.

**What the code does.** `backend/app/main.py` talks only to PostgreSQL. It stores `osint_sources.url` and never requests it.

`ai-brain/osint_client.py` uses `requests` against `BASE_URL` (default `http://localhost:8000`) with a 10-second timeout. Paths are fixed: `/auth/login`, `/sources`, `/threat-events`, and `/system-logs`. `ai-brain/osint_agent.py` sends alert text to Groq through `ChatGroq` (`model` `openai/gpt-oss-20b`) when `GROQ_API_KEY` is set. Mock alerts are read from local JSON files in `ai-brain/main.py`, not from the source URL.

`vision/vision_client.py` calls the same style of fixed paths on `BASE_URL`, plus `/camera-states`. `vision/detector.py` can download `yolov8n.pt` through Ultralytics. The browser map in `frontend/heimdall_console.html` loads OpenStreetMap tiles in the client, not on the API server.

`frontend/demo_backend/main.py` is an in-memory mock used by `tests/test_frontend_demo_api.py`. It is not a Compose service and is not the API the OSINT client calls.

**Status: Partial.**

**Remaining gap.** Outbound OSINT traffic goes to the configured API origin and to Groq, with no separate allowlist module. Stored source URLs are not fetched today. A later fetcher would be starting from an unvalidated string field.

## Data privacy

**Password hashing.** Registration writes only the Argon2 hash from `hash_password` into `users.password_hash` (`backend/app/auth.py`, `backend/app/security.py`). Login compares with `verify_password`. API responses use `UserRead`, which omits the hash.

**Soft deletes.** `deleted_at` is a nullable timestamp on these tables in `backend/app/models.py`:

| Table | `deleted_at` | API behavior |
| --- | --- | --- |
| `users` | Yes | Login and `get_current_user` ignore rows where it is set. No route sets it. |
| `osint_sources` | Yes | `DELETE /sources/{source_id}` sets it. Lists and reads skip those rows. |
| `threat_events` | Yes | `DELETE /threat-events/{event_id}` sets it. Lists and reads skip those rows. |
| `alert_logs` | Yes | `DELETE /alert-logs/{alert_id}` sets it. Lists and reads skip those rows. |
| `camera_states` | No | No soft delete. |
| `system_logs` | No | No soft delete. `GET /system-logs` returns all rows. |

The column was added for the domain tables in Alembic revision `0dafecf04f65`, and for `users` in `4d70a0dd39ea`. Soft-deleted domain rows stay in PostgreSQL. Deletes do not remove the primary key, and foreign keys from alerts use `ON DELETE RESTRICT`.

**Where PII is stored.**

| Location | Data |
| --- | --- |
| `users.username` | Account identifier, stored lowercased |
| `users.password_hash` | Argon2 hash, not the password |
| `osint_sources` | Source name, type, and URL |
| `alert_logs.message` | Free-text alert text |
| `system_logs.message` | Free-text module messages. The OSINT agent copies the raw alert into this message (`ai-brain/osint_agent.py`) |
| `threat_events` | Object class, confidence, status, optional source and camera ids. No image bytes |

The schema has no email, phone, or street-address columns. Vision posts class names and scores, not frames (`vision/main.py`). The database volume is the Docker volume `postgres_data`.

## Summary

| Category | Applies | Status | Remaining gap |
| --- | --- | --- | --- |
| A01 Broken Access Control | Yes | Partial | No roles or object ownership. Registration defaults to on. |
| A02 Cryptographic Failures | Yes | Partial | Argon2 and signed, expiring JWTs are in place. Transport is HTTP. Tokens are not revocable. |
| A03 Injection | Yes | Implemented | ORM and Pydantic validation. `url` is only a non-empty string. |
| A04 Insecure Design | Yes | Partial | Single privilege level for every account. OSINT does not gate the camera pipeline. |
| A05 Security Misconfiguration | Yes | Partial | Docs, root containers, and published Postgres. Secrets come from the environment. |
| A06 Vulnerable and Outdated Components | Yes | Partial | Accepted `pip-audit` ignores. Unpinned OSINT deps. Frontend job has no `pip-audit`. |
| A07 Identification and Authentication Failures | Yes | Partial | Hashed passwords and bearer JWTs. No login rate limit or lockout. |
| A08 Software and Data Integrity Failures | Yes | Partial | CI, Alembic, Dependabot, TruffleHog. Unpinned OSINT deps and unsigned YOLO weights. |
| A09 Security Logging and Monitoring Failures | Yes | Partial | No auth audit log. `system_logs` is client-written application data. |
| A10 Server-Side Request Forgery | Yes | Partial | API does not fetch stored URLs. OSINT calls the configured API and Groq. |

## Open items

1. Add an authorization model. Today every active user can call every data route (`backend/app/main.py`).
2. Turn off public registration after service accounts exist (`ENABLE_USER_REGISTRATION` defaults to `true`).
3. Add login rate limiting and lockout. Neither exists under `backend/app/`.
4. Add a way to revoke access tokens before `exp`, or document a short lifetime as the only control. Logout is client-side only.
5. Plan TLS before any host other than localhost. Compose exposes HTTP ports only.
6. Clear the accepted backend audit ignores when the major upgrades land: `PYSEC-2026-1845` (pytest) and `PYSEC-2026-161`, `PYSEC-2026-248`, `PYSEC-2026-249`, `PYSEC-2026-2280`, `PYSEC-2026-2281` (Starlette via FastAPI). See comments in `.github/workflows/ci.yml`.
7. Pin `ai-brain/requirements.txt` and run `pip-audit` on `frontend/requirements.txt` in CI.
8. Record authentication failures and administrative changes in a log the client cannot forge. `system_logs` is not that log.
9. Decide whether `/docs`, `/redoc`, and `/openapi.json` stay public.
10. If OSINT later fetches `osint_sources.url`, validate the URL and allowlist destinations before the first request. The current client does not fetch that column.
