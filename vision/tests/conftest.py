"""Put ``vision/`` on ``sys.path`` so tests import modules like production."""

import sys
from pathlib import Path

VISION_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VISION_DIR))
