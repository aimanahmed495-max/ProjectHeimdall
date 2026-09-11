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
