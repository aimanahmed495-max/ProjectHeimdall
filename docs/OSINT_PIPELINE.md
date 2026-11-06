# OSINT pipeline

The OSINT module (`ai-brain/`) is a host program and an HTTP client of the backend API. It never imports `backend/` code or touches the database. The entrypoint is `ai-brain/main.py`, which runs one of two paths depending on `FEATURE_LIVE_OSINT` (`ai-brain/osint_settings.py`):

- **Mock path** (flag off, the default): classify the alerts in `mock_alerts.json` once and exit. No corroboration, no camera change.
- **Live path** (flag on): poll the ntfy and RSS adapters (and Bluesky when `FEATURE_BLUESKY` is on) until interrupted, classify matching items, and set the camera Active when two distinct sources agree on the same shared object class (never `unknown`).

`OsintIngestionApp` loads `ai-brain/.env` with `python-dotenv` before anything else. `load_dotenv` does not override variables already set in the process environment.

## Data flow

### Live path

```mermaid
flowchart LR
    ntfy["ntfy topic<br/>NtfyAdapter"]
    rss["RSS feed<br/>RssAdapter"]
    filter["KeywordFilter<br/>OSINT_KEYWORDS"]
    agent["OsintAgent<br/>LangGraph + Groq<br/>normalize_object_class"]
    tracker["CorroborationTracker<br/>window, 2 distinct sources<br/>unknown never fires"]
    activator["CameraActivator"]
    api["Backend API"]

    ntfy -->|"SourceItem"| filter
    rss -->|"SourceItem"| filter
    filter -->|"matching text"| agent
    agent -->|"POST /threat-events (Pending)<br/>POST /system-logs"| api
    agent -->|"shared object_class, event_id"| tracker
    tracker -->|"Corroboration (first time only)"| activator
    activator -->|"PATCH /threat-events/{id}<br/>PUT /camera-states/{CAMERA_ID}<br/>POST /system-logs"| api
```

1. **Startup** (`main.py`, `_run_live`). `HeimdallAPIClient.authenticate` posts `OSINT_API_USERNAME` and `OSINT_API_PASSWORD` to `POST /auth/login` and keeps the bearer token on its HTTP session (`ai-brain/osint_client.py`). `OsintAgent` is then built, which requires `GROQ_API_KEY`. `configure_logging` (`ai-brain/osint_logging.py`) attaches a JSON-line handler to the root logger (stderr, INFO and above) when no handlers are already configured. The live runner is given `user_id` from `HeimdallAPIClient.current_user_id()` so later log events can carry it.
2. **Source registration** (`LiveOsintRunner.register_sources`, `ai-brain/live_osint.py`). The runner calls `GET /sources`, reuses the `source_id` of any adapter whose `source_name` is already stored, and calls `POST /sources` only for missing names. It prints the chosen id for each adapter (banner output, not JSON).
3. **Poll cycle** (`_run_cycle`). Every adapter is polled once, in order (ntfy, RSS, then Bluesky when enabled). Then the runner sleeps `OSINT_POLL_SECONDS` and repeats.
4. **Deduplication** (`SourceAdapter.poll`, `ai-brain/source_adapter.py`). Each adapter remembers the external ids it has already yielded and skips them. Items with an empty external id are dropped. This memory lasts only for the life of the process.
5. **Keyword filter** (`KeywordFilter.keep`, `ai-brain/keyword_filter.py`). A case-insensitive substring match against `OSINT_KEYWORDS`. Items that do not match emit a JSON `keyword_drop` event at INFO and never reach Groq.
6. **Classification** (`OsintAgent.run`, `ai-brain/osint_agent.py`). A three-node LangGraph: `ingest_alert` trims the text, `classify_with_llm` asks Groq model `openai/gpt-oss-20b` (temperature 0) for `object_class` and `confidence_score` as structured output (with a plain-JSON fallback parser), and `post_to_api` creates a threat event (`source_id`, `object_class`, `confidence_score`, status `Pending`) and a system log with module `osint-agent`. The prompt lists the five allowed classes. `ThreatClassification` runs every predicted label through `object_classes.normalize_object_class` before it is stored or returned. Each classified item emits a JSON `classify` event (WARNING when the result carries an error).
7. **Corroboration** (`CorroborationTracker.observe`, `ai-brain/corroboration.py`). Only results with no error, a non-empty `object_class`, and a positive `threat_event.event_id` are observed. The tracker normalizes the class again (so synonyms such as `man` and `woman` share a key), drops sightings older than `CORROBORATION_WINDOW_SECONDS` relative to the new report, and fires when two or more distinct `source_id`s remain for that class. The class `unknown` never corroborates, even from two sources. The same source reporting twice never counts. Timestamps come from the source item (ntfy `time`, RSS `pubDate`), not from when the item was processed. A class fires at most once per process unless an activation fails (see Failure behavior).
8. **Activation** (`CameraActivator.activate`, `ai-brain/camera_activation.py`). In this order: `PATCH /threat-events/{event_id}` with status `Corroborated` and `corroborated_at` (UTC ISO-8601) for every event in the window, `PUT /camera-states/{CAMERA_ID}` with mode `Active`, fps `5`, resolution `720p`, then one `POST /system-logs` naming the class and source ids, attached to the first event. On success the runner emits a JSON `corroborate` event. The camera row must already exist; the activator does not create it.

### Mock path

`main.py` reads `mock_sources.json` and `mock_alerts.json`, authenticates, registers each mock source with `POST /sources` (a `409 Conflict` is treated as already registered and the existing record is looked up), maps each alert's `source_name` to its `source_id`, builds `OsintAgent`, runs every alert through it, and prints a per-alert summary. It does not poll, filter by keyword, corroborate, or touch any camera. Mock classifications still go through `normalize_object_class`.

## Shared object classes

`ai-brain/object_classes.py` is the single vocabulary for classification and corroboration. Allowed values:

| Class | Example synonyms mapped onto it |
|---|---|
| `person` | man, woman, suspect, pedestrian, individual, human, intruder |
| `vehicle` | car, truck, van, bus, motorcycle, bike, suv, taxi, sedan |
| `crowd` | mob, group, gathering, people, protesters, riot |
| `package` | parcel, box, bag, backpack, suitcase, luggage, bundle |
| `unknown` | empty input, or any label not in the allowed set or synonym map |

`normalize_object_class` strips and lowercases the raw string, keeps an already-allowed class, maps known synonyms, and otherwise returns `unknown`. The agent prompt asks the model for one of the five allowed classes; the validator and the tracker both normalize so a synonym from a test double or a loose model reply still lands on the shared key. Corroboration requires two distinct sources on the same shared class other than `unknown`.

## Structured logging

Pipeline events on the live path use `logging` through `ai-brain/osint_logging.py`. `configure_logging` writes one JSON object per line to stderr with at least `timestamp`, `level`, `request_id`, and `user_id`. Startup banners, source-id listings, mock-path summaries, and Ctrl+C stop text stay as plain `print` output.

| Event | When | Typical level |
|---|---|---|
| `keyword_drop` | Item failed the keyword filter | INFO |
| `classify` | Agent finished one live item | INFO, or WARNING when `error` is set |
| `corroborate` | Activation succeeded for a class | INFO |
| `error` | Controlled live-loop failure (poll, classify, or activation) | ERROR |

Each poll batch and each classified item gets its own `request_id` (`new_request_id`). The runner binds `user_id` for the whole poll loop. Caplog coverage lives in `ai-brain/tests/test_osint_logging.py`.

## Source adapters

Adapters subclass `SourceAdapter` (`ai-brain/source_adapter.py`). An adapter provides `registration_payload()` (the `POST /sources` body) and `_fetch_items()` (one fetch of the current page). The base class `poll()` handles deduplication. Each item is a `SourceItem` with `source_name`, `text`, `timestamp`, and `external_id`.

| Adapter | `source_name` | `source_type` | Registered `url` | Reliability |
|---|---|---|---|---|
| `NtfyAdapter` | `ntfy-tipline` | `Public Push` | `<NTFY_SERVER>/<NTFY_TOPIC>` | 0.5 |
| `RssAdapter` | `local-rss-feed` | `RSS` | `RSS_FEED_URL` | 0.5 |
| `BlueskyAdapter` | `bluesky-watchlist` | `Social Media` | `<BLUESKY_APPVIEW_URL>/xrpc/app.bsky.feed.getAuthorFeed` | 0.5 |

### ntfy (`ai-brain/ntfy_adapter.py`)

- One plain HTTP GET per poll to `<server>/<topic>/json?poll=1&since=<since>`. It does not open the ntfy streaming connection. No credentials are sent.
- `since` is `10m` on the first poll, then the id of the last message seen, so later polls only ask for newer messages.
- The response is JSON lines. Only objects with `event` equal to `message`, an `id`, and a non-empty `message` become items. Open and keepalive events, blank lines, and lines that are not JSON objects are skipped.
- `timestamp` is the unix `time` field in UTC, or the current time when it is missing.
- An empty `NTFY_TOPIC` raises `ValueError("NTFY_TOPIC is not set.")`. A blank `NTFY_SERVER` falls back to `https://ntfy.sh`.

### RSS (`ai-brain/rss_adapter.py`)

- One HTTP GET per poll to `RSS_FEED_URL`, parsed with the standard-library `xml.etree.ElementTree`. Tags match with or without an XML namespace.
- Each `<item>` under `<channel>` needs a `guid` (the external id) and some text. Text is the `title` and `description` joined with a newline.
- `timestamp` is the RFC 822 `pubDate` (naive dates are treated as UTC), or the current time when it is missing or unparsable.
- A blank `RSS_FEED_URL` falls back to `http://localhost:8001/feed.xml`.

### Bluesky (`ai-brain/bluesky_adapter.py`)

- Off unless `FEATURE_BLUESKY` is on (and live OSINT is on). No new dependency; uses `requests` like ntfy and RSS.
- One unauthenticated HTTP GET per configured actor to `<BLUESKY_APPVIEW_URL>/xrpc/app.bsky.feed.getAuthorFeed?actor=...&limit=25&filter=posts_no_replies`. No cursor, no auth header, and no keyword search.
- Skips reposts and pins (`reason` present), non-`app.bsky.feed.post` records, empty text, uris that do not start with `at://`, authors labeled `!no-unauthenticated`, and posts whose AppView `indexedAt` is older than 10 minutes.
- `timestamp` is `indexedAt` (not client-set `createdAt`). All actors share one Heimdall source id, so two Bluesky accounts never corroborate each other.
- Empty `BLUESKY_ACTORS` or more than 10 actors raises `ValueError` at startup. A blank `BLUESKY_APPVIEW_URL` falls back to `https://public.api.bsky.app`.
- One actor's `RequestException` is logged and skipped; if every actor fails in the same poll, the error is re-raised so the live loop reports it like ntfy/RSS failures.

### Local demo feed (`ai-brain/demo_feed.py`)

`python ai-brain/demo_feed.py` starts a standard-library HTTP server on `127.0.0.1`. `GET /` is a form, `POST /items` stores a report in memory (request body capped at 8192 bytes), and `GET /feed.xml` serves the reports as RSS 2.0 with guids `demo-1`, `demo-2`, and so on. This is what the default `RSS_FEED_URL` points at.

The port comes from `DEMO_FEED_PORT` (default `8001`, also used when the value is not a valid port). That variable is read only by the demo server and is not listed in `ai-brain/.env.example`, so it is not in the table below.

## Environment variables

These are exactly the variables in `ai-brain/.env.example`, in the same order. "Example value" is the value in that file. "Default in code" is what the code uses when the variable is unset.

| Variable | Example value | Default in code | Used by | Purpose |
|---|---|---|---|---|
| `GROQ_API_KEY` | *(empty)* | none; required | Both paths (`osint_agent.py`) | Groq API key for classification. Missing or blank stops startup. |
| `BASE_URL` | `http://localhost:8000` | `http://localhost:8000` | Both paths (`osint_client.py`) | Backend API origin. A trailing `/` is stripped. |
| `OSINT_API_USERNAME` | `replace_with_osint_username` | none; required | Both paths (`osint_client.py`) | Service account for `POST /auth/login`. |
| `OSINT_API_PASSWORD` | `replace_with_osint_password` | none; required | Both paths (`osint_client.py`) | Password for that account. |
| `FEATURE_LIVE_OSINT` | `false` | `false` | `main.py` (`osint_settings.py`) | `1`, `true`, `yes`, or `on` (any case) selects the live path. Anything else keeps the mock path. |
| `NTFY_SERVER` | `https://ntfy.sh` | `https://ntfy.sh` | Live path (`ntfy_adapter.py`) | ntfy origin, without the topic. |
| `NTFY_TOPIC` | `heimdall-demo-change-me` | none; required on the live path | Live path (`ntfy_adapter.py`) | Public ntfy topic to poll. |
| `RSS_FEED_URL` | `http://localhost:8001/feed.xml` | `http://localhost:8001/feed.xml` | Live path (`rss_adapter.py`) | RSS 2.0 document to poll. |
| `FEATURE_BLUESKY` | `false` | `false` | Live path (`osint_settings.py`, `live_osint.py`) | `1`, `true`, `yes`, or `on` appends the Bluesky adapter. Only read when live OSINT is on. |
| `BLUESKY_APPVIEW_URL` | `https://public.api.bsky.app` | `https://public.api.bsky.app` | Live path (`bluesky_adapter.py`) | Bluesky AppView origin for getAuthorFeed. |
| `BLUESKY_ACTORS` | `replace-with-demo-handle.bsky.social` | none; required when Bluesky is on | Live path (`bluesky_adapter.py`) | Comma-separated handles or DIDs, at most 10. |
| `OSINT_POLL_SECONDS` | `5` | `5` | Live path (`osint_settings.py`) | Seconds to sleep between poll cycles. Positive float. |
| `OSINT_KEYWORDS` | `shots,gun,weapon,armed,fire,explosion,suspicious,fight,robbery,threat` | the same ten words | Live path (`keyword_filter.py`) | Comma-separated keywords. Blank entries are ignored; an empty list uses the defaults. |
| `CORROBORATION_WINDOW_SECONDS` | `300` | `300` | Live path (`osint_settings.py`) | Maximum age gap, in seconds, between reports that can corroborate. Positive integer. |
| `CAMERA_ID` | `1` | `1` | Live path (`osint_settings.py`) | `camera_states.camera_id` set Active on corroboration. Positive integer. |

`OSINT_POLL_SECONDS`, `CORROBORATION_WINDOW_SECONDS`, and `CAMERA_ID` silently fall back to their defaults when the value is blank, not a number, or not positive (`_positive_float` and `_positive_int` in `osint_settings.py`).

## Failure behavior

Startup and mock-path failures still print plain `Error: ...` or `Error preparing OSINT ingestion: ...` to stderr. Inside the live loop, controlled failures emit JSON `error` events (`stage` is `poll`, `classify`, or `corroborate`) and the loop keeps running. Keyword drops use JSON `keyword_drop` events. `HeimdallAPIUnavailableError` (connection failure or timeout) is a subclass of `HeimdallAPIError`, so every handler below that catches `HeimdallAPIError` also covers an unreachable API. HTTP requests to the API and to both sources use a 10 second timeout.

### Startup (exit code 1, nothing is polled)

| Condition | Where it is caught |
|---|---|
| API unreachable during login | `_authenticate_live` / `run` in `main.py` |
| `OSINT_API_USERNAME` or `OSINT_API_PASSWORD` missing, login rejected, or no `access_token` in the response | same |
| `GROQ_API_KEY` missing (`OsintAgentError`) | `_build_live_agent` / `run` in `main.py` |
| `NTFY_TOPIC` empty (`ValueError` while building the default adapters) | `_start_live` in `main.py` |
| `BLUESKY_ACTORS` empty or more than 10 when `FEATURE_BLUESKY` is on (`ValueError`) | `_start_live` in `main.py` |
| `GET /sources` fails or does not return a list, `POST /sources` fails, or a created source has no `source_id` | `_start_live` in `main.py` |
| Mock path only: a mock JSON file is missing, is not a JSON array, or has an alert without `source_name` or `alert_text`, or an alert names an unregistered source | `run` in `main.py` |

### Inside the live loop (the loop keeps running)

| Condition | Behavior |
|---|---|
| An adapter request fails (`requests.RequestException`: connection error, timeout, or non-2xx status via `raise_for_status`) | JSON `error` with `stage=poll`, that adapter yields nothing this cycle, the other adapters still run, polling continues (`_new_items`). |
| ntfy returns lines that are not JSON or not message events | Those lines are skipped (`_accept_line`). |
| RSS returns invalid XML or no `<channel>` | No items this cycle, nothing logged (`_parse_feed`). |
| Groq call or output parsing fails | The result carries `Groq classification failed: ...`; nothing is posted and the item does not count toward corroboration. A JSON `classify` event is still emitted at WARNING. |
| `POST /threat-events` fails | The result carries the error; nothing counts toward corroboration. |
| Threat event stored but `POST /system-logs` fails | The result keeps `threat_event` but also carries an error, so the runner skips corroboration for that event. |
| Two sources both classify as `unknown` (or any unmapped label that normalizes to `unknown`) | Both may post Pending threat events; the tracker never fires and the camera stays Dormant. |
| Activation fails (`PATCH`, `PUT`, or the activation `POST /system-logs`) | JSON `error` with `stage=corroborate`, and `CorroborationTracker.release` re-arms the class so the next matching report can fire again. Calls that already succeeded are not rolled back. A missing camera row fails here with a 404 from the `PUT`. |
| Ctrl+C after source registration | Prints `Stopped live OSINT polling.` and exits 0. |

Only `requests.RequestException` is caught around an adapter poll and only `HeimdallAPIError` around the agent and the activator. Any other exception ends the process.

On restart, adapter dedup memory and corroboration state start empty. The first ntfy poll asks for the last 10 minutes again and the RSS feed is read in full, so items may be classified and posted a second time.

The mock path processes every alert even if some fail. It exits 1 if any alert finished with an error, otherwise 0.

### Test coverage

Unit and integration coverage in `ai-brain/tests/`: shared class mapping and the unknown fallback (`test_object_classes.py`), corroboration rules including synonym agreement and unknown never firing (`test_corroboration.py`), JSON classify / corroborate / error fields (`test_osint_logging.py`), keyword filtering, source registration, single-source no-op, Bluesky flag wiring, and activation order (`test_live_osint.py`), adapter parsing and dedup (`test_adapters.py`, `test_bluesky_adapter.py`), and login and source mapping (`test_osint_integration.py`). End-to-end coverage in `tests/e2e_pipeline/`: matching sources activate the camera (T02); different classes, an expired window, an adapter request error, and the same source twice leave the camera Dormant (T03). These failure cases still have no dedicated unit test: activation failure re-arming the class, and a system-log failure skipping corroboration.
