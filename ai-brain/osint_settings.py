"""Read live-OSINT settings from the environment."""

from __future__ import annotations

import os


def live_osint_enabled() -> bool:
    """Return True when ``FEATURE_LIVE_OSINT`` is turned on.

    The default is off, which keeps the mock JSON ingestion path.

    Returns:
        ``True`` for ``1``, ``true``, ``yes``, or ``on`` (case-insensitive).
    """

    return _flag_enabled("FEATURE_LIVE_OSINT")


def bluesky_enabled() -> bool:
    """Return True when ``FEATURE_BLUESKY`` is turned on.

    The default is off. The flag only matters when live OSINT is on;
    ``LiveOsintRunner`` is the only caller.

    Returns:
        ``True`` for ``1``, ``true``, ``yes``, or ``on`` (case-insensitive).
    """

    return _flag_enabled("FEATURE_BLUESKY")


def _flag_enabled(name: str) -> bool:
    """Return True when an env flag is a recognized on-value."""

    raw = os.getenv(name, "false")
    return raw.strip().lower() in {"1", "true", "yes", "on"}

def poll_seconds() -> float:
    """Return ``OSINT_POLL_SECONDS``, or 5 when the value is unusable.

    Returns:
        A positive poll interval in seconds.
    """

    return _positive_float("OSINT_POLL_SECONDS", 5.0)


def corroboration_window_seconds() -> int:
    """Return ``CORROBORATION_WINDOW_SECONDS``, or 300 by default.

    Returns:
        A positive corroboration window length in seconds.
    """

    return _positive_int("CORROBORATION_WINDOW_SECONDS", 300)


def camera_id() -> int:
    """Return ``CAMERA_ID``, or 1 when the value is unusable.

    Returns:
        A positive Heimdall camera id.
    """

    return _positive_int("CAMERA_ID", 1)


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
