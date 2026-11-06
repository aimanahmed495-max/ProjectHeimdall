# Heimdall OSINT Ingestion

Authenticated LangGraph pipeline that turns open-source reports into source-attributed Heimdall threat events. Two paths share the same API client and classifier:

- **Mock** (`FEATURE_LIVE_OSINT` off, the default): classify `mock_alerts.json` once and exit. No corroboration, no camera change.
- **Live** (`FEATURE_LIVE_OSINT=true`): poll ntfy and RSS (and Bluesky when `FEATURE_BLUESKY` is on), classify keyword matches, and set camera `CAMERA_ID` Active when two distinct sources agree on the same shared object class inside the corroboration window.

The module uses the real `/auth/login`, `/sources`, `/threat-events`, `/camera-states`, and `/system-logs` endpoints. It does not start Docker or the backend itself. Deeper flow and failure notes live in [docs/OSINT_PIPELINE.md](../docs/OSINT_PIPELINE.md).

## Requirements

- Python 3.11+
- A running Heimdall Core API at `http://localhost:8000`
- A registered Heimdall service account
- A valid Groq API key (live and mock paths both call Groq)

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

Variables in `ai-brain/.env.example` (same names, same order):

```text
GROQ_API_KEY=
BASE_URL=http://localhost:8000
OSINT_API_USERNAME=replace_with_osint_username
OSINT_API_PASSWORD=replace_with_osint_password
FEATURE_LIVE_OSINT=false
NTFY_SERVER=https://ntfy.sh
NTFY_TOPIC=heimdall-demo-change-me
RSS_FEED_URL=http://localhost:8001/feed.xml
FEATURE_BLUESKY=false
BLUESKY_APPVIEW_URL=https://public.api.bsky.app
BLUESKY_ACTORS=replace-with-demo-handle.bsky.social
OSINT_POLL_SECONDS=5
OSINT_KEYWORDS=shots,gun,weapon,armed,fire,explosion,suspicious,fight,robbery,threat
CORROBORATION_WINDOW_SECONDS=300
CAMERA_ID=1
```

`FEATURE_LIVE_OSINT` and `FEATURE_BLUESKY` accept `1`, `true`, `yes`, or `on` (any case). Anything else leaves the flag off. Bluesky is only wired when live OSINT is on. The `.env` file is ignored by Git. Do not commit real API keys or passwords.

## Shared object classes

Classifier output is normalized in `object_classes.py` to one of `person`, `vehicle`, `crowd`, `package`, or `unknown` so independent sources can corroborate. Obvious synonyms map to those labels (for example man/woman/suspect → `person`, car/truck/van → `vehicle`). Anything else becomes `unknown`. The class `unknown` never corroborates, even from two sources.

## Mock data

- `mock_sources.json` contains the OSINT source records.
- `mock_alerts.json` contains alert text and the source that reported it.
- Multiple reports may reference the same source because repeated observations are valid evidence, not accidental database duplication.

## Run (mock path)

Start PostgreSQL and the backend first, then run:

```bash
cd ai-brain
python main.py
```

The process prints authentication status, source registration, Groq classifications, created record IDs, and any errors. Leave `FEATURE_LIVE_OSINT` false (or unset) for this path.

## Live sources

Set `FEATURE_LIVE_OSINT=true` in `ai-brain/.env` to poll public sources instead of the mock files:

- ntfy topic `NTFY_TOPIC` on `NTFY_SERVER` (a normal HTTP poll, not a stream)
- RSS document `RSS_FEED_URL` (default `http://localhost:8001/feed.xml`)
- Bluesky author feeds when `FEATURE_BLUESKY=true` (default off)

Bluesky is a short watchlist, not keyword search. With the flag on, `BlueskyAdapter` polls unauthenticated `app.bsky.feed.getAuthorFeed` on `BLUESKY_APPVIEW_URL` (default `https://public.api.bsky.app`) for each handle or DID in `BLUESKY_ACTORS` (comma-separated, at most 10). Only list accounts the team owns or public agency accounts. Unauthenticated Bluesky keyword search is unreliable and is not used. All watched accounts register as one Heimdall source (`bluesky-watchlist`, reliability 0.5), so two Bluesky accounts never corroborate each other; a Bluesky tip still corroborates with ntfy or RSS. For the demo, post a matching tip from the team Bluesky account while ntfy or RSS also reports the same class.

Start the local RSS demo, which uses only the Python standard library:

```bash
python ai-brain/demo_feed.py
```

Open <http://127.0.0.1:8001/>, submit a report, and the feed is at `/feed.xml`. Reports that do not match `OSINT_KEYWORDS` are logged and are not sent to Groq.

When two different registered sources classify the same shared `object_class` within `CORROBORATION_WINDOW_SECONDS` (default 300), the loop PATCHes those threat events to status `Corroborated` with `corroborated_at`, PUTs camera `CAMERA_ID` (default 1) to `Active`, and posts one system log. One source alone does not change the camera. The camera row must already exist. A second report of a category that already corroborated does not activate the camera again.

## Demo steps

1. Start the stack and seed so camera 1 exists: `docker compose up -d`, then `docker compose exec api python -m backend.app.seed`.
2. Copy and fill `ai-brain/.env` (service account, Groq key, a private `NTFY_TOPIC`).
3. Reset the demo camera and print the demo commands:

```bash
set -a; . ai-brain/.env; set +a
bash scripts/demo_reset.sh
```

4. In separate terminals, start the RSS demo feed, then the live OSINT loop (`FEATURE_LIVE_OSINT=true`), then post one matching report to ntfy and one through the demo feed form (commands printed by the reset script).
5. Watch the console and `GET /camera-states/1`: camera 1 becomes `Active` only after both sources classify the same shared class inside the window.

## Demo reset and preflight

`scripts/demo_reset.sh` needs `curl` and `jq`. It reads `BASE_URL`, `OSINT_API_USERNAME`, `OSINT_API_PASSWORD`, `CAMERA_ID`, `NTFY_SERVER`, `NTFY_TOPIC`, and `RSS_FEED_URL` from the environment. Unset variables get the same defaults the OSINT module uses. It:

1. Checks `GET /health` and stops if the API or database is down.
2. Logs in with the OSINT service account.
3. Reads camera `CAMERA_ID` (default 1) and PUTs it back to `Dormant` with its current fps and resolution. It stops if the camera row does not exist; seed it with `docker compose exec api python -m backend.app.seed`.
4. Prints the commands for the RSS demo feed, the live OSINT loop, and one matching report for ntfy and for the demo feed.

It warns when `NTFY_TOPIC` is unset or still the placeholder, because public ntfy topics are readable by anyone. Credentials and the access token are never printed and are not passed to `curl` as arguments. Any failed step exits with status 1.

## Test

Unit and integration tests (HTTP and Groq mocked; no live network):

```bash
python -m pytest ai-brain/tests -q
```

Those cover authentication, bearer-token setup, source attribution, unknown-source rejection, OSINT-only event creation, keyword filtering, shared class normalization, corroboration (including synonym agreement and the `unknown` non-corroboration rule), camera activation, and structured logging fields.

Pipeline E2E (`tests/e2e_pipeline/`, marker `e2e`; not the Playwright package under `tests/e2e/`): starts the real API as a subprocess against the local test Postgres, drives `LiveOsintRunner` with `StaticAdapter` fakes and a scripted classifier (no Groq, no ntfy), and asserts camera activation, corroboration status, negatives, and failure isolation. The API subprocess is always stopped. Default pytest `addopts` deselect the marker; run it explicitly:

```bash
pytest -m e2e tests/e2e_pipeline -q
```

Postgres must accept the `test`/`test`/`test` credentials used by `scripts/check` (override `POSTGRES_PORT` if needed).
