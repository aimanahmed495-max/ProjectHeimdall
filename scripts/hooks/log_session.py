#!/usr/bin/env python3
"""Append raw AI session events to .ai-log/raw/YYYY-MM-DD.jsonl.

Shared by Cursor hooks (.cursor/hooks.json) and Claude Code hooks (.claude/settings.json).
Usage: log_session.py <tool> <event>. Reads the hook payload as JSON on stdin.
Never blocks the agent: always exits 0 and, for Cursor prompt events, returns continue=true.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),  # OpenAI / Anthropic style
    re.compile(r"gsk_[A-Za-z0-9]{20,}"),  # Groq
    re.compile(r"AIza[0-9A-Za-z_\-]{20,}"),  # Google
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),  # GitHub
]
TEXT_KEYS = ("prompt", "text", "response", "last_assistant_message", "message")


def redact(value: str) -> str:
    for pattern in SECRET_PATTERNS:
        value = pattern.sub("[REDACTED]", value)
    return value


def main() -> None:
    tool = sys.argv[1] if len(sys.argv) > 1 else "unknown"
    event = sys.argv[2] if len(sys.argv) > 2 else "unknown"
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        payload = {}

    text = next((payload[k] for k in TEXT_KEYS if isinstance(payload.get(k), str)), "")
    now = dt.datetime.now().astimezone()
    record = {
        "ts": now.isoformat(timespec="seconds"),
        "tool": tool,
        "event": event,
        "session": payload.get("session_id") or payload.get("conversation_id"),
        "text": redact(text),
        "transcript_path": payload.get("transcript_path"),
    }
    out_dir = Path(".ai-log/raw")
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / f"{now:%Y-%m-%d}.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception:  # logging must never break the agent
        pass
    if len(sys.argv) > 2 and sys.argv[1] == "cursor" and sys.argv[2] == "prompt":
        print(json.dumps({"continue": True}))
    sys.exit(0)
