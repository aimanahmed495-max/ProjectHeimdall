"""Shared fakes for vision unit tests. No network, model, or camera."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from vision_client import HeimdallAPIError, HeimdallAPIUnavailableError


class FakeDetector:
    """Return scripted detections for every frame."""

    def __init__(self, detections: Optional[List[Tuple[str, float]]] = None) -> None:
        self.detections = list(detections or [("person", 0.9)])
        self.calls = 0

    def detect(self, frame: Any) -> List[Tuple[str, float]]:
        self.calls += 1
        return list(self.detections)


class FakeFrameSource:
    """Count open/close and yield a fixed sequence of synthetic frames."""

    def __init__(
        self,
        frames: Optional[List[Tuple[str, Any]]] = None,
        fail_open: Optional[BaseException] = None,
    ) -> None:
        self._frames = list(frames or [("frame-1", object())])
        self._index = 0
        self._open = False
        self.fail_open = fail_open
        self.open_count = 0
        self.close_count = 0
        self.read_count = 0

    def open(self) -> None:
        if self.fail_open is not None:
            raise self.fail_open
        self._open = True
        self.open_count += 1
        self._index = 0

    def read(self) -> Optional[Tuple[str, Any]]:
        self.read_count += 1
        if not self._open or not self._frames:
            return None
        item = self._frames[self._index % len(self._frames)]
        self._index += 1
        return item

    def close(self) -> None:
        self._open = False
        self.close_count += 1

    @property
    def is_open(self) -> bool:
        return self._open


class FakeCapture:
    """Stand-in for ``cv2.VideoCapture``."""

    def __init__(self, frames: Optional[List[Any]] = None, opened: bool = True) -> None:
        self._frames = list(frames if frames is not None else [object(), object()])
        self._index = 0
        self._opened = opened
        self.release_calls = 0
        self.set_calls: List[Tuple[Any, Any]] = []

    def isOpened(self) -> bool:
        return self._opened

    def read(self):
        if self._index >= len(self._frames):
            return False, None
        frame = self._frames[self._index]
        self._index += 1
        return True, frame

    def set(self, prop_id: Any, value: Any) -> None:
        self.set_calls.append((prop_id, value))
        if prop_id == 1 and value == 0:
            self._index = 0

    def release(self) -> None:
        self.release_calls += 1
        self._opened = False


class FakeClient:
    """In-memory client. Fails the test on any camera-state write."""

    def __init__(self, states: Optional[List[Optional[Dict[str, Any]]]] = None) -> None:
        self._states = list(states or [])
        self.threat_events: List[Dict[str, Any]] = []
        self.system_logs: List[Dict[str, Any]] = []
        self.get_calls = 0
        self._next_event_id = 1
        self.raise_on_get: Optional[BaseException] = None

    def get_camera_state(self, camera_id: int) -> Optional[Dict[str, Any]]:
        self.get_calls += 1
        if self.raise_on_get is not None:
            raise self.raise_on_get
        if not self._states:
            return {
                "camera_id": camera_id,
                "mode": "Dormant",
                "fps": 5,
                "resolution": "720p",
            }
        return self._states.pop(0)

    def post_threat_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(event)
        payload["event_id"] = self._next_event_id
        self._next_event_id += 1
        self.threat_events.append(payload)
        return payload

    def post_system_log(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        payload = dict(log_entry)
        payload["log_id"] = len(self.system_logs) + 1
        self.system_logs.append(payload)
        return payload

    def post_camera_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raise AssertionError(f"vision must not write camera state: POST {state}")

    def set_camera_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        raise AssertionError(f"vision must not write camera state: PUT {state}")


class FakePreview:
    """Record preview show/close calls. No real display."""

    def __init__(self) -> None:
        self.shown: List[Tuple[Any, List[Tuple[str, float]]]] = []
        self.close_count = 0

    def show(self, frame: Any, detections: List[Tuple[str, float]]) -> None:
        self.shown.append((frame, list(detections)))

    def close(self) -> None:
        self.close_count += 1


class FakeCv2:
    """Minimal ``cv2`` stand-in for ``PreviewWindow`` unit tests."""

    FONT_HERSHEY_SIMPLEX = 0

    def __init__(self) -> None:
        self.imshow_calls: List[Tuple[str, Any]] = []
        self.put_text_calls: List[Tuple[Any, ...]] = []
        self.wait_key_calls: List[int] = []
        self.destroy_calls = 0
        self.imshow_error: Optional[BaseException] = None

    def putText(self, *args: Any) -> None:
        self.put_text_calls.append(args)

    def imshow(self, title: str, frame: Any) -> None:
        if self.imshow_error is not None:
            raise self.imshow_error
        self.imshow_calls.append((title, frame))

    def waitKey(self, delay: int) -> int:
        self.wait_key_calls.append(delay)
        return 0

    def destroyAllWindows(self) -> None:
        self.destroy_calls += 1


class FakeFrame:
    """Frame object with ``copy`` for annotation tests."""

    def __init__(self, tag: str = "frame") -> None:
        self.tag = tag
        self.copy_count = 0

    def copy(self) -> "FakeFrame":
        self.copy_count += 1
        return FakeFrame(tag=f"{self.tag}-copy")


def make_settings(**overrides):
    """Build a ``VisionSettings`` with test-friendly defaults."""

    from vision_settings import VisionSettings

    values = {
        "camera_id": 1,
        "frame_source": "0",
        "state_poll_seconds": 0.05,
        "event_cooldown_seconds": 30.0,
        "feature_pi_camera": False,
        "show_window": False,
        "active_fps": 60.0,
        "dormant_fps": 15.0,
    }
    values.update(overrides)
    return VisionSettings(**values)


# Re-export error types for convenience in tests.
__all__ = [
    "FakeCapture",
    "FakeClient",
    "FakeCv2",
    "FakeDetector",
    "FakeFrame",
    "FakeFrameSource",
    "FakePreview",
    "HeimdallAPIError",
    "HeimdallAPIUnavailableError",
    "make_settings",
]
