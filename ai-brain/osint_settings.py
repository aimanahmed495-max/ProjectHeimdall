"""Read live-OSINT settings from the environment."""

from __future__ import annotations

import logging
import os


def live_osint_enabled() -> bool:
    """Return True when ``FEATURE_LIVE_OSINT`` is turned on.

    The default is off, which keeps the mock JSON ingestion path.
    """

    raw = os.getenv("FEATURE_LIVE_OSINT", "false")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def poll_seconds() -> float:
    """Return ``OSINT_POLL_SECONDS``, or 5 when the value is unusable."""

    return _positive_float("OSINT_POLL_SECONDS", 5.0)


def corroboration_window_seconds() -> int:
    """Return ``CORROBORATION_WINDOW_SECONDS``, or 300 by default."""

    return _positive_int("CORROBORATION_WINDOW_SECONDS", 300)


def camera_id() -> int:
    """Return ``CAMERA_ID``, or 1 when the value is unusable."""

    return _positive_int("CAMERA_ID", 1)


def configure_logging() -> None:
    """Show info logs when the process has not configured logging yet."""

    if logging.getLogger().handlers:
        return
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def _positive_int(name: str, default: int) -> int:
    """Parse a positive integer environment variable."""

    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if value <= 0:
        return default
    return value


def _positive_float(name: str, default: float) -> float:
    """Parse a positive float environment variable."""

    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if value <= 0:
        return default
    return value
