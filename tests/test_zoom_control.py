"""
Unit tests for src/zoom_control.py

ZoomController fires Ctrl+/- hotkeys when the viewing-distance zone changes.
We mock pyautogui so no actual key events are sent during tests.
"""

from unittest.mock import call, patch

import pytest

from src.zoom_control import ZoomController


@pytest.fixture()
def zoom() -> ZoomController:
    """Fresh ZoomController starting in the neutral zone."""
    return ZoomController()


class TestZoneClassification:
    def test_close_zone(self, zoom: ZoomController) -> None:
        assert zoom._classify(20) == "close"
        assert zoom._classify(39) == "close"

    def test_neutral_zone(self, zoom: ZoomController) -> None:
        assert zoom._classify(40) == "neutral"
        assert zoom._classify(60) == "neutral"

    def test_far_zone(self, zoom: ZoomController) -> None:
        assert zoom._classify(62) == "far"
        assert zoom._classify(100) == "far"

    def test_hysteresis_holds_close_until_exit_threshold(self, zoom: ZoomController) -> None:
        zoom._last_zone = "close"
        assert zoom._classify(40) == "close"
        assert zoom._classify(43) == "close"
        assert zoom._classify(44) == "neutral"

    def test_hysteresis_holds_far_until_exit_threshold(self, zoom: ZoomController) -> None:
        zoom._last_zone = "far"
        assert zoom._classify(61) == "far"
        assert zoom._classify(58) == "far"
        assert zoom._classify(57) == "neutral"


class TestZoomTransitions:
    def test_no_hotkey_when_zone_unchanged(self, zoom: ZoomController) -> None:
        """Staying in the neutral zone should not fire any hotkey."""
        with patch("src.zoom_control.pag") as mock_pag:
            zoom.update(50, now_ms=10_000)  # neutral -> neutral (no change)
            zoom.update(55, now_ms=10_500)  # still neutral
            mock_pag.hotkey.assert_not_called()

    def test_zoom_in_when_moving_far(self, zoom: ZoomController) -> None:
        """Moving from neutral to far should trigger Ctrl++."""
        with patch("src.zoom_control.pag") as mock_pag:
            zoom.update(80, now_ms=10_000)  # neutral -> far
            mock_pag.hotkey.assert_called_once_with("ctrl", "+")

    def test_zoom_out_when_moving_close(self, zoom: ZoomController) -> None:
        """Moving from neutral to close should trigger Ctrl+-."""
        with patch("src.zoom_control.pag") as mock_pag:
            zoom.update(20, now_ms=10_000)  # neutral -> close
            mock_pag.hotkey.assert_called_once_with("ctrl", "-")

    def test_zoom_in_when_returning_from_close_to_neutral(
        self, zoom: ZoomController
    ) -> None:
        """Returning from close to neutral should restore zoom (Ctrl++)."""
        with patch("src.zoom_control.pag") as mock_pag:
            zoom.update(20, now_ms=10_000)  # neutral -> close  (Ctrl+-)
            # Move the EMA across the hysteresis boundary.
            for step in range(1, 12):
                zoom.update(50, now_ms=10_000 + step * 300)
            assert mock_pag.hotkey.call_args_list == [
                call("ctrl", "-"),
                call("ctrl", "+"),
            ]

    def test_zoom_out_when_returning_from_far_to_neutral(
        self, zoom: ZoomController
    ) -> None:
        """Returning from far to neutral should restore zoom (Ctrl+-)."""
        with patch("src.zoom_control.pag") as mock_pag:
            zoom.update(80, now_ms=10_000)  # neutral -> far     (Ctrl++)
            # Move the EMA across the hysteresis boundary.
            for step in range(1, 9):
                zoom.update(50, now_ms=10_000 + step * 300)
            assert mock_pag.hotkey.call_args_list == [
                call("ctrl", "+"),
                call("ctrl", "-"),
            ]

    def test_no_duplicate_hotkey_for_same_zone(self, zoom: ZoomController) -> None:
        """Multiple updates within the same zone fire only one hotkey."""
        with patch("src.zoom_control.pag") as mock_pag:
            zoom.update(80, now_ms=10_000)  # neutral -> far  (1 hotkey)
            zoom.update(90, now_ms=10_500)  # still far
            zoom.update(100, now_ms=11_000)  # still far
            assert mock_pag.hotkey.call_count == 1

    def test_cooldown_blocks_rapid_flips(self, zoom: ZoomController) -> None:
        with patch("src.zoom_control.pag") as mock_pag:
            zoom.update(20, now_ms=10_000)  # neutral -> close
            zoom.update(80, now_ms=10_200)  # too soon to flip to far
            mock_pag.hotkey.assert_called_once()
