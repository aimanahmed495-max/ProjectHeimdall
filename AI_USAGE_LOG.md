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