# Heimdall Dashboard Prototype

This is the first frontend prototype for Heimdall. It demonstrates the
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


## What the backend team must provide

The prototype expects these routes:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Backend availability |
| `GET` | `/api/status` | Current operating mode and service health |
| `GET` | `/api/alerts` | Existing alerts |
| `PATCH` | `/api/alerts/{id}/acknowledge` | Operator acknowledges an alert |
| `WS` | `/ws/events` | Live alerts and system changes |

