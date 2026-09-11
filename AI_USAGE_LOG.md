## 2026-09-10 — feat: add OSINT ingestion agent with Groq classification (4a77609)

**Files changed:** ai-brain/.env.example, ai-brain/README.md, ai-brain/main.py, ai-brain/mock_alerts.json, ai-brain/mock_sources.json, ai-brain/osint_agent.py, ai-brain/osint_client.py, ai-brain/requirements.txt

**AI assistance used for:** Drafting the LangGraph OSINT agent (osint_agent.py), the Heimdall API client wrapper (osint_client.py), and the ingestion entrypoint (main.py); generating mock OSINT sources/alerts; and writing the module README.

**Verification:** Ran the full pipeline against the live Heimdall Core API (docker compose up + Alembic migrations applied). Registered 3 mock sources via POST /sources, processed 5 mock alerts through Groq (openai/gpt-oss-20b) classification, and confirmed all 5 threat events were created and retrievable via GET /threat-events.
## 2026-09-10 — docs: consolidate AI usage log and fix model name in README (0d350ff)

**Files changed:** AI_USAGE_LOG.md,ai-brain/README.md

**AI assistance used for:** <!-- fill in one line -->

**Verification:** <!-- fill in one line -->
