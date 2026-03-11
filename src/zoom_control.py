"""
Adjusts the active window's zoom level (Ctrl+/Ctrl-) based on the user's
viewing distance from the screen.

Zone layout (distance in cm):
    close  : < 40  → zoom out (text already appears large when sitting near)
    neutral: 40–61 → restore zoom direction relative to previous zone
    far    : > 61  → zoom in  (text appears small when sitting far away)
"""

import time

import pyautogui as pag

from .config import (
    DISTANCE_ZONE_CLOSE_MAX,
    DISTANCE_ZONE_NEAR_MAX,
    ZOOM_COOLDOWN_MS,
    ZOOM_HYSTERESIS_CM,
    ZOOM_SMOOTHING_ALPHA,
)


class ZoomController:
    """Tracks viewing-distance zones and fires keyboard zoom shortcuts."""

    _ZONE_CLOSE = "close"
    _ZONE_NEUTRAL = "neutral"
    _ZONE_FAR = "far"

    def __init__(self) -> None:
        # Assume a reasonable starting distance so the first frame does not
        # trigger a spurious zoom change.
        self._last_zone: str = self._ZONE_NEUTRAL
        self._last_zoom_ms: float = 0.0
        self._smoothed_distance: float | None = None

    def update(self, distance_cm: int, now_ms: float | None = None) -> None:
        """Call on every frame with the estimated face-to-screen distance."""
        now_ms = _ms() if now_ms is None else now_ms
        smoothed = self._smooth(distance_cm)
        current_zone = self._classify(smoothed)
        if current_zone != self._last_zone:
            if self._can_zoom(now_ms, current_zone):
                self._apply_zoom(current_zone, self._last_zone)
                self._last_zone = current_zone
                self._last_zoom_ms = now_ms

    def _classify(self, distance_cm: float) -> str:
        close_enter = DISTANCE_ZONE_CLOSE_MAX
        close_exit = DISTANCE_ZONE_CLOSE_MAX + ZOOM_HYSTERESIS_CM
        far_enter = DISTANCE_ZONE_NEAR_MAX
        far_exit = DISTANCE_ZONE_NEAR_MAX - ZOOM_HYSTERESIS_CM

        if self._last_zone == self._ZONE_CLOSE:
            return self._ZONE_NEUTRAL if distance_cm >= close_exit else self._ZONE_CLOSE
        if self._last_zone == self._ZONE_FAR:
            return self._ZONE_NEUTRAL if distance_cm <= far_exit else self._ZONE_FAR

        if distance_cm < close_enter:
            return self._ZONE_CLOSE
        if distance_cm > far_enter:
            return self._ZONE_FAR
        return self._ZONE_NEUTRAL

    @staticmethod
    def _apply_zoom(current: str, previous: str) -> None:
        if current == ZoomController._ZONE_FAR:
            pag.hotkey("ctrl", "+")
        elif current == ZoomController._ZONE_CLOSE:
            pag.hotkey("ctrl", "-")
        else:
            # Entered neutral zone — restore opposite of where we came from
            if previous == ZoomController._ZONE_CLOSE:
                pag.hotkey("ctrl", "+")
            else:
                pag.hotkey("ctrl", "-")

    def _smooth(self, distance_cm: int) -> float:
        if self._smoothed_distance is None:
            self._smoothed_distance = float(distance_cm)
        else:
            alpha = ZOOM_SMOOTHING_ALPHA
            self._smoothed_distance = (
                alpha * distance_cm + (1.0 - alpha) * self._smoothed_distance
            )
        return self._smoothed_distance

    def _can_zoom(self, now_ms: float, target_zone: str) -> bool:
        cooldown = ZOOM_COOLDOWN_MS
        if target_zone == self._ZONE_NEUTRAL:
            cooldown = max(200, cooldown // 2)
        return (now_ms - self._last_zoom_ms) >= cooldown


def _ms() -> float:
    return time.monotonic() * 1_000.0
