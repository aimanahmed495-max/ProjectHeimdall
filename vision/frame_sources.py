"""Frame sources with an explicit open / read / close lifecycle."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Callable, List, Optional, Tuple

from vision_settings import VisionSettings

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {
    ".bmp",
    ".jpeg",
    ".jpg",
    ".png",
    ".tif",
    ".tiff",
    ".webp",
}

PI_CAMERA_MESSAGE = (
    "Pi camera streaming is not implemented yet (task T18). "
    "Leave FEATURE_PI_CAMERA off and use VISION_FRAME_SOURCE for "
    "a webcam index, video file, or image directory."
)


class FrameSource(ABC):
    """Camera-agnostic source of labeled frames.

    A live camera must be released when the trigger ends, so sources
    expose ``open`` / ``read`` / ``close`` instead of a one-shot generator.
    """

    @abstractmethod
    def open(self) -> None:
        """Acquire the underlying capture or media."""

    @abstractmethod
    def read(self) -> Optional[Tuple[str, Any]]:
        """Return the next ``(label, frame)`` pair, or ``None``."""

    @abstractmethod
    def close(self) -> None:
        """Release the underlying capture or media."""

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Return True while the source holds an open resource."""


class StaticImageSource(FrameSource):
    """Read still images from a directory as sequential frames."""

    def __init__(self, media_dir: Path) -> None:
        """Create a source that scans ``media_dir`` for image files.

        Args:
            media_dir: Folder containing images. Non-image files are ignored.
        """

        self._media_dir = media_dir
        self._paths: List[Path] = []
        self._index = 0
        self._open = False

    def open(self) -> None:
        """Scan the directory and reset the read cursor."""

        self._paths = self._image_paths()
        self._index = 0
        self._open = True
        if not self._paths:
            logger.warning("No images found in %s", self._media_dir)

    def read(self) -> Optional[Tuple[str, Any]]:
        """Return the next image, looping from the start when exhausted.

        Returns:
            ``(filename, frame)`` or ``None`` when closed or empty.
        """

        if not self._open or not self._paths:
            return None

        path = self._paths[self._index % len(self._paths)]
        self._index += 1
        return self._load_image(path)

    def close(self) -> None:
        """Drop the scanned path list."""

        self._paths = []
        self._index = 0
        self._open = False

    @property
    def is_open(self) -> bool:
        """Return True after a successful ``open``."""

        return self._open

    def _image_paths(self) -> List[Path]:
        """Return sorted image paths in the media directory."""

        if not self._media_dir.is_dir():
            return []
        paths = [
            path
            for path in self._media_dir.iterdir()
            if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
        ]
        return sorted(paths)

    def _load_image(self, path: Path) -> Optional[Tuple[str, Any]]:
        """Load one image through OpenCV, skipping unreadable files."""

        import cv2

        frame = cv2.imread(str(path))
        if frame is None:
            logger.warning("Skipping unreadable image: %s", path.name)
            return None
        return path.name, frame


class VideoCaptureSource(FrameSource):
    """Read frames from a webcam index or a video file via OpenCV."""

    def __init__(
        self,
        target: str,
        capture_factory: Optional[Callable[[Any], Any]] = None,
    ) -> None:
        """Create a VideoCapture-backed source.

        Args:
            target: Webcam index as digits (for example ``0``), or a
                filesystem path to a video file.
            capture_factory: Optional factory for tests. Defaults to
                ``cv2.VideoCapture``.
        """

        self._target = target
        self._capture_factory = capture_factory or self._default_factory
        self._capture: Any = None
        self._is_file = not target.isdigit()
        self._frame_index = 0

    def open(self) -> None:
        """Open the webcam or video file.

        Raises:
            RuntimeError: The capture could not be opened.
        """

        if self._capture is not None:
            return
        opened = self._capture_factory(self._capture_target())
        if opened is None or not opened.isOpened():
            if opened is not None:
                opened.release()
            raise RuntimeError(
                f"Could not open frame source {self._target!r}. "
                "Check VISION_FRAME_SOURCE and camera permissions."
            )
        self._capture = opened
        self._frame_index = 0

    def read(self) -> Optional[Tuple[str, Any]]:
        """Return the next frame, looping a video file at end-of-file.

        Returns:
            ``(label, frame)`` or ``None`` when closed or temporarily empty.
        """

        if self._capture is None:
            return None
        ok, frame = self._capture.read()
        if not ok:
            return self._handle_read_miss()
        self._frame_index += 1
        return f"frame-{self._frame_index}", frame

    def close(self) -> None:
        """Release the OpenCV capture."""

        if self._capture is None:
            return
        self._capture.release()
        self._capture = None

    @property
    def is_open(self) -> bool:
        """Return True while a capture handle is held."""

        return self._capture is not None

    def _capture_target(self) -> Any:
        """Return an int webcam index or the path string for a file."""

        if self._target.isdigit():
            return int(self._target)
        return self._target

    def _handle_read_miss(self) -> Optional[Tuple[str, Any]]:
        """Loop a file source; return None for a live camera miss."""

        if not self._is_file:
            return None
        # CAP_PROP_POS_FRAMES == 1; avoid importing cv2 just for the constant.
        self._capture.set(1, 0)
        ok, frame = self._capture.read()
        if not ok:
            return None
        self._frame_index += 1
        return f"frame-{self._frame_index}", frame

    @staticmethod
    def _default_factory(target: Any) -> Any:
        """Import OpenCV lazily and open ``target``."""

        import cv2

        return cv2.VideoCapture(target)


class PiCameraSource(FrameSource):
    """Placeholder until the Raspberry Pi stream lands in T18."""

    def open(self) -> None:
        """Refuse to start; Pi streaming is task T18.

        Raises:
            RuntimeError: Always, with a pointer to T18.
        """

        raise RuntimeError(PI_CAMERA_MESSAGE)

    def read(self) -> Optional[Tuple[str, Any]]:
        """Return None; the placeholder never yields frames."""

        return None

    def close(self) -> None:
        """No-op; nothing was acquired."""

    @property
    def is_open(self) -> bool:
        """Return False; open always fails."""

        return False


def build_frame_source(settings: VisionSettings) -> FrameSource:
    """Choose a frame source from settings and feature flags.

    Args:
        settings: Resolved vision settings.

    Returns:
        A ``PiCameraSource`` when the flag is on, otherwise a webcam,
        video file, or static image directory source.
    """

    if settings.feature_pi_camera:
        return PiCameraSource()
    target = settings.frame_source
    path = Path(target)
    if path.is_dir():
        return StaticImageSource(path)
    return VideoCaptureSource(target)
