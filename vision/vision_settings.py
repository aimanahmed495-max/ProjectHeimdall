"""Read vision runner settings from the environment."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_TRUE_VALUES = {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class VisionSettings:
    """Resolved vision configuration for one process."""

    camera_id: int
    frame_source: str
    state_poll_seconds: float
    event_cooldown_seconds: float
    feature_pi_camera: bool
    show_window: bool


def load_settings() -> VisionSettings:
    """Load settings from the process environment.

    Returns:
        A ``VisionSettings`` instance with defaults applied for missing
        or invalid values.
    """

    return VisionSettings(
        camera_id=camera_id(),
        frame_source=frame_source(),
        state_poll_seconds=state_poll_seconds(),
        event_cooldown_seconds=event_cooldown_seconds(),
        feature_pi_camera=pi_camera_enabled(),
        show_window=show_window_enabled(),
    )


def pi_camera_enabled() -> bool:
    """Return True when ``FEATURE_PI_CAMERA`` is turned on.

    The default is off. Accepted spellings match ``FEATURE_LIVE_OSINT``.

    Returns:
        ``True`` for ``1``, ``true``, ``yes``, or ``on`` (case-insensitive).
    """

    return _flag_enabled("FEATURE_PI_CAMERA")


def show_window_enabled() -> bool:
    """Return True when ``VISION_SHOW_WINDOW`` is turned on.

    The default is off. Accepted spellings match ``FEATURE_PI_CAMERA``.

    Returns:
        ``True`` for ``1``, ``true``, ``yes``, or ``on`` (case-insensitive).
    """

    return _flag_enabled("VISION_SHOW_WINDOW")


def _flag_enabled(name: str) -> bool:
    """Return True when an env flag uses a known truthy spelling."""

    raw = os.getenv(name, "false")
    return raw.strip().lower() in _TRUE_VALUES


def camera_id() -> int:
    """Return ``VISION_CAMERA_ID``, or 1 when the value is unusable.

    Returns:
        A positive Heimdall camera id.
    """

    return _positive_int("VISION_CAMERA_ID", 1)


def frame_source() -> str:
    """Return ``VISION_FRAME_SOURCE``, or ``0`` when unset.

    Returns:
        Webcam index digits, a video file path, or an image directory.
    """

    raw = os.getenv("VISION_FRAME_SOURCE")
    if raw is None or not raw.strip():
        return "0"
    return raw.strip()


def state_poll_seconds() -> float:
    """Return ``VISION_STATE_POLL_SECONDS``, or 2 when unusable.

    Returns:
        A positive poll interval in seconds.
    """

    return _positive_float("VISION_STATE_POLL_SECONDS", 2.0)


def event_cooldown_seconds() -> float:
    """Return ``VISION_EVENT_COOLDOWN_SECONDS``, or 30 when unusable.

    Returns:
        A positive per-class event cooldown in seconds.
    """

    return _positive_float("VISION_EVENT_COOLDOWN_SECONDS", 30.0)


def _positive_int(name: str, default: int) -> int:
    """Parse a positive integer environment variable."""

    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        value = int(raw)
    except ValueError:
        logger.warning("Invalid %s=%r; using default %s", name, raw, default)
        return default
    if value <= 0:
        logger.warning("Non-positive %s=%r; using default %s", name, raw, default)
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
        logger.warning("Invalid %s=%r; using default %s", name, raw, default)
        return default
    if value <= 0:
        logger.warning("Non-positive %s=%r; using default %s", name, raw, default)
        return default
    return value
