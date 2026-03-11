"""
Cross-platform nightlight helper.

Temperature mode attempts to warm the display using per-OS gamma controls.
If unsupported, it falls back to brightness dimming.
"""

from __future__ import annotations

import platform
import time
from dataclasses import dataclass
from typing import Iterable, List

import screen_brightness_control as sbc

from .config import (
    NIGHTLIGHT_BRIGHTNESS,
    NIGHTLIGHT_MODE,
    NIGHTLIGHT_POLL_SECONDS,
    NIGHTLIGHT_WARMTH,
)


@dataclass
class _GammaState:
    r: float
    g: float
    b: float


class NightLightController:
    """Apply and restore a nightlight temperature or brightness level."""

    def __init__(self, brightness: int | None = None) -> None:
        self._brightness = NIGHTLIGHT_BRIGHTNESS if brightness is None else brightness
        self._previous: List[int] | None = None
        self._previous_gamma: _GammaState | None = None

    def enable(self) -> None:
        if NIGHTLIGHT_MODE == "temperature":
            if _enable_temperature(NIGHTLIGHT_WARMTH):
                return
        self._previous = _get_brightness_list()
        _set_brightness_all(self._brightness)

    def disable(self) -> None:
        if NIGHTLIGHT_MODE == "temperature":
            if _disable_temperature():
                return
        if self._previous is None:
            return
        try:
            _set_brightness_all(self._previous)
        finally:
            self._previous = None

    def run(self) -> None:
        """Enable nightlight and keep it on until interrupted."""
        self.enable()
        try:
            while True:
                time.sleep(NIGHTLIGHT_POLL_SECONDS)
        finally:
            self.disable()


def _get_brightness_list() -> List[int]:
    value = sbc.get_brightness()
    if isinstance(value, int):
        return [value]
    return list(value)


def _set_brightness_all(levels: int | Iterable[int]) -> None:
    try:
        sbc.set_brightness(levels)
    except Exception:
        # Fallback: apply a single value to all displays.
        if isinstance(levels, int):
            sbc.set_brightness(levels, display=0)
        else:
            for idx, level in enumerate(levels):
                try:
                    sbc.set_brightness(level, display=idx)
                except Exception:
                    continue


def _enable_temperature(warmth: float) -> bool:
    system = platform.system().lower()
    warmth = _clamp(warmth, 0.0, 1.0)
    # Reduce blue most, green a bit, keep red at 1.0.
    r, g, b = 1.0, 1.0 - (warmth * 0.35), 1.0 - (warmth * 0.7)

    if system == "windows":
        return _windows_set_gamma(r, g, b)
    if system == "linux":
        return _linux_set_gamma(r, g, b)
    # macOS does not expose a stable gamma API in stdlib; fall back.
    return False


def _disable_temperature() -> bool:
    system = platform.system().lower()
    if system == "windows":
        return _windows_set_gamma(1.0, 1.0, 1.0)
    if system == "linux":
        return _linux_set_gamma(1.0, 1.0, 1.0)
    return False


def _windows_set_gamma(r: float, g: float, b: float) -> bool:
    try:
        import ctypes
        from ctypes import byref, c_uint16

        gdi32 = ctypes.windll.gdi32
        user32 = ctypes.windll.user32

        hdc = user32.GetDC(0)
        if not hdc:
            return False

        ramp_type = c_uint16 * (256 * 3)
        ramp = ramp_type()
        for i in range(256):
            base = i * 256
            ramp[i] = int(_clamp(base * r, 0, 65535))
            ramp[256 + i] = int(_clamp(base * g, 0, 65535))
            ramp[512 + i] = int(_clamp(base * b, 0, 65535))

        result = gdi32.SetDeviceGammaRamp(hdc, byref(ramp))
        user32.ReleaseDC(0, hdc)
        return bool(result)
    except Exception:
        return False


def _linux_set_gamma(r: float, g: float, b: float) -> bool:
    try:
        import subprocess

        outputs = _linux_outputs()
        if not outputs:
            return False
        gamma = f"{r:.3f}:{g:.3f}:{b:.3f}"
        for output in outputs:
            subprocess.run(
                ["xrandr", "--output", output, "--gamma", gamma],
                check=False,
                capture_output=True,
            )
        return True
    except Exception:
        return False


def _linux_outputs() -> List[str]:
    try:
        import subprocess

        result = subprocess.run(
            ["xrandr", "--query"],
            check=False,
            capture_output=True,
            text=True,
        )
        outputs = []
        for line in result.stdout.splitlines():
            if " connected" in line:
                outputs.append(line.split()[0])
        return outputs
    except Exception:
        return []


def _clamp(value: float, lo: float, hi: float) -> float:
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value
