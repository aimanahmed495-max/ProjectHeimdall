#!/usr/bin/env python3
"""Claude Code PreToolUse guard: block file tools from touching .env files.

Exit code 2 blocks the tool call and shows stderr to Claude.
"""

from __future__ import annotations

import json
import sys
from pathlib import PurePath


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    path = str((payload.get("tool_input") or {}).get("file_path", ""))
    name = PurePath(path).name
    if name.startswith(".env") and name != ".env.example":
        print(f"Blocked: {name} holds secrets. Use .env.example for structure.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
