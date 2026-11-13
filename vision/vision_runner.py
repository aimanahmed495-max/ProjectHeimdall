"""Poll camera state and run detection only while the camera is Active."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, List, Optional, Protocol, Tuple

from frame_sources import PI_CAMERA_MESSAGE, FrameSource
from preview_window import PreviewWindow, build_preview_window
from throttle import DetectionThrottle
from vision_client import (
    HeimdallAPIError,
    HeimdallAPIUnavailableError,
    HeimdallVisionClient,
)
from vision_settings import VisionSettings

logger = logging.getLogger(__name__)

MODULE_NAME = "vision"
DEFAULT_STATUS = "Pending"
DEFAULT_FPS = 5.0


class Detector(Protocol):
    """The subset of ``ThreatDetector`` the runner needs."""

    def detect(self, frame: Any) -> List[Tuple[str, float]]:
        """Return ``(object_class, confidence)`` detections for one frame."""


class VisionRunner:
    """Poll camera state and capture only while the row is Active."""

    def __init__(
        self,
        client: HeimdallVisionClient,
        detector: Detector,
        source: FrameSource,
        settings: VisionSettings,
        sleep: Optional[Callable[[float], None]] = None,
        clock: Optional[Callable[[], float]] = None,
        throttle: Optional[DetectionThrottle] = None,
        preview: Optional[PreviewWindow] = None,
    ) -> None:
        """Wire the vision loop.

        Args:
            client: Authenticated Heimdall vision API client.
            detector: Object detector. Tests inject a fake.
            source: Frame source opened only while the camera is Active.
            settings: Resolved environment settings.
            sleep: Wait function, replaced in tests.
            clock: Monotonic clock, replaced in tests.
            throttle: Per-class post cooldown. Defaults from settings.
            preview: Optional frame preview. Defaults from ``show_window``.
        """

        self._client = client
        self._detector = detector
        self._source = source
        self._settings = settings
        self._sleep = sleep or time.sleep
        self._clock = clock or time.monotonic
        self._throttle = throttle or DetectionThrottle(
            settings.event_cooldown_seconds,
            clock=self._clock,
        )
        self._preview = preview or build_preview_window(settings.show_window)

    def run(self, max_cycles: Optional[int] = None) -> int:
        """Poll until interrupted, or until ``max_cycles`` when set.

        Args:
            max_cycles: Stop after this many state polls. ``None`` runs forever.

        Returns:
            Process exit code. Keyboard interrupt returns 0. A refused Pi
            source returns 1.
        """

        try:
            return self._poll_loop(max_cycles)
        except KeyboardInterrupt:
            logger.info("Stopped vision runner.")
            return 0
        except RuntimeError as exc:
            if PI_CAMERA_MESSAGE in str(exc):
                logger.error("%s", exc)
                return 1
            raise
        finally:
            self._close_source()

    def _poll_loop(self, max_cycles: Optional[int]) -> int:
        """Poll camera state, then sleep or capture, until finished."""

        completed = 0
        while True:
            self._run_cycle()
            completed += 1
            if max_cycles is not None and completed >= max_cycles:
                return 0

    def _run_cycle(self) -> None:
        """Fetch camera state once and capture or idle accordingly."""

        try:
            state = self._client.get_camera_state(self._settings.camera_id)
        except HeimdallAPIUnavailableError as exc:
            logger.warning("API unavailable while polling camera state: %s", exc)
            self._close_source()
            self._sleep(self._settings.state_poll_seconds)
            return
        except HeimdallAPIError as exc:
            logger.warning("Camera state poll failed: %s", exc)
            self._close_source()
            self._sleep(self._settings.state_poll_seconds)
            return

        if state is None:
            logger.warning(
                "Camera %s not found; waiting for seed or operator registration",
                self._settings.camera_id,
            )
            self._close_source()
            self._sleep(self._settings.state_poll_seconds)
            return

        mode = state.get("mode")
        if mode == "Active":
            self._run_active(state)
            return

        self._close_source()
        self._sleep(self._settings.state_poll_seconds)

    def _run_active(self, state: dict) -> None:
        """Open the source and process frames until the poll window ends."""

        if not self._source.is_open:
            self._source.open()
        fps = self._fps_from_state(state)
        frame_delay = 1.0 / fps
        deadline = self._clock() + self._settings.state_poll_seconds
        while self._clock() < deadline:
            self._process_one_frame()
            self._sleep(frame_delay)

    def _process_one_frame(self) -> None:
        """Read one frame, detect, preview, and post throttled events."""

        labeled = self._source.read()
        if labeled is None:
            return
        label, frame = labeled
        try:
            detections = self._detector.detect(frame)
        except Exception as exc:  # noqa: BLE001 - keep the loop alive
            logger.warning("Detector failed on %s: %s", label, exc)
            return
        self._preview.show(frame, detections)
        for object_class, confidence in detections:
            self._maybe_post(object_class, confidence, label)

    def _maybe_post(
        self,
        object_class: str,
        confidence: float,
        label: str,
    ) -> None:
        """Post one detection when the class cooldown allows it."""

        if not self._throttle.allow(object_class):
            return
        try:
            threat_event = self._client.post_threat_event(
                {
                    "object_class": object_class,
                    "confidence_score": round(confidence, 4),
                    "camera_id": self._settings.camera_id,
                    "status": DEFAULT_STATUS,
                }
            )
            self._client.post_system_log(
                {
                    "event_id": threat_event.get("event_id"),
                    "module": MODULE_NAME,
                    "message": (
                        f"Vision detected {object_class} "
                        f"(confidence={confidence:.2f}) in {label}"
                    ),
                }
            )
            logger.info(
                "Posted %s (%.2f) for camera %s from %s",
                object_class,
                confidence,
                self._settings.camera_id,
                label,
            )
        except (HeimdallAPIError, HeimdallAPIUnavailableError) as exc:
            logger.warning("Failed to post detection: %s", exc)

    def _fps_from_state(self, state: dict) -> float:
        """Return a positive fps from the camera row, or the default."""

        raw = state.get("fps", DEFAULT_FPS)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            return DEFAULT_FPS
        if value <= 0:
            return DEFAULT_FPS
        return value

    def _close_source(self) -> None:
        """Release the frame source and close any preview window."""

        if self._source.is_open:
            self._source.close()
        self._preview.close()
