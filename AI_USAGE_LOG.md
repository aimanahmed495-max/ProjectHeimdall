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

---

## 2026-11-02 — Prototype 3 Frontend Browser E2E Testing

**Developer:** Zareer Sanjeed Khan
**Branch:** `test/prototype3-frontend-e2e`
**Related issues:** Prototype 3 frontend testing
**AI tools:** Codex for planning, troubleshooting, and review


### Assistance:

* Suggested an isolated Git branch and Playwright test structure.
* Provided the Playwright configuration and browser E2E test.
* Guided installation of Node.js, Playwright, and Chromium.
* Provided Docker, database-seeding, health-check, and regression-test commands.
* Helped diagnose the initial Streamlit iframe locator timeout.

### Human review, refactoring, and modifications made:

* Created and reviewed the Playwright configuration and E2E test files.
* Confirmed that generated dependencies and test artifacts are excluded from Git.
* Built and seeded the application using Docker Compose.
* Ran the test manually and reviewed the initial failure output.
* Replaced the unsuccessful title-based iframe selector with a selector that waits for and uses the first attached Streamlit iframe.
* Reran the browser test after the correction and confirmed that it passed.

### Verification and testing method:

* Playwright registration, login, record-loading, and logout workflow: **1 passed**.
* The initial Playwright attempt failed because of the iframe locator; the corrected version passed.
* Existing Node.js/jsdom frontend regression suite: **48 passed**.
* Python dashboard and frontend API tests: **5 passed, 1 dependency deprecation warning**.
* API health check returned a healthy database connection.
* Streamlit health check returned `ok`.
* `git diff --check` reported no whitespace errors.


---

## 2026-11-02 — Prototype 3 Frontend E2E CI Integration

**Developer:** Zareer Sanjeed Khan
**Branch:** `ci/prototype3-frontend-e2e`
**Related issues:** Prototype 3 frontend testing and CI integration
**AI tools:** Codex for workflow planning, YAML generation, and validation guidance


### Assistance:

* Configured Node.js 22 and installed the isolated dependencies from `tests/e2e`.
* Installed Playwright Chromium and its required system dependencies.
* Started the Heimdall application with Docker Compose.
* Added API and Streamlit health-check waits before executing the browser test.
* Seeded the test database before running Playwright.
* Added failure-only uploads for Playwright screenshots, traces, and reports.
* Added service-log collection on failure and unconditional Docker cleanup.

### Human review, refactoring, and modifications made:

* Reviewed the existing workflow before making changes.
* Kept the new browser test in a separate job without modifying the existing backend, frontend, OSINT, secret-scan, or vision jobs.
* Reviewed the Docker service name, health-check URLs, seed command, test directory, and artifact paths.
* Confirmed the workflow uses the previously tested Playwright E2E configuration.

### Verification and testing method:

* `git diff --check` reported no whitespace errors.
* Ruby successfully parsed the workflow: `YAML syntax valid`.
* `docker compose config --quiet` completed successfully: `Docker Compose config valid`.
* The Playwright workflow had previously passed locally after correcting the initial iframe locator failure.

## 2026-11-05 — Prototype 3 agent-assisted work (Cursor)

Entries for the Cursor agent tasks in `docs/agent/TASKS.md` and two frontend changes by Zareer. Prompts, outputs and verification are reconstructed from the agent sessions.

### 23:59 T02 OSINT pipeline E2E, matching sources
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#61`
- **Branch:** `agent/T02`
- **Prompt submitted:** "Take task T02 from docs/agent/TASKS.md. Link issue #61."
- **AI output summary:** Added `tests/e2e_pipeline/` (marker `e2e`). A session fixture runs `alembic upgrade head`, starts the real API with uvicorn on a free localhost port against the test Postgres, and always stops it. The test registers the OSINT user and camera 1 (reset to Dormant), runs `LiveOsintRunner` with two `StaticAdapter` sources and a scripted classifier that returns `person` and posts real threat events, `max_cycles=1`, then checks over HTTP that camera 1 is Active and both events are Corroborated with distinct source ids. `pyproject.toml` registers the marker and deselects it by default (`-m 'not e2e'`), so `pytest tests/` in the frontend CI job is unchanged. No new dependency, no `ci.yml` change.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** `POSTGRES_PORT=5433 .venv/osint/bin/pytest -m e2e tests/e2e_pipeline`: 1 passed, run four times in a row against the same database. A temporary copy with a keyword filter that matches nothing failed on `'Dormant' == 'Active'`; the copy was deleted. No uvicorn process left after passing and failing runs. `.venv/frontend/bin/pytest tests/ -q`: 5 passed, 1 deselected. `ruff check` and `ruff format --check` on `tests/e2e_pipeline`: clean. `bash scripts/check`: OK, run from a temporary copy that only changes `POSTGRES_PORT` to 5433, against a throwaway local Postgres 16 cluster.

### 23:59 T06 OSINT structured logging
- **Date:** 2026-11-04 (work finished after midnight, 2026-11-05)
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#64`
- **Branch:** `agent/T06`
- **Prompt submitted:** "Take task T06 from docs/agent/TASKS.md. Link issue #64."
- **AI output summary:** Added `ai-brain/osint_logging.py` (JSON formatter, `log_context`, `log_event`, `configure_logging`). The live loop now logs classify, corroborate, keyword-drop, and error events as JSON lines with `timestamp`, `level`, `request_id`, and `user_id` instead of printing them. `user_id` comes from a new `HeimdallAPIClient.current_user_id()` that calls `GET /auth/me`. The banner prints in `main.py` and `live_osint.py` are unchanged. Added 14 tests in `ai-brain/tests/test_osint_logging.py` and noted the logs and the `/auth/me` call in `docs/OWASP_AUDIT.md` (A09, A10). Partway through, another agent switched the shared checkout to `agent/T17` and the three commits landed there; they were moved to `agent/T06`, `agent/T17` was reset to `main`, and work continued in `.worktrees/T06`.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something. Aiman's T06 work was moved onto the wrong branch by the agent's branch switch in the shared checkout and was cleaned up by hand.
- **Verification:** In a checkout without `.env`: `pytest ai-brain/tests` 43 passed; `pytest ai-brain/tests/test_osint_logging.py` 14 passed on three consecutive runs; `ruff check backend/ ai-brain/ vision/` passed; `complexipy` passed for `backend`, `ai-brain`, and `vision`. `bash scripts/check` was not run locally: one `.venv` only, and Postgres was not running. Backend and frontend tests were not run locally; this change does not touch either.

### 00:00 T09 OSINT pipeline doc
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#66`
- **Branch:** `agent/T09`
- **Prompt submitted:** "Take task T09 from docs/agent/TASKS.md. Link issue #66."
- **AI output summary:** Wrote `docs/OSINT_PIPELINE.md` from the code in `ai-brain/` on `main`: live and mock data flow with a Mermaid diagram, the ntfy and RSS adapters, an environment variable table matching `ai-brain/.env.example`, and failure behavior at startup and inside the live loop. It notes that `DEMO_FEED_PORT` is read by `demo_feed.py` but missing from `.env.example`, and lists the failure cases that have no test yet.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** A script compared the env table with `ai-brain/.env.example` (same 12 names, order, and values: match). Backend source checked for the 404 on `PUT /camera-states/{camera_id}`. `bash scripts/check` in a clean worktree at the doc commit: ruff, complexipy, `ai-brain` tests, and frontend tests passed; alembic and backend tests failed because the local Postgres rejects the `test` user (environment, not this change).

### 00:00 T14 demo reset and preflight script
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#70`
- **Branch:** `agent/T14`
- **Prompt submitted:** "Take task T14 from docs/agent/TASKS.md. Link issue #70."
- **AI output summary:** Added `scripts/demo_reset.sh`, which checks `GET /health`, logs in with `OSINT_API_USERNAME`/`OSINT_API_PASSWORD` from the environment, reads camera `CAMERA_ID` (default 1), PUTs it back to `Dormant` with its current fps and resolution, and prints the RSS feed, live OSINT loop, ntfy, and demo-feed commands. Documented it in `ai-brain/README.md`. Credentials and the token are passed to `curl` through stdin and file descriptors, never as arguments or output.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** `shellcheck` 0.11.0 (throwaway venv, not a project dependency) on `scripts/demo_reset.sh`: no findings. Ran the script against a throwaway local fake API with synthetic credentials: happy path set camera 1 from Active 15 fps 1080p to Dormant 15 fps 1080p; wrong password, missing credentials, missing camera, invalid `CAMERA_ID`, and unreachable API each exited 1 with a clear message. Credentials and token appeared in neither the output nor the logged `curl` argument lists. `ruff`, `complexipy`, `pytest ai-brain/tests -q` (29 passed), `pytest tests/ -q` (5 passed). `bash scripts/check`: the Alembic and backend test steps failed locally because Postgres on port 5432 has no `test` role; not caused by this change; left to CI. Not run against the real API or Postgres.

### 00:00 T17 login rate limiting plan
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#72`
- **Branch:** `agent/T17`
- **Prompt submitted:** "Take task T17 from docs/agent/TASKS.md. Link issue #72."
- **AI output summary:** The agent first checked the task's precondition ("confirm no teammate owns auth") and found that Arham owns backend auth (#21, PR #22, and the commit history of `auth.py`), so it stopped and asked. After Aiman chose "write the plan as a proposal for Arham", it wrote `docs/agent/plans/T17.md`. The plan proposes an in-memory failure counter in a new `backend/app/rate_limit.py`, keyed per (IP, username) with a looser per-IP cap, that returns 429 with `Retry-After`. It needs no new dependency and no migration, changes about 10 lines of `auth.py`, and lists tests, docs, and four open questions for Arham. No code was written.
- **Human review and modifications:** Aiman chose to have the plan written as a proposal for Arham rather than as agent-owned work. During the session, the agent's branch switch in the shared checkout collided with the parallel T06 agent, whose commits landed on `agent/T17`. The agent stopped and reported it; the T06 commits were moved to `agent/T06` and T17 continued in its own worktree. Review of the plan itself: Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** `bash scripts/check` in the `agent/T17` worktree: ruff, complexipy, `ai-brain` tests, and frontend tests passed. `alembic upgrade head` and the backend tests failed because the local Postgres rejects the `test` user (environment; the change is docs-only). Ownership was checked with `gh issue view 21`, `gh pr list --author sadidarham`, and `git log -- backend/app/auth.py`.

### 00:01 T15 Bluesky adapter plan
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#71`
- **Branch:** `agent/T15`
- **Prompt submitted:** "Take task T15 from docs/agent/TASKS.md. Plan only, do not build. Link issue #71."
- **AI output summary:** Wrote `docs/agent/plans/T15.md`. The plan checks Bluesky's API and auth rules against the official docs and public issue reports, and finds that unauthenticated `searchPosts` returns 403 intermittently while `getAuthorFeed` is documented as no-auth. It recommends a `getAuthorFeed` watchlist adapter behind `FEATURE_BLUESKY` with no new dependency, one source id for every Bluesky account, and `indexedAt` timestamps. It also lists files, env variables, 11 fixture tests, OWASP updates, and four open questions. No code was written. The build is blocked on T01.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something. Aiman approved the plan before the build.
- **Verification:** No live request was sent to Bluesky (a manual `curl` check is listed in the plan). `bash scripts/check` in the `agent/T15` worktree: ruff, complexipy, `ai-brain` tests, and frontend tests passed. `alembic upgrade head` and the backend tests failed because the local Postgres rejects the `test` user (environment, not this change).

### 00:01 T16 plan: vision trigger-driven activation
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#34`
- **Branch:** `agent/T16`
- **Prompt submitted:** "Take task T16 from docs/agent/TASKS.md. Plan only, do not build. Link issue #34."
- **AI output summary:** Wrote `docs/agent/plans/T16.md`. Vision becomes read-only on camera state: it polls `GET /camera-states/{id}` and captures only while OSINT's `CameraActivator` has the camera Active. The plan covers webcam and video-file frame sources, `FEATURE_PI_CAMERA` (placeholder until T18), a per-class post cooldown, re-login on 401, the tests, the doc and OWASP updates, and four open questions. No code under `vision/` changed.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something. Aiman approved the plan before the build.
- **Verification:** `bash scripts/check` ran on `agent/T16`. Ruff, complexipy, the OSINT tests, and the frontend tests passed. `alembic upgrade head` and the backend tests failed because the local Postgres on port 5432 rejected the CI test credentials (`test`/`test`). That is an environment issue; this branch changes only Markdown files.

### 00:03 T01 shared object classes
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#60`
- **Branch:** `cursor/t01-shared-object-classes-979e`
- **Prompt submitted:** Take task T01 from `docs/agent/TASKS.md`. Link issue #60.
- **AI output summary:** Added `ai-brain/object_classes.py` to map classifier labels onto person, vehicle, crowd, package, or unknown; wired it into `ThreatClassification` and `CorroborationTracker`; tightened the allowed-class list in the system prompt; added mapping and synonym-corroboration tests; marked T01 done in the task queue.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something. Stale test assertions broken by the T01/T06 merge were fixed in #83.
- **Verification:** `bash scripts/check` printed `OK`. `pytest ai-brain/tests/test_object_classes.py ai-brain/tests/test_corroboration.py -v` — 40 passed.

### 18:04 T04 CI step for the pipeline E2E (plan)
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#63`
- **Branch:** `cursor/t04-ci-pipeline-e2e-7956`
- **Prompt submitted:** "Take task T04 from docs/agent/TASKS.md. Link issue #63."
- **AI output summary:** Wrote `docs/agent/plans/T04.md`. Recommends a new `e2e-pipeline` GitHub Actions job with a Postgres 17 service (same credentials as the backend job) running `pytest -m e2e tests/e2e_pipeline -q`, with the exact YAML and a rejection of adding a step to the existing Playwright/Compose `e2e` job because of shared-database contamination. No `ci.yml` edit in this PR.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something. `ci.yml` cannot be written by the tools, so Aiman applied the workflow edits by hand (Ubuntu 24.04, Playwright install without `--with-deps`, timeouts).
- **Verification:** `bash scripts/check` failed on this branch and on a stash that restored `main` content: `ai-brain/tests/test_osint_logging.py::test_corroborate_event_has_required_fields` asserts corroboration category `weapon` but the logger records `unknown` after T01 class normalization. Unrelated to this docs-only plan; no second attempt to "fix" that failure on this branch.
### 18:06 T03 pipeline E2E, negative and failure cases
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#62`
- **Branch:** `cursor/t03-pipeline-e2e-negative-f6ee`
- **Prompt submitted:** "Take task T03 from docs/agent/TASKS.md. Link issue #62."
- **AI output summary:** Extended `tests/e2e_pipeline/test_osint_pipeline.py` with four cases on the T02 harness: different classes leave camera 1 Dormant; reports outside the corroboration window stay Pending; a source `ConnectionError` does not stop the runner or the healthy source; the same source reporting twice never corroborates. Shared helpers (`build_runner`, `ScriptedClassifier` queue, `FailingAdapter`) keep the suite DRY. Marked T02 and T03 done in `docs/agent/TASKS.md`. Also fixed two pre-existing assertions in `ai-brain/tests/test_osint_logging.py` that still expected corroboration category `weapon` after T01 normalization maps it to `unknown`.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** `.venv/osint/bin/pytest -m e2e tests/e2e_pipeline`: 5 passed on five consecutive runs; no leftover uvicorn. `bash scripts/check`: OK.


### 18:30 Frontend threat-status filter correction

- **Date:** 2026-11-05
- **Team member:** Zareer Sanjeed Khan
- **Tool used:** Codex
- **Associated Git issue:** #85
- **Branch:** `fix/frontend-history-filters`

- **Assistance:** Suggested replacing legacy history-filter statuses with Pending, Corroborated, and Resolved; adding Corroborated to the rule filter; adding an accessible history-filter label; and adding two regression tests. Also suggested ignoring generated frontend-console dependencies.

- **Human review and modifications:** Zareer manually applied the changes in VS Code, inspected the diff, and ran the JavaScript and Python frontend tests. Peer review is pending.

- **Verification:** `npm test --prefix tests/frontend-console`: 50 passed, including both new regression tests. `python -m pytest tests/test_dashboard.py tests/test_frontend_demo_api.py -q`: 5 passed, 1 dependency deprecation warning. `git diff --check`: no whitespace errors. Playwright and the full CI suite have not been rerun for this fix.
### 18:30 T01 follow-up: never corroborate on unknown
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#60`
- **Branch:** `agent/T01-unknown-fix`
- **Prompt submitted:** Follow-up to T01 (issue #60). Make `CorroborationTracker` never corroborate on `unknown`; add tests for two unknowns and different unmapped labels; change `ScriptedAgent` to emit `person` and update logging/e2e assertions; branch `agent/T01-unknown-fix`, one PR, link #60.
- **AI output summary:** `CorroborationTracker.observe` returns early when the normalized class is `unknown`. Added unit tests for two explicit unknowns and for different unmapped labels (`weapon`/`drone`). `ScriptedAgent` now emits `person`; logging and live-osint activation assertions expect `person`. Noted the unknown rule in `docs/OSINT_PIPELINE.md`. `tests/e2e_pipeline/` already used `person`, so no edit there.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something. Aiman had the unknown-never-corroborates rule added after review (#84).
- **Verification:** `bash scripts/check` printed `OK`. `.venv/osint/bin/pytest ai-brain/tests/test_corroboration.py ai-brain/tests/test_osint_logging.py ai-brain/tests/test_live_osint.py -q`: 38 passed.

### 18:59 T09 OSINT pipeline doc refresh
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#66`
- **Branch:** `cursor/t09-osint-pipeline-doc-f6be`
- **Prompt submitted:** Refresh `docs/OSINT_PIPELINE.md` to match main now that T01, T06 and the unknown fix are merged (shared classes, JSON logging on stderr, unknown never corroborates). Docs only. Link issue #66.
- **AI output summary:** Updated the pipeline doc with shared object-class normalization, JSON-line logging events (`keyword_drop`, `classify`, `corroborate`, `error`), the unknown-never-corroborates rule, and refreshed failure/test-coverage notes. Marked T06 and T09 done in `docs/agent/TASKS.md`.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** Env table script matched all 12 names/order/example values in `ai-brain/.env.example`. `bash scripts/check` printed `OK`.
### 18:59 T08 OWASP audit refresh for live OSINT
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#65`
- **Branch:** `cursor/t08-owasp-audit-refresh-7551`
- **Prompt submitted:** "Take task T08 from docs/agent/TASKS.md. Link issue #65."
- **AI output summary:** Docs-only refresh of `docs/OWASP_AUDIT.md` for A04, A07, A09, A10, the Summary table, and Open items. Documented that live corroboration (`CorroborationTracker` / `CameraActivator`, behind `FEATURE_LIVE_OSINT`) gates camera Active, that ntfy and RSS adapters GET env-configured URLs (not the stored `osint_sources.url` column), and that login rate limiting remains plan-only (`docs/agent/plans/T17.md`). Marked T08 done in `docs/agent/TASKS.md`.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** Spot-checked claims against `ai-brain/corroboration.py`, `camera_activation.py`, `ntfy_adapter.py`, `rss_adapter.py`, `live_osint.py`, `main.py`, `osint_client.py`, and `osint_logging.py`. Confirmed stale phrases about OSINT never changing camera mode / never fetching feeds are gone. `bash scripts/check` printed `OK`.
### 18:57 T12 OSINT QA log draft
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#68`
- **Branch:** `cursor/t12-osint-qa-log-bc7d`
- **Prompt submitted:** "Take task T12 from docs/agent/TASKS.md. Link issue #68."
- **AI output summary:** Added `docs/qa/osint-qa-log.md` with one row per existing OSINT unit or E2E test that was run in this session (test path, edge case, severity, result, resolution, linked issue). Marked T12 done in `docs/agent/TASKS.md`. No production code changes.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** `.venv/osint/bin/pytest ai-brain/tests -q`: 78 passed. `.venv/osint/bin/pytest -m e2e tests/e2e_pipeline -v`: 5 passed. `bash scripts/check`: OK.
### 19:00 T11 docstring pass, OSINT module
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#67`
- **Branch:** `cursor/t11-osint-docstrings-3cbe`
- **Prompt submitted:** "Take task T11 from docs/agent/TASKS.md. Link issue #67."
- **AI output summary:** Filled Google-style `Args` / `Returns` / `Raises` / `Yields` / `Attributes` sections on every public class and method under `ai-brain/` (adapters, client, agent, live loop, logging, settings, demo feed, and related helpers). No executable code changed.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** AST dump with docstrings stripped matched `HEAD` for all 14 touched files (behavior-changing files: none). `bash scripts/check` printed `OK`.
### 18:58 T13 OSINT README refresh
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#69`
- **Branch:** `cursor/t13-osint-readme-refresh-8d49`
- **Prompt submitted:** "Take task T13 from docs/agent/TASKS.md. Link issue #69."
- **AI output summary:** Refreshed `ai-brain/README.md` and the OSINT statements in root `README.md`: removed the stale claim that OSINT does not switch the camera; documented `FEATURE_LIVE_OSINT`, shared object classes (including that `unknown` never corroborates), the `tests/e2e_pipeline` E2E suite, and demo steps plus `scripts/demo_reset.sh`. Env block matches `ai-brain/.env.example`. Marked T13 done in `docs/agent/TASKS.md`.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** Compared the README env block to `ai-brain/.env.example` (exact match). Confirmed root README no longer contains "does not switch". `bash scripts/check` printed `OK`.

### 19:42 T16 build: vision trigger-driven activation
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#34`
- **Branch:** `agent/T16-build`
- **Prompt submitted:** Build T16 from `docs/agent/plans/T16.md` (issue #34). Plan approved; include optional E2E now that T02 is merged. Decisions: PiCameraSource placeholder until T18; keep raw COCO names; do not add auto-return to Dormant. Branch `agent/T16-build`, one PR, Closes #34.
- **AI output summary:** Replaced the run-once still-image pipeline with `VisionRunner` that polls camera state and captures only while Active. Added frame sources (webcam/video/static + Pi placeholder), settings, per-class throttle, read-only `get_camera_state` with 401 re-login, unit tests, optional E2E after OSINT corroboration, `scripts/check` vision step, and docs/OWASP updates.
- **Human review and modifications:** Decisions from the prompt were applied as given (placeholder Pi source, raw COCO names, no auto-Dormant). Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** `.venv/osint/bin/pytest vision/tests -q`: 23 passed. `PYTHONPATH=. .venv/backend/bin/pytest vision/tests backend/tests/test_vision_client.py --cov=vision`: 30 passed, 86% total coverage. `.venv/backend/bin/pytest -m e2e tests/e2e_pipeline -q`: 6 passed. `bash scripts/check`: OK. Webcam/manual demo not run in this environment (no camera).
### 19:54 T15 Bluesky watchlist adapter build
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#71`
- **Branch:** `agent/T15-build`
- **Prompt submitted:** "Build T15 from docs/agent/plans/T15.md (issue #71). The plan is approved: getAuthorFeed watchlist adapter behind FEATURE_BLUESKY, reliability_score 0.5, at most 10 accounts, 25 posts per page, 10 minute startup window. Record the post-deletion gap as a documented open item in docs/OWASP_AUDIT.md; do not strip post text from logs. Branch agent/T15-build, one PR, Closes #71."
- **AI output summary:** Added `BlueskyAdapter` (`ai-brain/bluesky_adapter.py`) polling unauthenticated `getAuthorFeed` for a short actor watchlist behind `FEATURE_BLUESKY` (default off). Wired through `bluesky_enabled()` and `LiveOsintRunner._select_adapters`. Fixture tests cover filtering, dedup, URL shape, per-actor failures, and corroboration with a non-Bluesky source. Updated `.env.example`, README, `OSINT_PIPELINE.md`, and OWASP A04/A10/privacy plus open item 11 for the deletion gap without stripping post text.
- **Human review and modifications:** Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something. Approval choices already applied: reliability 0.5, limits 10/25/10m, deletion gap as open item, do not strip post text.
- **Verification:** `.venv/osint/bin/pytest ai-brain/tests -q`: 89 passed. `ruff check ai-brain/` and `complexipy ai-brain --max-complexity-allowed 15` passed. `bash scripts/check`: OK. No live Bluesky request was sent.

### 20:19 T17 build: login rate limiting
- **Date:** 2026-11-05
- **Team member:** Aiman Ahmed (`@aimanahmed495-max`)
- **Tool used:** Cursor
- **Associated Git issue:** `#72`
- **Branch:** `agent/T17-build`
- **Prompt submitted:** Build T17 from `docs/agent/plans/T17.md`. Team Lead explicitly authorized minimal edits to `backend/app/auth.py` for this task only. Do not touch `security.py`, `models.py`, migrations, `docker-compose.yml`, or `.github/`. Branch `agent/T17-build`, one PR to main, Closes #72.
- **AI output summary:** Added in-memory `LoginRateLimiter` in `backend/app/rate_limit.py` and wired it into `POST /auth/login` (~10 lines in `auth.py`): check before password verify, 429 with `Retry-After` when over limit, reset per-user count on success. Unit and route tests cover over-limit, success reset, separate keys, window expiry, IP cap, disable switch, and eviction. Updated `.env.example`, `backend/README.md`, `docs/DEVELOPER_SETUP.md`, OWASP A07/A09, and marked T17 done in `docs/agent/TASKS.md`.
- **Human review and modifications:** Authorization for `auth.py` came from Aiman in the prompt. Aiman read the merged diff and the PR review summary, and relied on CI results (all checks green) rather than rerunning locally. Small fixes made by hand where changes broke something.
- **Verification:** `bash scripts/check` printed `OK`. `pytest backend/tests/test_rate_limit.py backend/tests/test_auth.py`: 26 passed.
### 20:40 Frontend Event History Playwright coverage

- **Date:** 2026-11-05
- **Team member:** Zareer Sanjeed Khan
- **Tool used:** Codex
- **Associated Git issue:** #97
- **Branch:** `test/frontend-history-e2e`

- **Assistance:** Suggested extending the existing authenticated E2E flow with assertions for Event History visibility, seeded records, Pending/Corroborated/Resolved options, Pending-only filtering, reset behavior, and preserved sign-out coverage. Diagnosed an initial local failure as stale Docker data outside the seven-day history window.
- **Human review and modifications:** Zareer manually inserted and reviewed the assertions, removed assumptions about zero Resolved records and exact reset counts, reset the local test database, and reran the test.
- **Verification:** `git diff --check` passed. `node --check tests/e2e/heimdall.spec.js` passed. A fresh Docker database was seeded with six threat events. `npm test --prefix tests/e2e` passed: 1 test.
