# ---------------------------------------------------------------------------
# PopUp Wellness Monitor — Dockerfile
#
# NOTE: This application requires:
#   - A connected webcam    → pass --device /dev/video0
#   - A running X11 display → set DISPLAY env var and share the X socket
#
# Build:
#   docker build -t popup-wellness-monitor .
#
# Run (Linux with X11):
#   docker run --rm \
#     --device /dev/video0 \
#     -e DISPLAY=$DISPLAY \
#     -v /tmp/.X11-unix:/tmp/.X11-unix \
#     popup-wellness-monitor
# ---------------------------------------------------------------------------

FROM python:3.13-slim

# System libraries required by OpenCV, Tkinter (pyautogui), and display
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxrandr2 \
    libx11-6 \
    x11-xserver-utils \
    python3-tk \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies first (layer-cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

CMD ["python", "main.py"]
