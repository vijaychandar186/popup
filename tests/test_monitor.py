"""
Unit tests for src/monitor.py

The EyeStrainMonitor integrates with cv2, mediapipe, pyautogui, and
screen_brightness_control — all of which require hardware. We patch
every external dependency so the core logic can be tested in isolation.
"""

from unittest.mock import MagicMock, patch

import pytest

_PATCHES = {
    "cv2": MagicMock(),
    "mediapipe": MagicMock(),
    "pyautogui": MagicMock(),
    "screen_brightness_control": MagicMock(),
    "src.face_mesh": MagicMock(FaceMeshDetector=MagicMock()),
}


@pytest.fixture(autouse=True)
def _patch_external(monkeypatch):
    """Apply module-level mocks for all external dependencies."""
    for module, mock in _PATCHES.items():
        monkeypatch.setitem(__import__("sys").modules, module, mock)
    yield


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_monitor():
    """Import and instantiate EyeStrainMonitor with all externals mocked."""
    # Re-import inside the fixture so patched sys.modules take effect.
    import importlib

    import src.monitor as mod

    importlib.reload(mod)
    return mod.EyeStrainMonitor()


def _fake_face(pupil_dist: float = 50.0, eye_opening: float = 20.0) -> list:
    """
    Return a minimal face landmark list understood by _estimate_distance and
    _check_blink.  Only the four indices used by the monitor matter.
    """
    from src.config import (
        LEFT_EYE_BOTTOM,
        LEFT_EYE_TOP,
        LEFT_PUPIL,
        RIGHT_PUPIL,
    )

    max_idx = max(LEFT_PUPIL, RIGHT_PUPIL, LEFT_EYE_TOP, LEFT_EYE_BOTTOM) + 1
    face = [(0, 0)] * max_idx

    # findDistance is mocked; the landmark values themselves are not used for
    # arithmetic in tests — only their positions in the list matter.
    face[LEFT_PUPIL] = (0, 0)
    face[RIGHT_PUPIL] = (pupil_dist, 0)
    face[LEFT_EYE_TOP] = (0, 0)
    face[LEFT_EYE_BOTTOM] = (0, eye_opening)
    return face


# ---------------------------------------------------------------------------
# Distance estimation
# ---------------------------------------------------------------------------


class TestEstimateDistance:
    def test_returns_positive_float(self) -> None:
        monitor = _make_monitor()
        # findDistance is already a Mock; configure its return value
        monitor._detector.findDistance.return_value = (50.0, {})
        face = _fake_face()
        dist = monitor._estimate_distance(face)
        assert dist > 0

    def test_inversely_proportional_to_pixel_width(self) -> None:
        monitor = _make_monitor()
        monitor._detector.findDistance.return_value = (100.0, {})
        dist_100 = monitor._estimate_distance(_fake_face())

        monitor._detector.findDistance.return_value = (50.0, {})
        dist_50 = monitor._estimate_distance(_fake_face())

        # Halving the pixel width should double the estimated distance
        assert pytest.approx(dist_50, rel=1e-6) == dist_100 * 2


# ---------------------------------------------------------------------------
# Blink detection
# ---------------------------------------------------------------------------


class TestCheckBlink:
    def test_no_alert_when_blinking_regularly(self) -> None:
        monitor = _make_monitor()
        import src.config as cfg

        # Eye closed (blink value ≤ BLINK_THRESHOLD)
        # opening * 100 ≤ 1200  →  opening ≤ 12
        monitor._detector.findDistance.return_value = (10.0, {})

        import src.monitor as mod

        now = mod._ms()
        monitor._blink_timer = now - cfg.BLINK_ALERT_INTERVAL_MS - 1

        with patch("src.monitor.pag") as mock_pag:
            monitor._check_blink(_fake_face(), now)
            # Eye is closed → timer reset, NO alert
            mock_pag.alert.assert_not_called()

    def test_alert_fires_after_no_blink_interval(self) -> None:
        monitor = _make_monitor()
        import src.config as cfg
        import src.monitor as mod

        # Eye open: opening * 100 > BLINK_THRESHOLD (1200) → opening > 12
        monitor._detector.findDistance.return_value = (20.0, {})

        now = mod._ms()
        # Simulate blink timer expired
        monitor._blink_timer = now - cfg.BLINK_ALERT_INTERVAL_MS - 1

        with patch("src.monitor.pag") as mock_pag:
            monitor._check_blink(_fake_face(), now)
            mock_pag.alert.assert_called_once()


# ---------------------------------------------------------------------------
# Proximity / too-close handling
# ---------------------------------------------------------------------------


class TestHandleTooClose:
    def test_standard_alert_below_escalation_threshold(self) -> None:
        monitor = _make_monitor()
        monitor._proximity_alert_count = 0

        with patch("src.monitor.pag") as mock_pag:
            monitor._handle_too_close()
            mock_pag.alert.assert_called_once()

    def test_critical_alert_and_brightness_dim_at_threshold(self) -> None:
        monitor = _make_monitor()
        import src.config as cfg

        monitor._proximity_alert_count = cfg.PROXIMITY_ESCALATION_THRESHOLD

        with patch("src.monitor.pag") as mock_pag, patch("src.monitor.sbc") as mock_sbc:
            monitor._handle_too_close()
            mock_pag.alert.assert_called_once()
            mock_sbc.set_brightness.assert_called_once_with(cfg.BRIGHTNESS_DIMMED)


# ---------------------------------------------------------------------------
# No-face auto-exit
# ---------------------------------------------------------------------------


class TestNoFaceExit:
    def test_exits_after_sustained_no_face(self) -> None:
        import src.config as cfg

        monitor = _make_monitor()

        # Mock cap.read to return a blank frame with no face
        monitor._cap.read.return_value = (True, MagicMock())
        monitor._detector.findFaceMesh.return_value = (MagicMock(), [])

        # Pre-load counter just below threshold
        monitor._no_face_frames = cfg.NO_FACE_EXIT_FRAMES - 1

        # One more frame should push it over and return False
        result = monitor._tick()
        assert result is False
