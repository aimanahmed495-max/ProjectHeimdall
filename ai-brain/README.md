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

## Test

From the repository root:

```bash
python -m pytest ai-brain/tests -q
```

The tests verify authentication, bearer-token setup, source attribution, unknown-source rejection, and OSINT-only event creation without fake camera references.
