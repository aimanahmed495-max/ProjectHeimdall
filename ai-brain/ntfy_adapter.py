"""Poll a public ntfy topic for OSINT messages."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode

import requests
from source_adapter import SourceAdapter, SourceItem


class NtfyAdapter(SourceAdapter):
    """Poll ``https://<server>/<topic>/json?poll=1&since=...`` once per call.

    The request is a normal HTTP GET. It does not open the ntfy streaming
    connection. Only lines whose ``event`` is ``message`` become items.
    """

    SOURCE_NAME = "ntfy-tipline"
    DEFAULT_SERVER = "https://ntfy.sh"

    def __init__(
        self,
        server: str,
        topic: str,
        timeout: float = 10.0,
    ) -> None:
        """Point the adapter at one public ntfy topic.

        Args:
            server: Origin such as ``https://ntfy.sh``, with no topic path.
            topic: Public topic name. No credentials are sent.
            timeout: Per-request timeout in seconds.

        Raises:
            ValueError: ``topic`` is empty.
        """

        super().__init__(self.SOURCE_NAME)
        cleaned_topic = topic.strip()
        if not cleaned_topic:
            raise ValueError("NTFY_TOPIC is not set.")
        self._server = server.strip().rstrip("/") or self.DEFAULT_SERVER
        self._topic = cleaned_topic
        self._timeout = timeout
        self._last_message_id: Optional[str] = None

    @classmethod
    def from_env(cls) -> "NtfyAdapter":
        """Build an adapter from ``NTFY_SERVER`` and ``NTFY_TOPIC``."""

        server = os.getenv("NTFY_SERVER", cls.DEFAULT_SERVER)
        topic = os.getenv("NTFY_TOPIC", "")
        return cls(server=server, topic=topic)

    def registration_payload(self) -> Dict[str, Any]:
        """Return the ``POST /sources`` body for the ntfy tipline."""

        return {
            "source_name": self.SOURCE_NAME,
            "source_type": "Public Push",
            "url": f"{self._server}/{self._topic}",
            "reliability_score": 0.5,
        }

    def _fetch_items(self) -> List[SourceItem]:
        """GET the topic once and return message items."""

        response = requests.get(self._poll_url(), timeout=self._timeout)
        response.raise_for_status()
        items, last_id = self._parse_body(response.text)
        if last_id:
            self._last_message_id = last_id
        return items

    def _poll_url(self) -> str:
        """Return the non-streaming poll URL, using the last message id."""

        since = self._last_message_id or "10m"
        topic = quote(self._topic, safe="")
        query = urlencode((("poll", "1"), ("since", since)))
        return f"{self._server}/{topic}/json?{query}"

    def _parse_body(self, body: str) -> Tuple[List[SourceItem], Optional[str]]:
        """Parse JSON lines and keep the latest message id."""

        items: List[SourceItem] = []
        last_id: Optional[str] = None
        for line in body.splitlines():
            parsed = self._accept_line(line)
            if parsed is None:
                continue
            message_id, item = parsed
            last_id = message_id
            if item is not None:
                items.append(item)
        return items, last_id

    def _accept_line(
        self,
        line: str,
    ) -> Optional[Tuple[str, Optional[SourceItem]]]:
        """Return a message id, or None for open, keepalive, and junk lines."""

        payload = self._json_object(line)
        if payload is None or payload.get("event") != "message":
            return None
        message_id = self._message_id(payload)
        if message_id is None:
            return None
        return message_id, self._message_item(payload, message_id)

    def _json_object(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse one JSON object, ignoring blank and non-object lines."""

        stripped = line.strip()
        if not stripped:
            return None
        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError:
            return None
        if isinstance(payload, dict):
            return payload
        return None

    def _message_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Return the ntfy message id when the line has one."""

        raw = payload.get("id")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
        if isinstance(raw, int):
            return str(raw)
        return None

    def _message_item(
        self,
        payload: Dict[str, Any],
        message_id: str,
    ) -> Optional[SourceItem]:
        """Build a source item when the message text is non-empty."""

        text = payload.get("message")
        if not isinstance(text, str) or not text.strip():
            return None
        return SourceItem(
            source_name=self.source_name,
            text=text.strip(),
            timestamp=self._timestamp(payload),
            external_id=message_id,
        )

    def _timestamp(self, payload: Dict[str, Any]) -> datetime:
        """Convert ntfy's unix ``time`` field to an aware datetime."""

        raw = payload.get("time")
        if isinstance(raw, (int, float)):
            return datetime.fromtimestamp(raw, tz=timezone.utc)
        return datetime.now(timezone.utc)
