"""
Core monitoring loop for PopUp Wellness Monitor.

Responsibilities:
- Capture webcam frames and run MediaPipe face-mesh detection.
- Estimate face-to-screen distance from inter-pupillary pixel width.
- Detect blink rate and fire alerts when blinking stops.
- Apply 20-20-20 rule: remind user to look away every 20 minutes.
- Escalate proximity alerts and dim screen brightness if user is too close.
- Auto-exit after a sustained period with no face detected.
"""

import time

import cv2
import pyautogui as pag
import screen_brightness_control as sbc

from .config import (
    BLINK_ALERT_INTERVAL_MS,
    BLINK_THRESHOLD,
    BREAK_ALERT_INTERVAL_MS,
    BRIGHTNESS_DIMMED,
    CAMERA_INDEX,
    DISTANCE_TOO_CLOSE,
    FOCAL_LENGTH,
    INTERPUPILLARY_DISTANCE_CM,
    LEFT_EYE_BOTTOM,
    LEFT_EYE_TOP,
    LEFT_PUPIL,
    NO_FACE_EXIT_FRAMES,
    PROXIMITY_ESCALATION_THRESHOLD,
    RIGHT_PUPIL,
)
from .face_mesh import FaceMeshDetector
from .zoom_control import ZoomController


def _ms() -> float:
    """Return current time in milliseconds."""
    return time.monotonic() * 1_000.0


class EyeStrainMonitor:
    """
    Real-time eye-strain monitor.

    Usage::

        monitor = EyeStrainMonitor()
        monitor.run()
    """

    def __init__(self) -> None:
        self._cap = cv2.VideoCapture(CAMERA_INDEX)
        self._detector = FaceMeshDetector()
        self._zoom = ZoomController()

        now = _ms()
        self._break_timer: float = now
        self._blink_timer: float = now

        self._no_face_frames: int = 0
        self._proximity_alert_count: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the blocking monitoring loop."""
        try:
            while self._tick():
                cv2.waitKey(1)
        finally:
            self._shutdown()

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def _tick(self) -> bool:
        """Process a single frame. Returns False when the loop should stop."""
        success, frame = self._cap.read()
        if not success:
            return True  # Transient read failure — keep trying

        frame, faces = self._detector.findFaceMesh(frame, draw=False)
        now = _ms()

        self._check_break_alert(now)

        if faces:
            self._no_face_frames = 0
            self._process_face(faces[0], now)
        else:
            self._no_face_frames += 1
            if self._no_face_frames >= NO_FACE_EXIT_FRAMES:
                return False  # No face detected for too long — exit cleanly

        return True

    # ------------------------------------------------------------------
    # Face processing
    # ------------------------------------------------------------------

    def _process_face(self, face: list, now: float) -> None:
        distance_cm = self._estimate_distance(face)
        self._check_blink(face, now)

        if distance_cm < DISTANCE_TOO_CLOSE:
            self._handle_too_close()
        else:
            self._proximity_alert_count = 0
            self._zoom.update(int(distance_cm))

    def _estimate_distance(self, face: list) -> float:
        """Use inter-pupillary width to estimate distance from the screen."""
        left = face[LEFT_PUPIL]
        right = face[RIGHT_PUPIL]
        pixel_width, _ = self._detector.findDistance(left, right)
        return (INTERPUPILLARY_DISTANCE_CM * FOCAL_LENGTH) / pixel_width

    # ------------------------------------------------------------------
    # Blink detection
    # ------------------------------------------------------------------

    def _check_blink(self, face: list, now: float) -> None:
        top = face[LEFT_EYE_TOP]
        bottom = face[LEFT_EYE_BOTTOM]
        opening, _ = self._detector.findDistance(top, bottom)

        eye_open = int(opening * 100) > BLINK_THRESHOLD

        if eye_open:
            # Eye is open — check how long since last blink
            if now - self._blink_timer >= BLINK_ALERT_INTERVAL_MS:
                self._alert_no_blink()
                self._blink_timer = now
        else:
            # Eye is closed (blinking) — reset the timer
            self._blink_timer = now

    # ------------------------------------------------------------------
    # Break / 20-20-20 rule
    # ------------------------------------------------------------------

    def _check_break_alert(self, now: float) -> None:
        if now - self._break_timer >= BREAK_ALERT_INTERVAL_MS:
            self._alert_break()
            self._break_timer = now

    # ------------------------------------------------------------------
    # Proximity handling
    # ------------------------------------------------------------------

    def _handle_too_close(self) -> None:
        self._proximity_alert_count += 1

        if self._proximity_alert_count >= PROXIMITY_ESCALATION_THRESHOLD:
            self._alert_too_close_critical()
            # Back off the counter a little so the user gets a brief window
            # to move back before the next escalation.
            self._proximity_alert_count = PROXIMITY_ESCALATION_THRESHOLD - 2
        else:
            self._alert_too_close()

    # ------------------------------------------------------------------
    # Alert helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _alert_no_blink() -> None:
        pag.alert(
            text=(
                "You haven't blinked in the past 20 seconds.\n\n"
                "Blinking keeps your eyes lubricated. Try to blink regularly "
                "to avoid dryness and discomfort."
            ),
            title="Blink Reminder — PopUp Wellness Monitor",
        )

    @staticmethod
    def _alert_break() -> None:
        pag.alert(
            text=(
                "You have been looking at your screen for 20 minutes.\n\n"
                "20-20-20 Rule: Look at something 6 metres (20 feet) away "
                "for at least 20 seconds to relax your eyes."
            ),
            title="Break Reminder — PopUp Wellness Monitor",
        )

    @staticmethod
    def _alert_too_close() -> None:
        pag.alert(
            text=(
                "You are sitting too close to your display.\n\n"
                "Doctors recommend maintaining at least 50 cm between your "
                "eyes and the screen to reduce eye strain."
            ),
            title="Distance Alert — PopUp Wellness Monitor",
        )

    @staticmethod
    def _alert_too_close_critical() -> None:
        pag.alert(
            text=(
                "You are still too close to your display!\n\n"
                "As a precaution, your screen brightness is being dimmed. "
                "Please move back to a safe distance (≥ 50 cm) to restore it."
            ),
            title="Distance Alert: Dimming Screen — PopUp Wellness Monitor",
        )
        sbc.set_brightness(BRIGHTNESS_DIMMED)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _shutdown(self) -> None:
        self._cap.release()
        cv2.destroyAllWindows()
