# Agent task queue

One task per run. Branch `agent/<task-id>`, one PR to `main`. Protected paths (see AGENTS.md) mean plan only.

T01 shared object classes | deps: none | todo
  In `ai-brain/`, normalize the classifier output to one of person, vehicle, crowd, package, unknown so different sources can corroborate. Map obvious synonyms (man, woman, suspect to person; car, truck, van to vehicle; and so on). Anything else becomes unknown. Do not change the model call or prompt wording beyond listing the allowed classes.
  Accept: unit tests for each mapping and the unknown fallback; a corroboration test where two sources return different synonyms for the same class and still corroborate; `bash scripts/check` passes.

T02 pipeline E2E, matching sources | deps: none | todo
  `tests/e2e/test_osint_pipeline.py`, marker `e2e`. Start the real API as a subprocess against the local test Postgres (backend venv), register the OSINT user and camera 1, then run `LiveOsintRunner` with two `StaticAdapter` sources and a scripted fake classifier returning the same class, `max_cycles=1`. Assert camera 1 becomes Active and the threat events become Corroborated.
  Accept: the test passes locally; no network; the API subprocess is always stopped. If this needs a new dependency or a ci.yml change: plan only.

T03 pipeline E2E, negative and failure cases | deps: T02 | todo
  Same harness. Cases: different classes leave camera 1 Dormant; reports outside the window do not corroborate; one source raising a request error does not stop the other source or the runner; the same source twice does not corroborate.
  Accept: one test per case, all pass, none flaky across five consecutive runs.

T04 CI e2e job | deps: T02 | todo
  Plan only (touches `.github/workflows/ci.yml`). Add an `e2e` job with a Postgres service that installs backend and ai-brain requirements, runs migrations, and runs `pytest -m e2e`.
  Accept: plan in `docs/agent/plans/T04.md` listing the exact job YAML and why it is safe.

T05 browser E2E | deps: T02 | todo
  Plan only (new dependency, new CI step). Playwright against `frontend/heimdall_console.html` served on port 8501 (the API only allows that origin). Cover: login succeeds, bad login is rejected, camera 1 state is shown after the pipeline test sets it Active. Read the console HTML first and use real selectors.
  Accept: plan in `docs/agent/plans/T05.md` with the selectors found and the proposed CI step.

T06 OSINT structured logging | deps: none | todo
  Replace ad hoc prints for pipeline events in `ai-brain/` with `logging` that emits JSON lines with timestamp, level, request_id and user_id. Keep the existing console banner output unchanged.
  Accept: caplog tests assert each field is present on classify, corroborate, and error events; existing tests still pass.

T07 backend ready probe | deps: none | todo
  Confirm no open issue already owns this. Add `GET /ready` that returns 200 only when the database answers and migrations are at head, otherwise 503. `GET /health` stays unchanged.
  Accept: backend tests for ready and not ready; `docs/OWASP_AUDIT.md` route table updated.

T08 OWASP audit refresh | deps: none | todo
  Docs only. Update the A04 and A10 sections and Summary rows in `docs/OWASP_AUDIT.md` for the live OSINT path: corroboration now gates camera activation, and the OSINT module fetches the configured ntfy server and RSS feed URL. Every claim cites the file it came from.
  Accept: no sentence in A04 or A10 contradicts the current code; Open items updated.

T09 OSINT pipeline doc | deps: none | todo
  Docs only. `docs/OSINT_PIPELINE.md`: data flow, source adapters, env variable table, failure behavior.
  Accept: the env table matches `ai-brain/.env.example` exactly; no variable invented.

T10 k6 script | deps: none | todo
  Write `load/k6/api.js` hitting `/health`, login, and `GET /threat-events`. Do not run it and do not install k6. Aiman runs it and posts the output on the issue.
  Accept: script lints by inspection; README note in `load/` explains how to run it.

Deferred, not in the queue: Bluesky adapter, vision webcam source (#34).
