# Heimdall Vision Pipeline

Long-running YOLOv8 detector that captures frames only while the Heimdall
camera row is `Active`. OSINT corroboration (or an operator in the console)
sets that mode. Vision never writes `/camera-states`.

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

| Variable | Default | Meaning |
| --- | --- | --- |
| `BASE_URL` | `http://localhost:8000` | Heimdall API origin |
| `VISION_API_USERNAME` | (required) | Registered Heimdall user |
| `VISION_API_PASSWORD` | (required) | Password for that user |
| `FEATURE_PI_CAMERA` | `false` | `1` / `true` / `yes` / `on` selects the Pi placeholder (refuses until T18) |
| `VISION_CAMERA_ID` | `1` | Camera row to poll and attach to threat events |
| `VISION_FRAME_SOURCE` | `0` | Webcam index (digits), video file path, or image directory |
| `VISION_STATE_POLL_SECONDS` | `2` | How often to re-check camera mode while Active (and on poll errors) |
| `VISION_EVENT_COOLDOWN_SECONDS` | `30` | Minimum gap between two posts of the same class |
| `VISION_ACTIVE_FPS` | `60` | Frame pace while the camera row is Active |
| `VISION_DORMANT_FPS` | `15` | How often to re-poll camera state while Dormant (15 Hz) |
| `VISION_SHOW_WINDOW` | `false` | `1` / `true` / `yes` / `on` opens an OpenCV preview titled "Heimdall camera feed" while Active (demo only) |

The credentials must match an active account created through `POST /auth/register`.
The `.env` file is ignored by Git and must not be committed.

With `VISION_SHOW_WINDOW` on, each Active frame is shown in a local OpenCV
window with bounding boxes and class/confidence labels. Box color follows
confidence: green (≥ 0.80), yellow (≥ 0.65), red (below 0.65). The window
closes when the camera goes Dormant, the frame source is released, or the
runner stops. If no display is available, vision logs a warning and continues.

## Trigger model

1. Seed or the console registers camera `VISION_CAMERA_ID`.
2. Live OSINT corroboration (or an operator) sets that camera to `Active`.
3. Vision polls `GET /camera-states/{id}`. While `Active`, it opens the frame
   source at `VISION_ACTIVE_FPS` (default 60), runs YOLOv8n, and posts threat
   events (raw COCO class names) plus system logs. While `Dormant`, it releases
   the source and re-polls at `VISION_DORMANT_FPS` (default 15 Hz). Missing
   camera rows (404) still wait `VISION_STATE_POLL_SECONDS`.
4. Nothing in vision returns the camera to `Dormant`. Use the console or
   `scripts/demo_reset.sh` after a demo.

**Seed note:** `backend/app/seed.py` leaves camera 1 `Active`. Set it `Dormant`
before a demo if you want the webcam off until corroboration.

## Frame sources

- Digits (`0`, `1`, …): OpenCV webcam index. macOS prompts for camera permission
  the first time OpenCV opens the device.
- File path: video file via OpenCV. The file loops while the camera stays Active.
- Directory path: still images (`.jpg`, `.png`, and similar), looping while Active.
- `FEATURE_PI_CAMERA=on`: `PiCameraSource` placeholder. `open()` fails with a
  clear T18 message until the Pi stream lands.

Frames stay in memory. Only class name, confidence, and camera id are posted.

## Run

```bash
cd vision
python main.py
```

Leave the process running. Trigger corroboration with the live OSINT demo feed
(see `ai-brain/README.md`), or set the camera Active in the console. Detections
appear as `Pending` threat events with `camera_id` set and no `source_id`.

## Tests

```bash
# from the repository root; no camera, YOLO, or network required
pytest vision/tests -q
```

`scripts/check` runs the same suite with the OSINT virtualenv.
