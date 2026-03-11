"""
Configuration constants for PopUp Wellness Monitor.
Adjust these values to tune detection sensitivity and alert thresholds.
"""

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
CAMERA_INDEX: int = 0  # 0 = default webcam; increment for additional cameras

# ---------------------------------------------------------------------------
# Face measurement
# ---------------------------------------------------------------------------
# Average adult inter-pupillary distance in centimetres
INTERPUPILLARY_DISTANCE_CM: float = 6.3
# Estimated camera focal length in pixels (calibrate for your webcam if needed)
FOCAL_LENGTH: int = 600

# ---------------------------------------------------------------------------
# MediaPipe face-mesh landmark indices
# ---------------------------------------------------------------------------
LEFT_PUPIL: int = 145
RIGHT_PUPIL: int = 374
LEFT_EYE_TOP: int = 159
LEFT_EYE_BOTTOM: int = 23

# ---------------------------------------------------------------------------
# MediaPipe Tasks model
# ---------------------------------------------------------------------------
FACE_LANDMARKER_MODEL: str = "assets/face_landmarker.task"

# ---------------------------------------------------------------------------
# Distance thresholds (centimetres)
# ---------------------------------------------------------------------------
DISTANCE_TOO_CLOSE: int = 30  # Below this → danger zone, dim screen
DISTANCE_ZONE_CLOSE_MAX: int = 40  # < 40 cm  → zoom out
DISTANCE_ZONE_NEAR_MAX: int = 61  # 40–61 cm → neutral / zoom restore
# > 61 cm  → zoom in

# ---------------------------------------------------------------------------
# Zoom smoothing
# ---------------------------------------------------------------------------
# Hysteresis reduces flicker near zone boundaries; cooldown limits spam.
ZOOM_HYSTERESIS_CM: int = 4
ZOOM_COOLDOWN_MS: int = 1200
ZOOM_SMOOTHING_ALPHA: float = 0.2

# ---------------------------------------------------------------------------
# Blink detection
# ---------------------------------------------------------------------------
# Scaled vertical eye-opening ratio below which the eye is considered closed
BLINK_THRESHOLD: int = 1200
# Alert fires if no blink is detected for this long (milliseconds)
BLINK_ALERT_INTERVAL_MS: int = 20_000  # 20 seconds

# ---------------------------------------------------------------------------
# Break / 20-20-20 rule alert
# ---------------------------------------------------------------------------
# Every BREAK_ALERT_INTERVAL_MS ms remind the user to look away (20-20-20 rule)
BREAK_ALERT_INTERVAL_MS: int = 20 * 60 * 1_000  # 20 minutes

# ---------------------------------------------------------------------------
# Proximity-alert escalation
# ---------------------------------------------------------------------------
# Number of consecutive "too close" alerts before screen brightness is dimmed
PROXIMITY_ESCALATION_THRESHOLD: int = 5
BRIGHTNESS_DIMMED: int = 0  # Brightness level applied as a last resort (0–100)

# ---------------------------------------------------------------------------
# No-face auto-exit
# ---------------------------------------------------------------------------
# Exit gracefully after this many consecutive frames with no face detected
NO_FACE_EXIT_FRAMES: int = 500

# ---------------------------------------------------------------------------
# Nightlight mode (temperature / brightness)
# ---------------------------------------------------------------------------
NIGHTLIGHT_MODE: str = "temperature"  # "temperature" or "brightness"
NIGHTLIGHT_BRIGHTNESS: int = 25  # 0-100 brightness while nightlight is active
# Warmth is a 0.0-1.0 scale. Higher = warmer (less blue).
NIGHTLIGHT_WARMTH: float = 0.45
NIGHTLIGHT_POLL_SECONDS: int = 5
