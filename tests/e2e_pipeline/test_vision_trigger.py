"""E2E: OSINT corroboration Activates the camera; vision posts a detection."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, List, Optional, Tuple

import pytest
from camera_activation import CameraActivator
from corroboration import CorroborationTracker
from keyword_filter import KeywordFilter
from live_osint import LiveOsintRunner
from test_osint_pipeline import (
    ALPHA,
    BETA,
    SHARED_CLASS,
    ScriptedClassifier,
    assert_camera_mode,
    single_batch,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "vision"))

from vision_client import HeimdallVisionClient  # noqa: E402
from vision_runner import VisionRunner  # noqa: E402
from vision_settings import VisionSettings  # noqa: E402

pytestmark = pytest.mark.e2e


class FakeDetector:
    """Return one scripted detection per frame."""

    def detect(self, frame: Any) -> List[Tuple[str, float]]:
        return [("person", 0.88)]


class FakeFrameSource:
    """Yield a single synthetic frame while open."""

    def __init__(self) -> None:
        self._open = False

    def open(self) -> None:
        self._open = True

    def read(self) -> Optional[Tuple[str, Any]]:
        if not self._open:
            return None
        return ("e2e-frame", object())

    def close(self) -> None:
        self._open = False

    @property
    def is_open(self) -> bool:
        return self._open


def test_corroboration_triggers_vision_threat_event(
    api, osint_client, dormant_camera, api_url, osint_user
):
    """After OSINT Activates camera 1, VisionRunner posts a vision threat event."""

    now = datetime.now(timezone.utc)
    adapters = [
        single_batch(ALPHA, "gun seen near the north gate", "alpha-vision-1", now),
        single_batch(
            BETA,
            "man with a gun at the north gate",
            "beta-vision-1",
            now + timedelta(seconds=10),
        ),
    ]
    classifier = ScriptedClassifier(osint_client, SHARED_CLASS)
    osint_runner = LiveOsintRunner(
        client=osint_client,
        agent=classifier,
        adapters=adapters,
        keyword_filter=KeywordFilter(["gun"]),
        tracker=CorroborationTracker(window_seconds=300),
        activator=CameraActivator(osint_client, camera_id=dormant_camera),
        poll_interval=1,
        sleep=lambda _delay: None,
    )

    assert osint_runner.run(max_cycles=1) == 0
    assert_camera_mode(api, dormant_camera, "Active")

    vision_client = HeimdallVisionClient(
        base_url=api_url,
        username=osint_user["username"],
        password=osint_user["password"],
    )
    vision_client.authenticate()
    settings = VisionSettings(
        camera_id=dormant_camera,
        frame_source="0",
        state_poll_seconds=1.0,
        event_cooldown_seconds=0.0,
        feature_pi_camera=False,
    )
    now_clock = [0.0]

    def clock() -> float:
        return now_clock[0]

    def sleep(delay: float) -> None:
        now_clock[0] += delay

    vision_runner = VisionRunner(
        vision_client,
        FakeDetector(),
        FakeFrameSource(),
        settings,
        sleep=sleep,
        clock=clock,
    )
    assert vision_runner.run(max_cycles=1) == 0

    events = api.get("/threat-events")
    assert events.status_code == 200, events.text
    vision_events = [
        row
        for row in events.json()
        if row.get("camera_id") == dormant_camera
        and row.get("source_id") is None
        and row.get("object_class") == "person"
    ]
    assert len(vision_events) >= 1
    assert vision_events[0]["status"] == "Pending"
