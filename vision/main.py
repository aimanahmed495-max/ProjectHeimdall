"""Run YOLOv8 detection against the Heimdall Core API."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from dotenv import load_dotenv

from detector import StaticImageSource, ThreatDetector
from vision_client import (
    HeimdallAPIError,
    HeimdallAPIUnavailableError,
    HeimdallVisionClient,
)


PACKAGE_DIR = Path(__file__).resolve().parent


class VisionPipelineApp:
    """Load test media, run YOLOv8, and post results to Heimdall."""

    CAMERA_ID = 1
    PLACEHOLDER_FPS = 5
    PLACEHOLDER_RESOLUTION = "720p"
    MODULE_NAME = "vision"
    DEFAULT_STATUS = "Pending"

    def __init__(self, package_dir: Path = PACKAGE_DIR) -> None:
        """Configure paths and load ``vision/.env`` if present.

        Args:
            package_dir: Directory that contains ``test_media/`` and
                optional ``.env``.
        """

        self._package_dir = package_dir
        load_dotenv(self._package_dir / ".env")
        self._client = HeimdallVisionClient()
        self._media_dir = self._package_dir / "test_media"

    def run(self) -> int:
        """Detect objects in test images and print a live summary.

        Returns:
            Process exit code: ``0`` on success or an empty media
            folder, ``1`` on a controlled failure such as a missing API.
        """

        print("Heimdall vision pipeline")
        print(f"API: {self._client.base_url}")
        print()

        source = StaticImageSource(self._media_dir)
        if not source.has_frames():
            print(
                "No test images found in vision/test_media/. "
                "Add .jpg or .png files and rerun. "
                "See vision/README.md."
            )
            return 0

        try:
            print("Loading YOLOv8n...")
            detector = ThreatDetector()
        except Exception as exc:
            print(f"Error loading YOLOv8 model: {exc}", file=sys.stderr)
            return 1

        active_state: Optional[Dict[str, Any]] = None
        try:
            active_state = self._set_camera_mode("Active")
            self._print_camera_state(active_state)
            print()

            posted, frame_count, failed = self._process_frames(
                source,
                detector,
            )
        except HeimdallAPIUnavailableError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        except HeimdallAPIError as exc:
            print(f"Error posting to Heimdall: {exc}", file=sys.stderr)
            return 1
        finally:
            if active_state is not None:
                try:
                    dormant_state = self._set_camera_mode("Dormant")
                    self._print_camera_state(dormant_state)
                    print()
                except HeimdallAPIError as exc:
                    print(
                        f"Error setting camera state to Dormant: {exc}",
                        file=sys.stderr,
                    )
                    return 1

        print(
            f"Done. Posted {posted} threat event(s) from {frame_count} "
            f"frame(s) to {self._client.base_url}."
        )
        if failed:
            print(f"{failed} detection(s) finished with errors.")
            return 1

        return 0

    def _process_frames(
        self,
        source: StaticImageSource,
        detector: ThreatDetector,
    ) -> Tuple[int, int, int]:
        """Run detection on every frame and post matching API records.

        Returns:
            A tuple of ``(posted_events, frame_count, failed_posts)``.
        """

        posted = 0
        failed = 0
        frame_count = 0

        for index, (label, frame) in enumerate(source.get_frames(), start=1):
            frame_count += 1
            detections = detector.detect(frame)
            print(f"{index}. Frame: {label}")

            if not detections:
                print("   Detection: (none)")
                print()
                continue

            for object_class, confidence in detections:
                print(
                    f"   Detection: {object_class} "
                    f"(confidence {confidence:.2f})"
                )
                try:
                    threat_event, system_log = self._post_detection(
                        object_class,
                        confidence,
                        label,
                    )
                except HeimdallAPIError as exc:
                    print("   Threat event: (not posted)")
                    print("   System log: (not posted)")
                    print(f"   Error: {exc}")
                    print()
                    failed += 1
                    continue

                print(
                    "   Threat event: "
                    f"id={threat_event.get('event_id')} "
                    f"status={threat_event.get('status')}"
                )
                print(f"   System log: id={system_log.get('log_id')}")
                print()
                posted += 1

        return posted, frame_count, failed

    def _post_detection(
        self,
        object_class: str,
        confidence: float,
        label: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Post one detection as a threat event and a system log."""

        threat_event = self._client.post_threat_event(
            {
                "object_class": object_class,
                "confidence_score": round(confidence, 4),
                "camera_id": self.CAMERA_ID,
                "status": self.DEFAULT_STATUS,
            }
        )
        system_log = self._client.post_system_log(
            {
                "event_id": threat_event.get("event_id"),
                "module": self.MODULE_NAME,
                "message": (
                    f"Vision detected {object_class} "
                    f"(confidence={confidence:.2f}) in {label}"
                ),
            }
        )
        return threat_event, system_log

    def _set_camera_mode(self, mode: str) -> Dict[str, Any]:
        """Post a camera-state record with placeholder fps and resolution."""

        return self._client.post_camera_state(
            {
                "camera_id": self.CAMERA_ID,
                "mode": mode,
                "fps": self.PLACEHOLDER_FPS,
                "resolution": self.PLACEHOLDER_RESOLUTION,
            }
        )

    def _print_camera_state(self, state: Dict[str, Any]) -> None:
        """Print a one-line camera-state summary."""

        print(
            f"Camera state: {state.get('mode')} "
            f"(id={state.get('state_id')}, "
            f"fps={state.get('fps')}, "
            f"resolution={state.get('resolution')})"
        )


def main() -> int:
    """Entrypoint used by ``python main.py``."""

    return VisionPipelineApp().run()


if __name__ == "__main__":
    sys.exit(main())
