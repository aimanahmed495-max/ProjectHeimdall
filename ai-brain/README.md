# Heimdall OSINT Ingestion

Authenticated LangGraph pipeline that converts mock open-source reports into source-attributed Heimdall threat events.

The pipeline:

1. Logs into the Heimdall API using configured OSINT service credentials.
2. Registers the mock OSINT sources or reuses existing records.
3. Resolves each alert’s source name to its database `source_id`.
4. Uses Groq’s GPT-OSS 20B model to classify the alert.
5. Posts an OSINT-only threat event with a `source_id` and no fake `camera_id`.
6. Posts a system log referencing the created threat event.

This module uses the real `/auth/login`, `/sources`, `/threat-events`, and `/system-logs` endpoints. It does not start Docker or the backend itself.

## Requirements

- Python 3.9+
- A running Heimdall Core API at `http://localhost:8000`
- A registered Heimdall service account
- A valid Groq API key

See `backend/README.md` for backend setup instructions.

## Install

From the repository root using the project virtual environment:

```bash
python -m pip install -r ai-brain/requirements.txt

```

## Environment

Create the private environment file only if one does not already exist:

```bash
test -f ai-brain/.env || cp ai-brain/.env.example ai-brain/.env
```

Set the following values in `ai-brain/.env`:

```text
GROQ_API_KEY=your_groq_api_key
BASE_URL=http://localhost:8000
OSINT_API_USERNAME=your_osint_service_username
OSINT_API_PASSWORD=your_osint_service_password
```

The `.env` file is ignored by Git. Do not commit real API keys or passwords.

## Mock data

- `mock_sources.json` contains the OSINT source records.
- `mock_alerts.json` contains alert text and the source that reported it.
- Multiple reports may reference the same source because repeated observations are valid evidence, not accidental database duplication.

## Run

Start PostgreSQL and the backend first, then run:

```bash
cd ai-brain
python main.py
```

The process prints authentication status, source registration, Groq classifications, created record IDs, and any errors.

`FEATURE_LIVE_OSINT` defaults to `false`. Leave it false to keep this mock path.

## Live sources

Set `FEATURE_LIVE_OSINT=true` in `ai-brain/.env` to poll two public sources instead of the mock files:

- ntfy topic `NTFY_TOPIC` on `NTFY_SERVER` (a normal HTTP poll, not a stream)
- RSS document `RSS_FEED_URL` (default `http://localhost:8001/feed.xml`)

Start the local RSS demo, which uses only the Python standard library:

```bash
python ai-brain/demo_feed.py
```

Open <http://127.0.0.1:8001/>, submit a report, and the feed is at `/feed.xml`. Reports that do not match `OSINT_KEYWORDS` are logged and are not sent to Groq.

When two different registered sources classify the same `object_class` within `CORROBORATION_WINDOW_SECONDS` (default 300), the loop PATCHes those threat events to status `Corroborated` with `corroborated_at`, PUTs camera `CAMERA_ID` (default 1) to `Active`, and posts one system log. One source does not change the camera. The camera row must already exist. A second report of a category that already corroborated does not activate the camera again.

## Test

From the repository root:

```bash
python -m pytest ai-brain/tests -q
```

The tests verify authentication, bearer-token setup, source attribution, unknown-source rejection, and OSINT-only event creation without fake camera references.
