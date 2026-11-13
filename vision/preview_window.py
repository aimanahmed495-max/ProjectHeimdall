"""Optional OpenCV preview window for local demos."""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Tuple

logger = logging.getLogger(__name__)

WINDOW_TITLE = "Heimdall camera feed"
_TEXT_ORIGIN_X = 10
_TEXT_ORIGIN_Y = 24
_LINE_HEIGHT = 24
_FONT_SCALE = 0.6
_THICKNESS = 2
_COLOR_BGR = (0, 255, 0)


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
        detections: List[Tuple[str, float]],
    ) -> None:
        """Draw labels on ``frame`` and display it for one waitKey tick.

        Args:
            frame: Image array from the frame source. Must support ``copy``.
            detections: ``(object_class, confidence)`` pairs to annotate.
        """

        if not self._enabled or self._unavailable:
            return
        try:
            cv2 = self._require_backend()
            annotated = frame.copy()
            self._draw_labels(cv2, annotated, detections)
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

    @staticmethod
    def _draw_labels(
        cv2: Any,
        frame: Any,
        detections: List[Tuple[str, float]],
    ) -> None:
        """Write class name and confidence lines onto ``frame``."""

        y = _TEXT_ORIGIN_Y
        for object_class, confidence in detections:
            text = f"{object_class} {confidence:.2f}"
            cv2.putText(
                frame,
                text,
                (_TEXT_ORIGIN_X, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                _FONT_SCALE,
                _COLOR_BGR,
                _THICKNESS,
            )
            y += _LINE_HEIGHT


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
