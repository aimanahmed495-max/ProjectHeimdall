# Agent task queue

One task per run. Branch `agent/<task-id>`, one PR to `main`. Protected paths (see AGENTS.md) mean plan only.

T01 shared object classes | deps: none | done
  In `ai-brain/`, normalize the classifier output to one of person, vehicle, crowd, package, unknown so different sources can corroborate. Map obvious synonyms (man, woman, suspect to person; car, truck, van to vehicle; and so on). Anything else becomes unknown. Do not change the model call or prompt wording beyond listing the allowed classes.
  Accept: unit tests for each mapping and the unknown fallback; a corroboration test where two sources return different synonyms for the same class and still corroborate; `bash scripts/check` passes.

T02 pipeline E2E, matching sources | deps: none | done
  `tests/e2e_pipeline/test_osint_pipeline.py`, marker `e2e` (`tests/e2e/` is the Playwright package). Start the real API as a subprocess against the local test Postgres (backend venv), register the OSINT user and camera 1, then run `LiveOsintRunner` with two `StaticAdapter` sources and a scripted fake classifier returning the same class, `max_cycles=1`. Assert camera 1 becomes Active and the threat events become Corroborated.
  Accept: the test passes locally; no network; the API subprocess is always stopped. If this needs a new dependency or a ci.yml change: plan only.

T03 pipeline E2E, negative and failure cases | deps: T02 | done
  Same harness. Cases: different classes leave camera 1 Dormant; reports outside the window do not corroborate; one source raising a request error does not stop the other source or the runner; the same source twice does not corroborate.
  Accept: one test per case, all pass, none flaky across five consecutive runs.

T04 CI step for the pipeline E2E | deps: T02 | todo
  Plan only (touches `.github/workflows/ci.yml`). An `e2e` job already exists (Docker Compose + Playwright). Prefer adding a step to it over a new job; otherwise a job with a Postgres service that runs `pytest -m e2e`.
  Accept: plan in `docs/agent/plans/T04.md` with the exact YAML and why it is safe.

T06 OSINT structured logging | deps: none | done
  Replace ad hoc prints for pipeline events in `ai-brain/` with `logging` that emits JSON lines with timestamp, level, request_id and user_id. Keep the existing console banner output unchanged.
  Accept: caplog tests assert each field is present on classify, corroborate, and error events; existing tests still pass.

T08 OWASP audit refresh | deps: T01 | todo
  Docs only. Update A04, A10, A07, A09 and the Summary rows in `docs/OWASP_AUDIT.md` for the live OSINT path: corroboration now gates camera activation, and the OSINT module fetches the configured ntfy server and RSS feed URL. Every claim cites the file it came from.
  Accept: no sentence contradicts the current code; Open items updated.

T09 OSINT pipeline doc | deps: none | done
  Docs only. `docs/OSINT_PIPELINE.md`: data flow, source adapters, env variable table, failure behavior.
  Accept: the env table matches `ai-brain/.env.example` exactly; no variable invented.

T11 docstring pass, OSINT module | deps: T01, T03, T06 | done
  Google-style docstrings (Args, Returns, Raises) on every public class and method in `ai-brain/`. No behavior change.
  Accept: `bash scripts/check` passes; the diff contains only docstrings and comments.

T12 OSINT QA log draft | deps: T03 | todo
  `docs/qa/osint-qa-log.md`: test, edge case, severity (low/medium/high), result, resolution, linked issue (TODO if none). Only rows backed by a test that exists and was run.
  Accept: no row without a test behind it. Aiman posts it on the QA issue.

T13 OSINT README refresh | deps: T01 | done
  `ai-brain/README.md` and the OSINT statements in `README.md`. Remove the stale claim that OSINT does not switch the camera. Document the flag, shared classes, the E2E suite, and the demo steps.
  Accept: no statement contradicts the code.

T14 demo reset and preflight script | deps: none | todo
  `scripts/demo_reset.sh`: check `/health`, log in with the OSINT credentials from the environment, set camera 1 to Dormant (read its current fps and resolution first), print the ntfy and RSS demo commands. Never print credentials.
  Accept: shellcheck-clean by inspection; documented in `ai-brain/README.md`.

T15 Bluesky adapter | deps: T01 | todo
  Plan only first (new dependency and network behavior; verify the Bluesky API and auth requirements). Then a `SourceAdapter` behind `FEATURE_BLUESKY` (default off) with fixture tests, registered as a source, with `.env.example` and docs updated.
  Accept: plan in `docs/agent/plans/T15.md`; build only after Aiman approves it.

T16 vision trigger-driven activation (#34) | deps: T02 | todo
  Plan only first (touches `vision/`). Webcam or video-file frames into YOLOv8n, `vision/` no longer activates the camera itself, activation comes from corroboration, detections post as threat events with the camera ID, `FEATURE_PI_CAMERA` (default off) selects the source.
  Accept: plan in `docs/agent/plans/T16.md`; build only after Aiman approves it.

T17 login rate limiting | deps: none | todo
  Plan only (touches `backend/app/auth.py`). Closes the OWASP A07 gap. Confirm no teammate owns auth first.
  Accept: plan in `docs/agent/plans/T17.md`.

T18 Raspberry Pi camera, stretch | deps: T16 | hold
  `PiCameraStream`, a capture service with `/activate` and `/deactivate`, and a log of time from activation to first frame.

T19 OSINT location filtering | deps: T01 | hold
  A place or geotag filter so signals can be tied to an area. Plan first.

Teammate items, not in this queue: backend `/ready` and JSON logging, k6 runs, WCAG audit, browser E2E (merged), auth and OAuth.
