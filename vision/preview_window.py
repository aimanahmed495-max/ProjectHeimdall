"""Optional OpenCV preview window for local demos."""

from __future__ import annotations

import logging
from typing import Any, Optional, Sequence, Tuple

from detector import Detection

logger = logging.getLogger(__name__)

WINDOW_TITLE = "Heimdall camera feed"
_FONT_SCALE = 0.6
_THICKNESS = 2
_LABEL_OFFSET_Y = 6

# BGR colors for confidence bands.
_COLOR_GREEN = (0, 255, 0)
_COLOR_YELLOW = (0, 255, 255)
_COLOR_RED = (0, 0, 255)
_HIGH_CONFIDENCE = 0.80
_MID_CONFIDENCE = 0.65


class PreviewWindow:
    """Show annotated frames when enabled, or no-op when off / unavailable."""

    def __init__(
        self,
        enabled: bool = False,
        title: str = WINDOW_TITLE,
        backend: Any = None,
    ) -> None:
        """Create a preview that only opens a window when ``enabled``.

        Args:
            enabled: When False, ``show`` and ``close`` are no-ops.
            title: ``cv2.imshow`` window title.
            backend: Optional stand-in for ``cv2``. Tests inject a fake.
        """

        self._enabled = enabled
        self._title = title
        self._backend = backend
        self._visible = False
        self._unavailable = False

    def show(
        self,
        frame: Any,
        detections: Sequence[Detection],
    ) -> None:
        """Draw boxes and labels on ``frame`` and display for one waitKey.

        Args:
            frame: Image array from the frame source. Must support ``copy``.
            detections: ``(class, confidence, x1, y1, x2, y2)`` tuples.
        """

        if not self._enabled or self._unavailable:
            return
        try:
            cv2 = self._require_backend()
            annotated = frame.copy()
            self._draw_detections(cv2, annotated, detections)
            cv2.imshow(self._title, annotated)
            cv2.waitKey(1)
            self._visible = True
        except Exception as exc:  # noqa: BLE001 - keep the runner alive
            self._unavailable = True
            self._visible = False
            logger.warning(
                "Preview window unavailable; continuing without display: %s",
                exc,
            )

    def close(self) -> None:
        """Destroy the OpenCV window when one was shown."""

        if not self._visible:
            return
        try:
            cv2 = self._require_backend()
            cv2.destroyAllWindows()
        except Exception as exc:  # noqa: BLE001 - teardown must not raise
            logger.warning("Failed to close preview window: %s", exc)
        finally:
            self._visible = False

    def _require_backend(self) -> Any:
        """Return the injected backend, or import ``cv2`` once."""

        if self._backend is not None:
            return self._backend
        import cv2

        self._backend = cv2
        return cv2

    @classmethod
    def _draw_detections(
        cls,
        cv2: Any,
        frame: Any,
        detections: Sequence[Detection],
    ) -> None:
        """Draw a confidence-colored box and label for each detection."""

        for object_class, confidence, x1, y1, x2, y2 in detections:
            color = cls._color_for_confidence(confidence)
            top_left = (int(x1), int(y1))
            bottom_right = (int(x2), int(y2))
            cv2.rectangle(frame, top_left, bottom_right, color, _THICKNESS)
            text = f"{object_class} {confidence:.2f}"
            text_origin = (int(x1), max(int(y1) - _LABEL_OFFSET_Y, 0))
            cv2.putText(
                frame,
                text,
                text_origin,
                cv2.FONT_HERSHEY_SIMPLEX,
                _FONT_SCALE,
                color,
                _THICKNESS,
            )

    @staticmethod
    def _color_for_confidence(confidence: float) -> Tuple[int, int, int]:
        """Return BGR color for a confidence score."""

        if confidence >= _HIGH_CONFIDENCE:
            return _COLOR_GREEN
        if confidence >= _MID_CONFIDENCE:
            return _COLOR_YELLOW
        return _COLOR_RED


def build_preview_window(
    enabled: bool,
    backend: Optional[Any] = None,
) -> PreviewWindow:
    """Build a preview window for the runner.

    Args:
        enabled: Whether ``VISION_SHOW_WINDOW`` is on.
        backend: Optional ``cv2`` stand-in for tests.

    Returns:
        A ``PreviewWindow`` instance.
    """

    return PreviewWindow(enabled=enabled, backend=backend)
