# Heimdall Sentinel Dashboard Prototype

This is Zareer's first frontend prototype for Heimdall. It demonstrates the
planned frontend-to-backend flow before the real OSINT and camera services are
ready.

The prototype includes:

- a Streamlit-hosted operations console based on the supplied Claude design;
- HTML/CSS/JavaScript views for the map, triage queue, cameras, reasoning,
  analytics, and alert history;
- a Python FastAPI mock backend;
- a live WebSocket event stream;
- REST endpoints for system status and saved alerts;
- simulated threat creation and alert acknowledgement; and
- tests for the REST and WebSocket flows.

## How the prototype flows

1. The Streamlit dashboard loads saved state through REST endpoints.
2. It opens a persistent connection to `ws://localhost:8000/ws/events`.
3. The **Simulate threat** button calls the mock backend.
4. FastAPI creates the alert and broadcasts an `alert.created` event.
5. The dashboard receives the event and refreshes its display.
6. The operator can acknowledge the alert from the dashboard.

In the real system, the OSINT engine will replace the **Simulate threat**
button. The agreed JSON contract can remain the same.

## Requirements

- Python 3.11 or newer
- Git
- Two terminal windows

## Install on macOS or Linux

From this folder, run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r frontend/requirements.txt
```

## Run the backend

In the first terminal:

```bash
source .venv/bin/activate
uvicorn frontend.demo_backend.main:app --reload
```

The backend is available at <http://localhost:8000>. FastAPI's interactive API
documentation is available at <http://localhost:8000/docs>.

## Run the dashboard

Open a second terminal in this folder:

```bash
source .venv/bin/activate
python -m streamlit run frontend/app.py
```

Open <http://localhost:8501> if Streamlit does not open it automatically.

## Demonstrate it

1. Confirm the dashboard shows `NORMAL` and `CONNECTED`.
2. Choose a confidence score and location.
3. Press **Simulate threat**.
4. Point out the new WebSocket event and the `ALERT` system mode.
5. Open the alert to explain the confidence and AI reasoning.
6. Press **Acknowledge** and point out the live acknowledgement event.

## Run the tests

```bash
pytest -q
```

## Put the prototype on your own branch later

Do this only after cloning the real shared Heimdall repository and confirming
that its default branch is `main`:

```bash
git switch main
git pull --ff-only origin main
git switch -c zareer-dev
```

Copy this complete folder into the shared repository. Then inspect everything
before staging it:

```bash
git status
git diff
pytest -q
```

When you and the team are ready for the first commit, stage only this folder:

```bash
git add -- heimdall-dashboard-prototype
git diff --cached
git commit -m "feat(dashboard): add live alert prototype"
git push -u origin zareer-dev
```

`git diff --cached` is your final review of exactly what will enter the commit.
Do not stage unrelated files created by teammates.

## Learning resources used by this prototype

| Resource | What you use it for |
| --- | --- |
| Python 3.11+ | All application code |
| Streamlit | Hosting the operations console from a Python entry point |
| HTML, CSS, and JavaScript | Claude-designed interface and browser interactions |
| Leaflet and OpenStreetMap | Interactive Wichita operations map |
| FastAPI | Creating the mock REST API and WebSocket route |
| Uvicorn | Running the FastAPI application locally |
| HTTPX | Sending REST requests from the dashboard |
| websockets | Listening continuously for live backend events |
| Pydantic | Validating alert and status data |
| Pytest | Testing the API, WebSocket, and dashboard rendering |
| Git and GitHub | Branching, commits, team review, and pull requests |
| VS Code | Editing, running, and debugging the Python files |

The most useful documentation to study is the official Streamlit introductory
tutorial, FastAPI's first-steps and WebSocket tutorials, the Python `asyncio`
tutorial, and GitHub's guide to branches and pull requests.

## What the real backend team must provide

The prototype expects these routes:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Backend availability |
| `GET` | `/api/status` | Current operating mode and service health |
| `GET` | `/api/alerts` | Existing alerts |
| `PATCH` | `/api/alerts/{id}/acknowledge` | Operator acknowledges an alert |
| `WS` | `/ws/events` | Live alerts and system changes |

The WebSocket uses an event envelope such as:

```json
{
  "type": "alert.created",
  "timestamp": "2026-08-28T12:00:00Z",
  "data": {
    "id": "example-id",
    "title": "Possible weapon detected",
    "confidence": 87
  }
}
```

## Suggested first commit

After reviewing these files with the team, use a focused commit message:

```bash
git add -- heimdall-dashboard-prototype
git commit -m "feat(dashboard): add live alert prototype"
```

Do not commit `.venv`, editor settings, secrets, or generated cache files.
