# Heimdall Vision Pipeline

Prototype YOLOv8 detector that turns still frames into Heimdall threat events.

The pipeline reads images from `test_media/`, runs YOLOv8n, and posts camera state, threat events, and system logs to the existing FastAPI backend at `http://localhost:8000`. There is no physical camera yet. Frames come from a `FrameSource` interface, so a live Raspberry Pi camera later only needs a new `LiveCameraSource` that implements `get_frames()` — detection and API posting stay unchanged.

## Requirements

- Python 3.10+
- A running Heimdall Core API at `http://localhost:8000` (see `backend/README.md`)

The first run downloads `yolov8n.pt` from Ultralytics.

## Install

From the repository root:

```bash
cd vision
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment

```bash
cp .env.example .env
```

`.env` defaults to:

```text
BASE_URL=http://localhost:8000
```

## Test media

Put still images in `vision/test_media/`. Supported extensions: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, `.tiff`.

A short pre-recorded clip can be added later with another `FrameSource` implementation. Do not commit large media files.

If the folder is empty, `python main.py` prints a clear message and exits without crashing.

## Run

Make sure the API is up, then from `vision/`:

```bash
python main.py
```

The process marks camera 1 as `Active`, prints each frame and detection, posts matching threat events and system logs, then marks the camera `Dormant`. If the backend is not running, it exits with a clear error instead of crashing.
