## 2026-09-10 — feat: add OSINT ingestion agent with Groq classification (4a77609)

**Files changed:** ai-brain/.env.example, ai-brain/README.md, ai-brain/main.py, ai-brain/mock_alerts.json, ai-brain/mock_sources.json, ai-brain/osint_agent.py, ai-brain/osint_client.py, ai-brain/requirements.txt

**AI assistance used for:** Drafting the LangGraph OSINT agent (osint_agent.py), the Heimdall API client wrapper (osint_client.py), and the ingestion entrypoint (main.py); generating mock OSINT sources/alerts; and writing the module README.

**Verification:** Ran the full pipeline against the live Heimdall Core API (docker compose up + Alembic migrations applied). Registered 3 mock sources via POST /sources, processed 5 mock alerts through Groq (openai/gpt-oss-20b) classification, and confirmed all 5 threat events were created and retrievable via GET /threat-events.

## 2026-09-10 — docs: consolidate AI usage log and fix model name in README (0d350ff)

**Files changed:** AI_USAGE_LOG.md, ai-brain/README.md

**AI assistance used for:** Cleaning up duplicate auto-generated log stubs and correcting a stale model name reference.

**Verification:** Manual review of the diff before committing.

## 2026-09-10 — feat: add YOLOv8 vision pipeline against Heimdall API (be3783a)

**Files changed:** vision/.env.example, vision/README.md, vision/detector.py, vision/main.py, vision/requirements.txt, vision/vision_client.py, vision/test_media/*

**AI assistance used for:** Drafting the camera-agnostic FrameSource abstraction and ThreatDetector (detector.py), the Heimdall API client wrapper (vision_client.py), and the pipeline entrypoint (main.py), following the same OOP pattern as the OSINT module.

**Verification:** Ran the full pipeline against the live Heimdall Core API. Processed 3 test images (car, truck, person) through YOLOv8n, confirmed 19 detections posted as threat events and system logs, and verified camera state transitioned Active → Dormant correctly.
## 2026-09-10 — chore: fill in AI usage log and stop tracking downloaded model weights (2640a17)

**Files changed:** .gitignore,AI_USAGE_LOG.md,vision/yolov8n.pt

**AI assistance used for:** <!-- fill in one line -->

**Verification:** <!-- fill in one line -->
