"""YOLOv8 threat detector."""

from __future__ import annotations

from typing import Any, List, Tuple

# (object_class, confidence, x1, y1, x2, y2) in pixel coordinates.
Detection = Tuple[str, float, float, float, float, float]


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

    def detect(self, frame: Any) -> List[Detection]:
        """Detect objects in one BGR frame.

        Args:
            frame: Image array in OpenCV BGR format.

        Returns:
            A list of ``(object_class, confidence, x1, y1, x2, y2)``
            tuples for detections at or above the configured threshold.
            Class names are the raw COCO labels from YOLO. Box corners
            are pixel coordinates from the YOLO ``xyxy`` tensor.
        """

        results = self._model(frame, verbose=False)
        detections: List[Detection] = []

        for result in results:
            if result.boxes is None:
                continue
            self._append_boxes(result, detections)

        return detections

    def _append_boxes(
        self,
        result: Any,
        detections: List[Detection],
    ) -> None:
        """Keep boxes from one result that meet the confidence threshold."""

        names = result.names
        for box in result.boxes:
            confidence = float(box.conf[0])
            if confidence < self._confidence_threshold:
                continue
            class_id = int(box.cls[0])
            object_class = str(names[class_id])
            x1, y1, x2, y2 = (float(value) for value in box.xyxy[0])
            detections.append((object_class, confidence, x1, y1, x2, y2))
