# Project Heimdall

OSINT-triggered camera activation system. Open-source signals (ntfy tips, RSS feeds) are filtered, classified by an LLM, and corroborated across independent sources. A corroborated incident sets a camera Active, and the vision module then detects objects in frames. Operators review everything in a Streamlit-hosted dashboard.

Course project (CS 599 Senior Design 2). Graded deliverables and rules live in the instructor README. Keep that in mind: every change is reviewed by the Team Lead (Aiman) and logged.

## Modules
- `backend/`: FastAPI + SQLAlchemy + Alembic on PostgreSQL. JWT auth (Argon2 hashes), soft deletes, `GET /health`.
- `ai-brain/`: OSINT pipeline. Source adapters (ntfy, RSS), keyword filter, LangGraph/Groq classifier, `CorroborationTracker`, `CameraActivator`, local demo feed.
- `vision/`: YOLOv8 detection client. Posts threat events to the API.
- `frontend/`: Streamlit host (`app.py`) embedding `heimdall_console.html`.
- `tests/`: dashboard tests (pytest) and `tests/frontend-console` (Node + jsdom).
- `docs/`: developer setup, architecture, `OWASP_AUDIT.md`.

## Architecture invariants (do not break these)
1. OSINT and vision are HTTP clients of the backend. They never import `backend/` code or touch the database.
2. Domain rows are soft-deleted (`deleted_at`). Never add a hard delete.
3. Never weaken auth: Argon2 hashing, signed expiring JWTs, `get_current_user` on every data route.
4. Config comes from environment variables. Adding one means updating that module's `.env.example` in the same change.
5. Incomplete features sit behind a flag that defaults to off (`FEATURE_LIVE_OSINT`, `FEATURE_PI_CAMERA`).
6. Corroboration needs two distinct source ids with the same object class inside the window. Do not loosen it.
7. Every Alembic migration has a working downgrade.
8. Security-relevant behavior changes must update `docs/OWASP_AUDIT.md` in the same PR.

## Commands
- Whole check (CI equivalent): `bash scripts/check`
- Run the stack: `docker compose up -d`, seed with `docker compose exec api python -m backend.app.seed`
- Lint: `ruff check backend/ ai-brain/ vision/` (rules E, F, I, C901, max complexity 10)
- Cognitive complexity: `complexipy <module> --max-complexity-allowed 15`
- OSINT tests: `pytest ai-brain/tests -q`
- Backend tests need Postgres and `alembic upgrade head`; see `scripts/check` for the env vars.
- Frontend console tests (`npm test` in `tests/frontend-console`) run in CI only.

## Code style
- Python 3.11 compatible. Type hints on public functions.
- Classes and public methods get docstrings with `Args:` and `Returns:` in the style already used in `ai-brain/live_osint.py`.
- Small modules, no god classes, clean error handling. No bare `print` for new log events; use `logging`.
- Tests never hit real services. No Groq, no ntfy.sh, no network. Use fakes (`FakeAgent`, `ScriptedAgent`, `StaticAdapter` in `ai-brain/tests/test_live_osint.py`) or mocked `requests`.
- All test data is synthetic.

## Scope and safety
- Never read, print, or log any `.env` file or API key. Use `.env.example` for structure.
- Never commit `.env`, model weights, or database dumps.
- Do not change `docker-compose.yml`, `.github/workflows/ci.yml`, `backend/alembic/versions/`, `backend/app/auth.py`, `backend/app/security.py`, or `backend/app/models.py` without a plan first (see Workflow).
- `AI_USAGE_LOG.md` is the certified course log. Do not edit it. Draft entries in `docs/ai-log/` instead.

## Workflow
- Every PR links an issue (`Closes #N`) and uses Conventional Commits (`feat:`, `fix:`, `test:`, `docs:`, `chore:`).
- Small commits. One task, one branch, one PR.
- Adding a dependency? Say why in the PR.
- Test results and bugs go on the GitHub issue, not only in the PR.

## Cursor Cloud specific instructions
- The environment has Postgres and three virtualenvs (`.venv/backend`, `.venv/osint`, `.venv/frontend`). Run `bash scripts/check` before every commit; it prints only failures.
- No API keys exist here. Never use live providers. Do not ask for keys.
- One task per run from `docs/agent/TASKS.md`. Take the task ID in the prompt, or the first `todo` whose dependencies are `done`. Do only that.
- Branch `agent/<task-id>`. One PR to `main`. Never push to `main`.
- If the task touches a protected path from Scope and safety, write `docs/agent/plans/<task-id>.md` and stop. Open a PR with the plan only.
- Stop rule: after two failed attempts at the same error, stop, commit what works, and put the blocker in the PR description.
- Finish with `bash scripts/check`, then follow the ai-log skill and commit the draft entry. PR description: what changed, acceptance test result, anything you could not verify.
