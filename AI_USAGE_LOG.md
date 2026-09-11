# Heimdall — Frontend AI Development Log

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