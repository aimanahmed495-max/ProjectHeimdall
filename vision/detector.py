"""YOLOv8 threat detector."""

from __future__ import annotations

from typing import Any, List, Tuple


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

        from ultralytics import YOLO

        self._confidence_threshold = confidence_threshold
        self._model = YOLO(model_path)

    def detect(self, frame: Any) -> List[Tuple[str, float]]:
        """Detect objects in one BGR frame.

        Args:
            frame: Image array in OpenCV BGR format.

        Returns:
            A list of ``(object_class, confidence_score)`` tuples for
            detections at or above the configured threshold. Class names
            are the raw COCO labels from YOLO.
        """

        results = self._model(frame, verbose=False)
        detections: List[Tuple[str, float]] = []

        for result in results:
            if result.boxes is None:
                continue
            self._append_boxes(result, detections)

        return detections

    def _append_boxes(
        self,
        result: Any,
        detections: List[Tuple[str, float]],
    ) -> None:
        """Keep boxes from one result that meet the confidence threshold."""

        names = result.names
        for box in result.boxes:
            confidence = float(box.conf[0])
            if confidence < self._confidence_threshold:
                continue
            class_id = int(box.cls[0])
            object_class = str(names[class_id])
            detections.append((object_class, confidence))
