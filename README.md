# PopUp Wellness Monitor

A real-time desktop eye-strain monitor that uses your webcam and computer vision to enforce healthy screen habits — no cloud, no tracking, everything runs locally.

---

## What it does

| Feature | Detail |
|---|---|
| **Distance alert** | Warns you when your face is closer than 30 cm to the screen; dims brightness after repeated violations |
| **Blink reminder** | Fires an alert if no blink is detected for 20 seconds |
| **20-20-20 break rule** | Reminds you every 20 minutes to look at something 6 m away for 20 seconds |
| **Auto zoom adjust** | Adjusts the active window zoom (Ctrl +/−) as you move closer or farther from the screen |

---

## Project structure

```
popup/
├── src/
│   ├── __init__.py
│   ├── config.py          # All tunable constants
│   ├── face_mesh.py       # MediaPipe Tasks wrapper
│   ├── zoom_control.py    # Distance-based zoom logic
│   └── monitor.py         # Core monitoring loop
├── assets/
│   └── face_landmarker.task
├── tests/
│   ├── test_config.py
│   ├── test_zoom_control.py
│   └── test_monitor.py
├── main.py                # Entry point
├── nightlight.py          # Nightlight mode (brightness dim)
├── requirements.txt
├── environment.yml        # Conda environment
├── Dockerfile
└── .dockerignore
```

---

## Requirements

- Python 3.13+
- MediaPipe Tasks face landmarker model file
- A connected webcam
- A desktop environment (X11 / Windows / macOS) — alerts use native dialog boxes

---

## Setup

### Option 1 — pip

```bash
pip install -r requirements.txt
python main.py
```

Nightlight-only mode:

```bash
python nightlight.py
```

Nightlight temperature mode uses OS gamma controls (Windows, Linux via xrandr).
On macOS it falls back to brightness dimming.

### Option 2 — Conda

```bash
source /opt/conda/etc/profile.d/conda.sh
conda activate popup-wellness-monitor
conda env update -f environment.yml
python main.py

```

### Model file (required)

Download the MediaPipe Face Landmarker task file and place it at:

```
assets/face_landmarker.task
```

You can also point `FACE_LANDMARKER_MODEL` in [src/config.py](src/config.py)
to an absolute path if you prefer to store the model elsewhere.

### Option 3 — Docker (Linux, Windows, macOS notes)

Docker support depends on OS and how the webcam is exposed to the container.
Linux is straightforward. Windows requires WSL2 + USB camera passthrough.
macOS generally cannot pass a webcam into Docker, so use the native run.

```bash
# Build
docker build -t popup-wellness-monitor .

# Run (pass webcam device and X11 socket)
docker run --rm \
  --device /dev/video0 \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  popup-wellness-monitor
```

Windows (Docker Desktop + WSL2 + camera passthrough):

1. Install `usbipd-win` on Windows and ensure WSL2 is enabled.
2. Attach the camera to WSL2 (example commands on Windows):
   `usbipd list`
   `usbipd bind --busid <BUSID>`
   `usbipd attach --wsl --busid <BUSID>`
3. In your WSL2 shell, confirm the device appears as `/dev/video0`.
4. Run the Linux Docker command from inside WSL2.

PowerShell example (requires WSL2 and a Linux Docker context):

```powershell
docker run --rm `
  --device /dev/video0 `
  -e DISPLAY=$env:DISPLAY `
  -v /tmp/.X11-unix:/tmp/.X11-unix `
  popup-wellness-monitor
```

macOS:
Docker Desktop for macOS does not expose the webcam as `/dev/video0`.
Run the app natively with pip/conda instead.

---

## Configuration

All thresholds live in [src/config.py](src/config.py) — no magic numbers elsewhere.

| Constant | Default | Description |
|---|---|---|
| `CAMERA_INDEX` | `0` | Webcam index (increment for additional cameras) |
| `DISTANCE_TOO_CLOSE` | `30` cm | Danger-zone threshold |
| `BLINK_ALERT_INTERVAL_MS` | `20 000` ms | Alert if no blink within this window |
| `BREAK_ALERT_INTERVAL_MS` | `1 200 000` ms | 20-minute break reminder |
| `PROXIMITY_ESCALATION_THRESHOLD` | `5` | Alerts before screen is dimmed |

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

---

## How it works

1. OpenCV captures frames from your webcam.
2. MediaPipe Tasks Face Landmarker fits a 468-point face mesh to each frame.
3. The inter-pupillary pixel width is used with a known average IPD and focal length to estimate distance.
4. Eye-opening height at the eyelid landmarks is used to detect blinks.
5. `pyautogui` raises native alert dialogs; `screen-brightness-control` adjusts display brightness.
