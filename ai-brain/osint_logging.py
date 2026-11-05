"""JSON-line logging for OSINT pipeline events."""

from __future__ import annotations

import json
import logging
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional

_request_id: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
_user_id: ContextVar[Optional[int]] = ContextVar("user_id", default=None)


def new_request_id() -> str:
    """Return a fresh correlation id for one unit of pipeline work."""

    return uuid.uuid4().hex


@contextmanager
def log_context(
    request_id: Optional[str] = None,
    user_id: Optional[int] = None,
) -> Iterator[None]:
    """Bind ``request_id`` and ``user_id`` to events logged inside the block.

    Args:
        request_id: Correlation id. ``None`` keeps the enclosing value.
        user_id: API user the module is acting as. ``None`` keeps the
            enclosing value.

    Returns:
        A context manager that restores the previous values on exit.
    """

    tokens = []
    if request_id is not None:
        tokens.append((_request_id, _request_id.set(request_id)))
    if user_id is not None:
        tokens.append((_user_id, _user_id.set(user_id)))
    try:
        yield
    finally:
        for var, token in reversed(tokens):
            var.reset(token)


def log_event(
    logger: logging.Logger,
    level: int,
    event: str,
    message: str,
    **fields: Any,
) -> None:
    """Log one pipeline event with the bound request and user ids.

    Args:
        logger: Module logger that emits the record.
        level: ``logging`` level, for example ``logging.INFO``.
        event: Short machine-readable event name, such as ``classify``.
        message: Human-readable summary.
        **fields: Extra JSON fields for this event.
    """

    logger.log(
        level,
        message,
        extra={
            "event": event,
            "request_id": _request_id.get(),
            "user_id": _user_id.get(),
            "fields": fields,
        },
    )


class JsonFormatter(logging.Formatter):
    """Render each record as one JSON object per line."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize ``record`` with timestamp, level, request_id and user_id.

        Args:
            record: Record to format. Records not emitted through
                :func:`log_event` fall back to the ids bound right now.

        Returns:
            One line of JSON.
        """

        payload: Dict[str, Any] = {
            "timestamp": self._timestamp(record),
            "level": record.levelname,
            "logger": record.name,
            "event": getattr(record, "event", None),
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", _request_id.get()),
            "user_id": getattr(record, "user_id", _user_id.get()),
        }
        payload.update(getattr(record, "fields", None) or {})
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)

    @staticmethod
    def _timestamp(record: logging.LogRecord) -> str:
        """Return the record time as a UTC ISO-8601 string."""

        moment = datetime.fromtimestamp(record.created, tz=timezone.utc)
        return moment.isoformat().replace("+00:00", "Z")


def configure_logging() -> None:
    """Send INFO and above to stderr as JSON lines, unless already configured."""

    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)
