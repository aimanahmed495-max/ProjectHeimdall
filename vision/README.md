# Heimdall Vision Pipeline

Prototype YOLOv8 detector that turns still frames into Heimdall threat events.

The pipeline reads images from `test_media/`, runs YOLOv8n, and posts camera states, threat events, and system logs to the existing FastAPI backend at `http://localhost:8000`. There is no physical camera yet. Frames come from a `FrameSource` interface, so a live Raspberry Pi camera later only needs a new `LiveCameraSource` that implements `get_frames()`—detection and API posting stay unchanged.

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

Create the private vision environment file:

```bash
cp .env.example .env
```

Configure the API address and credentials for a registered Heimdall user:

```text
BASE_URL=http://localhost:8000
VISION_API_USERNAME=replace_with_vision_username
VISION_API_PASSWORD=replace_with_vision_password
```

The credentials must match an active account created through `POST /auth/register`. The `.env` file is ignored by Git and must not be committed.

Before sending camera states, threat events, or system logs, the vision client logs in through `POST /auth/login` and attaches the returned bearer token to protected requests.

## Test media

Put still images in `vision/test_media/`. Supported extensions are `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`, `.tif`, and `.tiff`.

A short prerecorded clip can be added later with another `FrameSource` implementation. Do not commit large media files.

If the folder is empty, `python main.py` prints a clear message and exits without crashing.

## Run

Make sure the API is running and the configured vision account exists. Then, from `vision/`, run:

```bash
python main.py
```

The pipeline:

1. Authenticates through `POST /auth/login`.
2. Marks camera 1 as `Active`.
3. Runs object detection on each test image.
4. Posts matching threat events and system logs.
5. Marks camera 1 as `Dormant`.

If authentication fails or the backend is unavailable, the pipeline prints a clear error and exits safely.

## Camera-state integration

The vision pipeline registers a missing camera through `POST /camera-states`. After registration, it updates the same camera record through `PUT /camera-states/{camera_id}` when switching between `Active` and `Dormant`.

Repeated pipeline runs update one existing camera row instead of creating duplicate camera-state records.