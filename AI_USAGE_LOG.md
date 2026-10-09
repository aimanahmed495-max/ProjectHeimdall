# AI Assistance Log

## 2026-09-07 to 2026-09-11 — Frontend dashboard prototype

**Developer:** Zareer Khan

**Branch:** `feature/2-frontend`
**Related issue:** #2 — Implementation of frontend dashboard prototype
**AI tools:** Claude and ChatGPT
**Updated:** September 8, 2026

This retrospective log groups work by development stage. AI assistance included debugging guidance, and technical explanations. My contribution included selecting the design, directing requirements, applying guided changes, running the application, testing interactions, and publishing the branch.

## Dashboard setup and design integration

**Goal:** Provide a frontend for viewing Heimdall alerts on a map and reviewing them in a triage queue.

**Work completed**
- Selected and supplied a dashboard design.
- Set up the Python environment and installed the prototype dependencies on macOS.
- Ran the Streamlit host and inspected the interface in the browser.
- Used the dashboard to display the Wichita map, alert cards, and system indicators.

**AI involvement:** Claude generated the draft UI design. ChatGPT made integration changes for hosting the interface through Streamlit, plus setup instructions and explanations of the frontend files.

**Outcome:** The dashboard loaded locally using `frontend/app.py`, `frontend/heimdall_console.html`, and `frontend/assets/nocturne.css`.

## API interaction and live updates

**Goal:** Test frontend behavior independently while the team's production backend was being developed.

**Work completed**
- Ran the frontend alongside a mock FastAPI service.
- Exercised simulated alert creation and acknowledgement.
- Supplied screenshots and server logs when interactions failed.
- Clarified that this service was only a frontend testing fixture.

**AI involvement:** ChatGPT generated mock API and frontend integration code for REST requests and WebSocket events.

**Outcome:** The prototype supported these interactions against the mock service. It did not establish integration with the production backend or real threat detection.

## Local troubleshooting

**Goal:** Resolve startup errors and the simulation button's failed requests.

**Work completed**
- Reported a Python import error and followed revised launch instructions.
- Corrected folder paths and resolved a port conflict from an already-running server.
- Supplied logs showing failed `OPTIONS /api/demo/alerts` requests.
- Applied guided corrections and repeated the browser demonstration.

**AI involvement:** ChatGPT interpreted the errors and provided corrective commands and configuration guidance. It identified the failed OPTIONS requests as a cross-origin preflight issue.

**Outcome:** The application ran locally, and later screenshots showed additional simulated alerts. Local CORS troubleshooting did not constitute a production security review.

## Testing and verification

**Goal:** Check the frontend host and mock API behaviors required for the demonstration.

**Work completed**
- Installed testing dependencies and ran `python -m pytest -q`.
- Inspected the test files and reviewed explanations of their assertions.
- Ran the dashboard and manually exercised simulation and acknowledgement.

**AI involvement:** ChatGPT explained its execution, assertions, and coverage limits.

**Recorded local result: five tests passed, with one dependency deprecation warning.**

| Check | What was verified |
| --- | --- |
| Streamlit startup | The host runs without reported Python exceptions |
| HTML integration strings | Expected connection code, event name, demo button ID, and endpoint text are present |
| Mock API health | The endpoint returns HTTP 200 and the expected JSON |
| Alert lifecycle | The mock API creates an alert and changes its status to acknowledged |
| WebSocket delivery | A test client receives a new-alert event with the expected confidence value |

The HTML test checks text rather than executing JavaScript. API and WebSocket tests use a test client, not the browser dashboard. Manual testing complemented these checks; full browser automation and production backend validation were not established by this test run.

## Branch publication and documentation

**Goal:** Make the frontend prototype available for team review on a separate branch.

**Work completed**
- Created issue #2 and used `feature/2-frontend`.
- Staged the frontend files, tests, and test configuration.
- Corrected trailing blank-line warnings from Git's whitespace check.
- Committed the prototype with `feat(frontend): add dashboard prototype`.
- Resolved publishing difficulties through VS Code and confirmed the branch was available on GitHub.

**AI involvement:** ChatGPT guided authentication and workspace troubleshooting.

**Outcome:** The prototype was published on its feature branch. This record does not claim peer approval, a merge into `main`, or successful CI execution.

## Follow-up work

- Agree with the backend developer on endpoint paths, alert fields, status values, and WebSocket event formats.
- Integrate and test the frontend against the production API.
- Add browser interaction tests and review error handling, duplicate events, and safe rendering of incoming data.
- Verify remaining design controls before presenting them as completed features.
- Review this log before committing and append entries for future AI-assisted changes.

## Frontend containerization and repository hygiene

**Goal:** Package the frontend consistently and prevent local environment data from being committed.

**Work completed**
- Added `frontend/Dockerfile` using Python 3.11 and Streamlit on port 8501.
- Added `.dockerignore` to exclude Git metadata, virtual environments, caches, and local environment files.
- Replaced the tracked `.env` with a sanitized `.env.example`.
- Renamed `AI_USAGE.md` to `AI_USAGE_LOG.md` to match the project rubric.
- Built the `heimdall-frontend` Docker image and ran it locally.
- Verified the containerized dashboard against the frontend mock API.
- Ran the automated test suite after the repository changes.

**AI involvement:** ChatGPT provided Dockerfile guidance, explained Docker installation and commands, identified a browser-origin mismatch during container testing, and guided the environment-file cleanup and Git checks.

**Outcome:** The frontend ran successfully from a Docker container, and five automated tests passed with one dependency deprecation warning. Production-backend polling remains pending until the adapter routes and response contract are available.

## Team development entries

This file records how AI tools were used while developing Project Heimdall. All generated suggestions were reviewed, tested, and approved by a team member before being committed.

## 2026-08-23 to 2026-08-27 — Initial backend foundation

**Developer:** Arham Sadid Hossain

**AI assistance used for:**

- Planning the PostgreSQL and Docker Compose setup
- Explaining Git branches, commits, and environment files
- Drafting the SQLAlchemy database models
- Setting up Alembic migrations
- Drafting the initial FastAPI endpoints
- Designing API and threat-level tests
- Debugging syntax, import, schema, and Alembic URL issues
- Drafting backend documentation

**Human verification:**

- PostgreSQL was started and tested locally.
- API endpoints were tested through Swagger UI.
- Alembic upgrade and downgrade were tested.
- Twenty-two automated tests passed.
- Changes were reviewed before being committed to the feature branch.

## 2026-09-08 — Database alignment with final report

**Developer:** Arham Sadid Hossain

**Reason for change:**

The team confirmed that the database should follow the five-table design in the May 2026 final report for Prototype 1.

**AI assistance used for:**

- Comparing the experimental three-table schema with the report
- Drafting updated SQLAlchemy models
- Reviewing an unsafe autogenerated Alembic migration
- Rewriting the migration with a controlled upgrade and downgrade
- Drafting the ERD, normalization notes, and rollback protocol

**Changes made:**

- Replaced the experimental schema with:
  - `osint_sources`
  - `threat_events`
  - `alert_logs`
  - `camera_states`
  - `system_logs`
- Removed the experimental `alert_actions` table.
- Added score-range database constraints.
- Added foreign keys and indexes.
- Added local database-backup instructions.
- Added `backups/` to `.gitignore`.

**Human decisions:**

- Arham approved removing two mock database records.
- The team chose to follow the report's five-table structure.
- PostgreSQL through Docker remains the local database instead of SQLite.
- Cameras, YOLO, real OSINT ingestion, and frontend integration remain outside Prototype 1.

**Verification completed:**

- Created a PostgreSQL backup before the destructive migration.
- Compiled the Python and Alembic files successfully.
- Applied migration `017083aec8b1`.
- Confirmed all five application tables exist.
- Downgraded to migration `226eb47c96bb`.
- Confirmed the old schema returned.
- Reapplied migration `017083aec8b1`.
- Ran `alembic check` with no new operations detected.

## 2026-09-08 — Five-module API skeleton

**Developer:** Arham Sadid Hossain

**Reason for change:**

The team requested a separate API skeleton branch with endpoints that can accept data from Heimdall's different modules.

**AI assistance used for:**

- Updating Pydantic request and response schemas
- Updating FastAPI endpoints for the report's five tables
- Replacing obsolete tests
- Removing the experimental threat-level and alert-action logic
- Updating backend documentation

**Changes made:**

- Created the `feature/2-api-skeleton` branch.
- Updated the API version to `0.2.0`.
- Added POST and GET endpoints for OSINT sources, threat events, alert logs, camera states, and system logs.
- Kept the PostgreSQL health endpoint.
- Removed the obsolete `alert_actions` API.
- Removed the old 0–100 automatic threat-level calculation.
- Added validation for scores, camera IDs, camera modes, FPS values, duplicate sources, and foreign-key references.
- Updated the README for Prototype 1.

**Verification completed:**

- Python files compiled successfully.
- All 18 updated automated tests passed.
- Tests covered all five report modules and important invalid-data cases.

**Prototype limitation:**

These endpoints currently accept manual Swagger requests and automated test data. Real OSINT, physical cameras, YOLO, LangGraph, WebSockets, and frontend integration are not implemented.

## 2026-09-08 — Complete backend Dockerization

**Developer:** Arham Sadid Hossain

**AI assistance used for:**

- Adding configurable PostgreSQL host and port settings
- Creating the FastAPI Dockerfile
- Creating `.dockerignore`
- Adding the API service and PostgreSQL health check to Docker Compose
- Documenting containerized startup commands

**Changes made:**

- Added `backend/Dockerfile`.
- Added a root `.dockerignore`.
- Added the FastAPI `api` service to Docker Compose.
- Configured the API container to connect to the `postgres` service.
- Configured the API to wait for PostgreSQL health.
- Configured Alembic migrations to run before Uvicorn starts.
- Preserved support for running FastAPI locally through `.venv`.

**Verification completed:**

- All 18 API tests still passed after the database connection update.
- The API Docker image built successfully.
- PostgreSQL reported healthy.
- The API container started successfully.
- `GET /health` returned HTTP 200 with the database connected.

## 2026-09-10 — feat: add OSINT ingestion agent with Groq classification (4a77609)

**Developer:** Aiman Ahmed

**Files changed:** ai-brain/.env.example, ai-brain/README.md, ai-brain/main.py, ai-brain/mock_alerts.json, ai-brain/mock_sources.json, ai-brain/osint_agent.py, ai-brain/osint_client.py, ai-brain/requirements.txt

**AI assistance used for:** Drafting the LangGraph OSINT agent (osint_agent.py), the Heimdall API client wrapper (osint_client.py), and the ingestion entrypoint (main.py); generating mock OSINT sources/alerts; and writing the module README.

**Verification:** Ran the full pipeline against the live Heimdall Core API (docker compose up + Alembic migrations applied). Registered 3 mock sources via POST /sources, processed 5 mock alerts through Groq (openai/gpt-oss-20b) classification, and confirmed all 5 threat events were created and retrievable via GET /threat-events.

## 2026-09-10 — feat: add YOLOv8 vision pipeline against Heimdall API (be3783a)

**Developer:** Aiman Ahmed

**Files changed:** vision/.env.example, vision/README.md, vision/detector.py, vision/main.py, vision/requirements.txt, vision/vision_client.py, vision/test_media/*

**AI assistance used for:** Drafting the camera-agnostic FrameSource abstraction and ThreatDetector (detector.py), the Heimdall API client wrapper (vision_client.py), and the pipeline entrypoint (main.py), following the same OOP pattern as the OSINT module.

**Verification:** Ran the full pipeline against the live Heimdall Core API. Processed 3 test images (car, truck, person) through YOLOv8n, confirmed 19 detections posted as threat events and system logs, and verified camera state transitioned Active → Dormant correctly.

## 2026-09-10 — chore: add CI pipeline with lint, tests, and secret scanning

**Developer:** Aiman Ahmed

**Files changed:** .github/workflows/ci.yml, backend/ruff.toml

**AI assistance used for:** Drafting the GitHub Actions workflow (backend lint/test job with a temporary Postgres service, frontend test job, TruffleHog secret scanning job); iteratively debugging CI failures including ruff rule scope, Alembic exclusion, PYTHONPATH resolution, and missing migration step before tests.

**Verification:** Confirmed via live CI runs on PR #8: backend job (lint + 18 tests) passing against a temporary Postgres service; secret-scan job passing. Frontend job intentionally failing pending a separate teammate PR that adds `frontend/requirements.txt` to main.

## 2026-09-10 — feat: add synthetic database seeder

**Developer:** Aiman Ahmed

**Files changed:** backend/app/seed.py, backend/README.md

**AI assistance used for:** Drafting the `DatabaseSeeder` class covering all five tables in dependency order, with idempotency checks to avoid duplicate inserts on repeat runs.

**Verification:** Ran against the live database: inserted 4 sources, 2 camera states, 6 threat events, 3 alert logs, 4 system logs. Confirmed via GET /threat-events that seeded data is retrievable through the real API. Re-ran a second time to confirm no duplicates were created.

## 2026-09-20 — Database Relationship Improvements

**Developer:** Arham Sadid Hossain
**Branch:** `feature/3-database-relationships`

**AI assistance:** Reviewed relational-database concepts and assisted with troubleshooting migration issues.

**Human work completed:** Implemented database relationships, constraints, API validation, migration updates, tests, and documentation.

**Verification:** Migration upgrade and rollback succeeded, all 22 backend tests passed, the database seeder remained idempotent, and the Docker API health check succeeded.

## 2026-09-21 — Camera State Integration

**Developer:** Arham Sadid Hossain

**AI assistance:** Reviewed API integration concepts and assisted with troubleshooting.

**Human work completed:** Implemented camera-state retrieval and updates, connected the vision client, added tests, and updated documentation.

**Verification:** All 30 backend tests passed, repeated vision runs completed successfully, and camera uniqueness was verified in PostgreSQL.

## 2026-09-22 — Authentication Foundation

**Developer:** Arham Sadid Hossain

**AI assistance:** Reviewed authentication concepts and assisted with troubleshooting configuration and testing.

**Human work completed:** Implemented the user model, password hashing, JWT authentication, migration, tests, Docker and CI configuration, and documentation.

**Verification:** Migration upgrade and rollback succeeded, all 38 backend tests passed, backend coverage reached 97.42%, and live testing confirmed that passwords were stored as Argon2 hashes.


## 2026-09-23 — Protected API Integration

**Developer:** Arham Sadid Hossain

**AI assistance:** Reviewed protected-route design, vision-client authentication, registration controls, automated tests, and documentation updates.

**Human work completed:** Protected all write endpoints with JWT bearer authentication, kept read and health endpoints public, connected the vision pipeline to authenticated API requests, added a registration feature flag, expanded API and client tests, and updated backend and vision documentation.

**Verification:** All 48 backend tests passed, backend coverage reached 97.45%, Ruff checks passed, Alembic detected no pending schema changes, Docker Compose configuration validated, and the authenticated vision pipeline completed successfully with camera state transitions and protected event posting.


## 2026-10-02 — Database Normalization and Authenticated OSINT Integration

**Developer:** Arham Sadid Hossain
**Branch:** `feature/7-database-normalization-audit`

**AI assistance:** Reviewed normalization, referential-integrity, deletion-behavior, authenticated service-client, testing, CI, and documentation concepts; assisted with troubleshooting the Alembic migration and OSINT integration.

**Human work completed:** Audited the Prototype 2 schema for third normal form, allowed threat events to originate from OSINT, vision, or both, added a database constraint requiring at least one origin, changed source, camera, and alert relationships to prevent destructive deletion, removed the OSINT pipeline’s fake camera dependency, added source attribution and JWT authentication to OSINT ingestion, added automated OSINT tests and a CI job, and updated backend and OSINT documentation.

**Verification:** Successfully tested Alembic upgrade, downgrade, and schema synchronization; confirmed PostgreSQL foreign-key and check constraints; passed all 50 backend tests with 97.49% coverage and all 5 OSINT tests; passed Ruff, compilation, Docker Compose validation, and whitespace checks; and completed a live authenticated OSINT run that classified and posted 5 source-attributed threat events with linked system logs.

## 2026-09-22 — Frontend Authentication Integration

**Developer:** Zareer Khan
**Branch:** `feature/frontend-auth-ui`

**AI assistance:** ChatGPT/Codex provided guidance for connecting registration, login, and user verification to the backend; assisted with CORS configuration, Docker configuration, troubleshooting.

**Human work completed:** Connected the frontend to the existing `/auth/register`, `/auth/login`, and `/auth/me` endpoints, configured the local environment, and tested account creation and sign-in. Implemented the authentication gate and sign-out flow while preserving the dashboard design. Submitted the changes for team review in PR #23.

**Verification:** Manually verified registration, successful login, invalid-password rejection, sign-out, and signing in again. Ran the existing dashboard and demo API suite: 5 tests passed with 1 dependency deprecation warning. 


## 2026-10-03 — Original Dashboard Integration with the Core Backend

**Developer:** Zareer Khan
**Branch:** `feature/prototype2-real-data`

**AI assistance:** ChatGPT/Codex assisted with reviewing frontend/backend compatibility. Provided guidance for authenticated REST requests, record mapping, polling, session cleanup, connection-status messages, and testing.

**Human work completed:** Applied and tested the integration in VS Code, retained the original dashboard layout, and connected it to sources, threat events, alert logs, camera states, and system logs. Replaced the dashboard's prototype data flow with REST collection loading and periodic refresh. Displayed camera-state information without claiming a live video feed and kept unsupported actions disabled. Submitted the integration for team review in PR #26.

**Verification:** Manually checked authenticated dashboard loading and confirmed that a backend-created threat event appeared in the console. Checked the original dashboard views and record display. Ran the existing dashboard and demo API suite: 5 tests passed. These existing tests did not provide complete automated coverage of the new core-backend integration.


## 2026-10-04 — Frontend Error Handling, Feature Visibility, and Behavior Tests

**Developer:** Zareer Khan
**Branch:** `feature/27-dashboard-actions`

**AI assistance:** ChatGPT/Codex generated a 22-test frontend behavior suite using Node.js and jsdom, tested it against the uploaded console.

**Human work completed:** Applied the error-handling and feature-flag changes in VS Code. Added readable messages for HTTP errors, network failures, and unreadable responses. Hid unsupported acknowledgment, threat-status, and camera-control actions while preserving available detail views and the original dashboard layout. Added the supplied test files to the project, ran them locally through Docker, and saved the work in a local commit.

**Verification:** All 22 frontend behavior tests passed locally using Node.js 22 through Docker. Tests covered authentication, registration, logout, session expiry, record rendering, escaped API text, polling, stale-data handling, network recovery, feature visibility, and prevention of late responses repopulating a signed-out dashboard. The suite used simulated API responses and mocked map functionality. The existing Python suite also passed: 5 tests with 1 dependency deprecation warning. Manually stopped and restarted the API to verify the connection warning and automatic recovery. `git diff --check` reported no whitespace errors.

**Remaining work:** Connect and test alert acknowledgment, threat-status updates, source soft-deletion, and camera-state history when the corresponding backend contracts are available. Feature visibility and simulated-response tests do not establish backend authorization or complete end-to-end integration.


## 2026-10-05 — Backend CRUD, Soft Deletion, and Protected Reads

**Developer:** Arham Sadid Hossain

**Branch:** `feature/28-backend-crud-security`

**AI assistance:** Reviewed soft-deletion design, authenticated read access, PATCH and DELETE endpoint behavior, Alembic migration safety, integration-test coverage, and documentation consistency; assisted with troubleshooting implementation and validation.

**Human work completed:** Added nullable `deleted_at` fields to OSINT sources, threat events, and alert logs; added `corroborated_at` support to threat events; protected resource GET endpoints with JWT authentication; added authenticated record-by-ID, status update, alert acknowledgement, and soft-delete endpoints; prevented deleted records from appearing in normal reads or receiving new references; added an Alembic migration, automated tests, and updated database documentation.

**Verification:** Successfully tested the Alembic upgrade and downgrade, confirmed no pending schema operations, passed all 71 backend tests with 96.91% coverage, and passed Ruff, compilation, and whitespace checks.

## 2026-10-06 — Frontend Alert Acknowledgment Integration

**Developer:** Zareer Khan

**Branch:** `feature/27-dashboard-actions`

**AI assistance:** ChatGPT/Codex generated additional automated tests, explained authenticated PATCH requests, and guided integration and troubleshooting.

**Human work completed:** Applied the changes locally; connected individual alert acknowledgment to PATCH /alert-logs/{alert_id}; rebuilt the frontend container; tested the browser workflow; and ran the expanded automated test suite.

**Verification:** All 30 Node.js/jsdom frontend tests passed using mocked API responses, including eight new tests covering acknowledgment success, HTTP errors, duplicate clicks, logout during requests, multiple alerts, and stale responses. Manual browser testing against the local backend passed, and git diff --check reported no whitespace errors.

## 2026-10-06 — Frontend Threat Status Updates

**Developer:** Zareer Khan

**Branch:** `feature/27-dashboard-actions`

**AI assistance:** ChatGPT/Codex authenticated PATCH integration, and additional frontend tests.

**Human work completed:** Applied the changes locally, rebuilt the frontend, and manually tested marking threats resolved and reopening them as pending while retaining alert acknowledgment state.

**Verification:** All 38 Node.js/jsdom frontend tests passed using mocked API responses, including eight new threat-status tests. Coverage includes status persistence, unchanged acknowledgment state, HTTP errors, duplicate requests, logout during requests, stale responses, and invalid response data. Manual browser testing against the local backend passed. git diff --check reported no whitespace errors.

## 2026-10-06 — Frontend Source Deletion

**Developer:** Zareer Khan

**Branch:** `feature/27-dashboard-actions`

**AI assistance:** ChatGPT/Codex provided guidance on confirmation, error handling, and preventing stale responses from restoring deleted sources.

**Human work completed:** Applied the changes to the existing dashboard and test files, rebuilt the frontend, and manually verified cancellation, successful deletion, persistence after refresh and login, and retention of existing threats and alerts.

**Verification:** All 48 Node.js/jsdom frontend tests passed using mocked API responses. Manual source-deletion checks against the local backend passed. `git diff --check` reported no whitespace errors.

## 2026-10-07 — CI Hardening: Complexity Caps and Dependency Scanning

**Developer:** Aiman Ahmed
**Branch:** `chore/31-ci-hardening` (PR #38)
**Related issue:** Closes #31
**AI tools:** Cursor (agent mode) for implementation; Claude for planning and review

### Exact prompt submitted (Cursor):
> Update the CI pipeline in .github/workflows/ci.yml and add supporting config. Keep every existing job working.
>
> Do NOT modify the existing frontend job. Add any new job at the end of the file, after secret-scan.
>
> 1. In pyproject.toml, add:
>    [tool.ruff.lint] select = ["E","F","I","C901"]
>    [tool.ruff.lint.mccabe] max-complexity = 10
> 2. In the osint job, remove the --select E,F,I flag so it uses the shared config.
> 3. Lint backend/, ai-brain/, and vision/ with the shared config.
> 4. Add a complexipy step that fails on cognitive complexity above 15 for backend, ai-brain, and vision.
> 5. Add a vision job: Python 3.11, install vision/requirements.txt, run pytest vision/tests. Skip with a clear message if vision/tests does not exist yet.
> 6. Add a pip-audit step to the backend, osint, and vision jobs, run against each job's requirements file, failing on any known CVE.
> 7. Create .github/dependabot.yml with weekly updates for pip (each requirements directory), github-actions, and docker.
> 8. Do not change any application code yet. Run `ruff check .` and list every C901 violation so I can fix them separately.

### Follow-up responses to Cursor's questions:
> Import-order rule failures: "Run ruff --fix on the imports only, no logic changes."
>
> pip-audit CVE failures: "Bump only the vulnerable packages, to the minimum fixed version each. Don't touch other pins. Run the backend tests after. For vision, check that the module still imports. If a fix needs a major version jump or breaks tests, revert that bump and instead add --ignore-vuln <ID> to pip-audit with a comment explaining why, and tell me which ones."

### AI output summary:
Added ruff C901 (max 10) to the shared config, complexipy checks, pip-audit steps, a vision CI job, and Dependabot config. Fixed import order with `ruff --fix` and bumped vulnerable packages, adding `--ignore-vuln` entries for six backend advisories that need major upgrades.

### Human review, refactoring and modifications made:
* Found that `backend/ruff.toml` overrode the shared config, and had it extend `pyproject.toml`.
* Found that `backend/Dockerfile` used Python 3.9, which cannot install the bumped `requests` and `python-dotenv`; changed it to 3.11.
* Chose to ignore major-upgrade advisories instead of upgrading FastAPI and pytest the week of the prototype.
* Kept the frontend job untouched to avoid conflicting with a teammate's open PR.

### Verification and testing method:
* `ruff check` and complexipy passed.
* `docker compose build` and `up` succeeded on Python 3.11 with a fresh database; `/health` returned `{"status":"ok","database":"connected"}`.
* CI passed on PR #38.

---

## 2026-10-08 — OWASP Audit and Documentation Package

**Developer:** Aiman Ahmed
**Branch:** `docs/35-owasp-readme-uml` (PR #49)
**Related issue:** Closes #35
**AI tools:** Cursor (agent mode) for drafting; Claude for planning and review

### Exact prompt submitted (Cursor):
> Documentation only. Do not change any application code, tests, CI, or requirements. Do not edit AI_USAGE_LOG.md.
>
> First read the code so every claim is verified: backend/app/ (main.py, auth.py, security.py, models.py, schemas.py, database.py), backend/alembic/versions/, docker-compose.yml, .env.example files, ai-brain/, vision/, frontend/, .github/workflows/ci.yml, .github/dependabot.yml, and the existing README.md. Never state something the code does not do. Cite file paths in the audit.
>
> 1. docs/OWASP_AUDIT.md: audit against the OWASP Top 10 (2021), one section per category A01-A10. For each: whether it applies to Heimdall, what the code does about it (with file references), a status of Implemented / Partial / Open / Not applicable, and any remaining gap. Specifically verify and report on:
>    - A01: which endpoints require authentication (read main.py), role checks, and CORS.
>    - A02: JWT signing and expiry, Argon2 password hashing (pwdlib), secrets read from environment.
>    - A03: input validation (Pydantic schemas) and SQL injection (SQLAlchemy ORM).
>    - A04/A05: configuration defaults, .env.example hygiene, debug settings, Docker setup.
>    - A06: dependency scanning (pip-audit in CI, Dependabot), and these accepted backend vulnerabilities ignored in ci.yml because the fixes need major upgrades: PYSEC-2026-1845 (pytest 9, dev only) and PYSEC-2026-161, -248, -249, -2280, -2281 (starlette 1.x via fastapi). Mark A06 as Partial.
>    - A07: authentication flow, token handling, any login rate limiting or lockout (report honestly if absent).
>    - A08/A09: logging, audit logs table, CI integrity (secret scanning with TruffleHog).
>    - A10: any server-side outbound requests (the OSINT module).
>    Also add a Data Privacy section: password hashing, soft deletes via deleted_at (list which tables have it), and where PII is stored. End with a summary table and a list of open items.
>
> 2. README.md: update the existing file. Keep what is accurate. Add or fix: project overview, architecture overview, features implemented in this prototype, tech stack, quick start with `docker compose down -v` then `docker compose up`, environment variables (names only, no secrets), how to run tests and linting, CI checks (ruff C901, complexipy, pip-audit, TruffleHog), the branching and commit conventions (feature/*, chore/*, docs/*, Conventional Commits, PRs link an Issue), and a link to docs/. Do not document feature flags or adapters that do not exist in the code yet.
>
> 3. docs/ARCHITECTURE.md: a Mermaid component diagram (flowchart) of the layers as actually implemented: OSINT module (ai-brain), backend API (FastAPI), PostgreSQL, vision module, frontend, and the data flows between them. Add a Mermaid ER diagram of the database tables from models.py, and a Mermaid sequence diagram of the login flow (JWT). Short prose under each diagram.
>
> 4. docs/DEVELOPER_SETUP.md: step-by-step setup for a new developer on macOS or Linux: prerequisites (Docker, Python 3.11 or newer), clone, .env setup, docker compose up, seeding data, health check (curl localhost:8000/health), running each module's tests, linting, and troubleshooting. Include this known issue: if the API exits on startup with a ForeignKeyViolation on threat_events, run `docker compose down -v` to reset the local database volume.
>
> When finished, list the files you created or changed and any claim you could not verify from the code.

### AI output summary:
Drafted `docs/OWASP_AUDIT.md`, an updated `README.md`, `docs/ARCHITECTURE.md` (Mermaid component, ER, and login sequence diagrams), and `docs/DEVELOPER_SETUP.md`.

### Human review, refactoring and modifications made:
* Read the audit against the code and kept its Partial statuses and open items instead of overstating controls.
* Reviewed the generated files before committing; no application code was changed.

### Verification and testing method:
* Spot-checked audit claims with `grep` (no `role` column in `models.py`; `ENABLE_USER_REGISTRATION` defaults to true in `docker-compose.yml` and `auth.py`) and by listing `backend/alembic/versions` to confirm migration `0dafecf04f65` exists.
* Passed peer review and CI on PR #49.

---

## 2026-10-08 — Live OSINT Adapters and Corroboration

**Developer:** Aiman Ahmed
**Branch:** `feature/32-osint-adapters` (PR #50)
**Related issues:** Closes #32, Closes #33
**AI tools:** Cursor (agent mode) for implementation; Claude for planning and review

### Exact prompt submitted (Cursor):
> Work in ai-brain/ only. Do not modify backend/, frontend/, vision/, docs/, or .github/.
>
> First read: ai-brain/main.py, osint_agent.py, osint_client.py, mock_alerts.json, mock_sources.json, requirements.txt, .env.example, ai-brain/tests/, plus backend/app/schemas.py and backend/app/main.py (read-only) to learn the exact request fields and allowed values for sources, threat events, PATCH /threat-events/{id} (including the corroboration field and status values) and PUT /camera-states/{camera_id}. Match the existing code style. The existing mock behavior must keep working unchanged.
>
> Implement GitHub Issues #32 and #33 (trimmed scope):
>
> 1. SourceAdapter: abstract base class (docstrings, type hints) that yields SourceItem(source_name, text, timestamp, external_id) and skips external_ids it has already returned.
>
> 2. NtfyAdapter: poll https://<NTFY_SERVER>/<NTFY_TOPIC>/json?poll=1&since=<last id or 10m> with requests (no streaming, no new dependency). Parse one JSON object per line and keep only event == "message". external_id = the message id. Source name "ntfy-tipline".
>
> 3. RssAdapter: fetch RSS_FEED_URL (default http://localhost:8001/feed.xml) with requests and parse it with the standard library xml.etree.ElementTree (no feedparser). external_id = item guid. Source name "local-rss-feed".
>
> 4. ai-brain/demo_feed.py: a demo RSS server using ONLY the standard library (http.server). GET /feed.xml returns RSS 2.0 with the items posted so far; GET / returns a simple HTML page with a text box and Submit button; POST /items adds an item to an in-memory list. Port 8001 (DEMO_FEED_PORT). Runnable with `python ai-brain/demo_feed.py`. No FastAPI.
>
> 5. KeywordFilter: case-insensitive match against OSINT_KEYWORDS (comma-separated, with defaults such as shots, gun, weapon, armed, fire, explosion, suspicious, fight, robbery, threat). Items without a match are logged and dropped before any LLM call.
>
> 6. CorroborationTracker: a pure, testable class. Keep recent reports keyed by the agent's classified threat category (use whatever category field the agent already returns). An event is corroborated when 2 or more DISTINCT source_ids report the same category within CORROBORATION_WINDOW_SECONDS (default 300). Two reports from the same source never count. Fire once per corroborated group: do not re-activate on every new report.
>
> 7. On corroboration, via the existing client: PATCH the threat event(s) to the corroborated status and set the corroboration field (use the exact field names from the backend schemas), then PUT /camera-states/<CAMERA_ID> to Active (CAMERA_ID default 1), then POST a system log entry for the activation. A single report must leave the camera unchanged.
>
> 8. Source registration: register both sources through the existing client at startup. Fetch existing sources first so reruns do not fail with 409, and map each adapter to its source_id.
>
> 9. Feature flag FEATURE_LIVE_OSINT (default false). Off: existing mock behavior, unchanged. On: loop every OSINT_POLL_SECONDS (default 5): poll adapters, filter, run the existing agent on each item with its source_id, feed the result to the tracker. Add to ai-brain/.env.example (placeholders only): FEATURE_LIVE_OSINT, NTFY_SERVER=https://ntfy.sh, NTFY_TOPIC=heimdall-demo-change-me, RSS_FEED_URL, OSINT_POLL_SECONDS, OSINT_KEYWORDS, CORROBORATION_WINDOW_SECONDS, CAMERA_ID.
>
> 10. No new dependencies. Do not edit requirements.txt unless unavoidable; if it is, tell me why.
>
> 11. Tests in ai-brain/tests with ALL network calls and the LLM mocked. Never construct a real ChatGroq (CI has no GROQ_API_KEY); inject a fake agent. Cover: ntfy parsing (message vs open/keepalive lines) and dedup, RSS parsing, keyword match / no match / case-insensitive, corroboration (one source stays pending; two distinct sources corroborate; same source twice does not; reports outside the window do not; fires only once), the activation calls (PATCH then PUT happen once), flag off uses the mock path, flag on uses the adapters, and source registration is idempotent.
>
> 12. Quality: object-oriented, docstrings, type hints. Every function under cyclomatic complexity 10 (ruff C901) and cognitive complexity 15 (complexipy), so split logic into small methods. Public, unauthenticated sources only. No secrets in code.
>
> When finished, run and report the full output of:
> ruff check ai-brain
> complexipy ai-brain --max-complexity-allowed 15
> pytest ai-brain/tests -q

### AI output summary:
Added ntfy and RSS source adapters behind a `SourceAdapter` base class, a standard-library demo feed server, a keyword filter, a corroboration tracker (2+ distinct sources within a time window), a camera activator, idempotent source registration, and the `FEATURE_LIVE_OSINT` flag.

### Human review, refactoring and modifications made:
* Cut Bluesky and any new dependencies from the scope so the CI dependency audit would not fail on new advisories.
* Confirmed that only `ai-brain/` changed and that `requirements.txt` was untouched.

### Verification and testing method:
* `ruff check ai-brain` passed.
* `complexipy ai-brain --max-complexity-allowed 15` passed with all functions under the limit (highest score 12, in existing code).
* `pytest ai-brain/tests -q`: 29 passed, with all network and LLM calls mocked.
* CI passed on PR #50.

---

## Audit Certification

I certify as Team Lead that all entries above accurately represent AI usage within this project phase, all prompts have been recorded, and all code has been validated by human review and automated testing.

**Team Lead Signature:** *Aiman Ahmed* — **Date:** October 8, 2026