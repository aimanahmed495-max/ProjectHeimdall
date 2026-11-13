"""Run the Heimdall vision module as a long-lived, trigger-driven process."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from dotenv import load_dotenv

from detector import ThreatDetector
from frame_sources import build_frame_source
from vision_client import HeimdallAPIError, HeimdallVisionClient
from vision_runner import VisionRunner
from vision_settings import load_settings

PACKAGE_DIR = Path(__file__).resolve().parent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    """Load settings, wire dependencies, and run the vision loop.

    Returns:
        Process exit code from ``VisionRunner.run``.
    """

    load_dotenv(PACKAGE_DIR / ".env")
    settings = load_settings()
    client = HeimdallVisionClient()

    print("Heimdall vision runner")
    print(f"API: {client.base_url}")
    print(f"Camera id: {settings.camera_id}")
    print(f"Frame source: {settings.frame_source}")
    print(f"FEATURE_PI_CAMERA: {settings.feature_pi_camera}")
    print(f"VISION_SHOW_WINDOW: {settings.show_window}")
    print()

    try:
        client.authenticate()
    except HeimdallAPIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Authentication: successful")
    print("Waiting for camera Active (OSINT corroboration or console)...")
    print()

    try:
        detector = ThreatDetector()
    except Exception as exc:  # noqa: BLE001 - model load can raise many types
        print(f"Error loading YOLOv8 model: {exc}", file=sys.stderr)
        return 1

    source = build_frame_source(settings)
    runner = VisionRunner(client, detector, source, settings)
    return runner.run()


if __name__ == "__main__":
    sys.exit(main())
