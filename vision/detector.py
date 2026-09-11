"""YOLOv8 threat detector and camera-agnostic frame sources."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator, List, Tuple

import cv2
import numpy as np
from ultralytics import YOLO


class FrameSource(ABC):
    """Camera-agnostic source of BGR video frames.

    Detection code depends only on this interface. A live Raspberry Pi
    camera can be added later as another subclass without changing
    :class:`ThreatDetector`.
    """

    @abstractmethod
    def has_frames(self) -> bool:
        """Return True if this source can produce at least one frame."""

    @abstractmethod
    def get_frames(self) -> Iterator[Tuple[str, np.ndarray]]:
        """Yield ``(label, frame)`` pairs until the source is exhausted.

        ``label`` is a human-readable identifier such as a filename or
        a camera frame index. ``frame`` is a BGR ``ndarray``.
        """


class StaticImageSource(FrameSource):
    """Read still images from a directory as sequential frames."""

    IMAGE_EXTENSIONS = {
        ".bmp",
        ".jpeg",
        ".jpg",
        ".png",
        ".tif",
        ".tiff",
        ".webp",
    }

    def __init__(self, media_dir: Path) -> None:
        """Create a source that scans ``media_dir`` for image files.

        Args:
            media_dir: Folder containing test images. Non-image files
                such as ``.gitkeep`` are ignored.
        """

        self._media_dir = media_dir

    def has_frames(self) -> bool:
        """Return True if at least one readable image path exists."""

        return bool(self._image_paths())

    def get_frames(self) -> Iterator[Tuple[str, np.ndarray]]:
        """Yield each image in the folder as a labeled BGR frame.

        Unreadable files are skipped rather than raising, so a mixed
        folder does not abort the pipeline.
        """

        for path in self._image_paths():
            frame = cv2.imread(str(path))
            if frame is None:
                print(f"Skipping unreadable image: {path.name}")
                continue
            yield path.name, frame

    def _image_paths(self) -> List[Path]:
        """Return sorted image paths in the media directory."""

        if not self._media_dir.is_dir():
            return []

        paths = [
            path
            for path in self._media_dir.iterdir()
            if path.is_file()
            and path.suffix.lower() in self.IMAGE_EXTENSIONS
        ]
        return sorted(paths)


class ThreatDetector:
    """Run YOLOv8 on a single frame and return high-confidence detections."""

    def __init__(
        self,
        model_path: str = "yolov8n.pt",
        confidence_threshold: float = 0.5,
    ) -> None:
        """Load YOLOv8 weights used for object detection.

        Args:
            model_path: Ultralytics weights file. ``yolov8n.pt`` is
                downloaded automatically on first use.
            confidence_threshold: Minimum score in ``[0, 1]`` required
                to keep a detection. Defaults to ``0.5``.
        """

        self._confidence_threshold = confidence_threshold
        self._model = YOLO(model_path)

    def detect(self, frame: np.ndarray) -> List[Tuple[str, float]]:
        """Detect objects in one BGR frame.

        Args:
            frame: Image array in OpenCV BGR format.

        Returns:
            A list of ``(object_class, confidence_score)`` tuples for
            detections at or above the configured threshold.
        """

        results = self._model(frame, verbose=False)
        detections: List[Tuple[str, float]] = []

        for result in results:
            if result.boxes is None:
                continue

            names = result.names
            for box in result.boxes:
                confidence = float(box.conf[0])
                if confidence < self._confidence_threshold:
                    continue

                class_id = int(box.cls[0])
                object_class = str(names[class_id])
                detections.append((object_class, confidence))

        return detections
