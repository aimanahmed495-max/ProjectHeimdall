"""Background WebSocket listener used by the Streamlit dashboard."""

from __future__ import annotations

import asyncio
import json
import threading
from collections import deque

import websockets


class EventBuffer:
    """Keep recent WebSocket events without writing to Streamlit from a thread."""

    def __init__(self, url: str, max_events: int = 50) -> None:
        self.url = url
        self._events: deque[dict] = deque(maxlen=max_events)
        self._lock = threading.Lock()
        self.connected = False
        self.error: str | None = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def snapshot(self) -> list[dict]:
        with self._lock:
            return list(reversed(self._events))

    def _run(self) -> None:
        asyncio.run(self._listen_forever())

    async def _listen_forever(self) -> None:
        while True:
            try:
                async with websockets.connect(self.url) as websocket:
                    self.connected = True
                    self.error = None
                    async for message in websocket:
                        event = json.loads(message)
                        with self._lock:
                            self._events.append(event)
            except Exception as exc:
                self.connected = False
                self.error = str(exc)
                await asyncio.sleep(2)
