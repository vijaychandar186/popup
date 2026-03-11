"""
Smoke tests for src/config.py

Verify that all expected constants are defined, correctly typed, and within
sensible ranges. These tests catch accidental deletions or type regressions.
"""

import src.config as cfg


class TestCameraConfig:
    def test_camera_index_is_non_negative_int(self) -> None:
        assert isinstance(cfg.CAMERA_INDEX, int)
        assert cfg.CAMERA_INDEX >= 0


class TestFaceMeasurementConfig:
    def test_ipd_positive_float(self) -> None:
        assert isinstance(cfg.INTERPUPILLARY_DISTANCE_CM, float)
        assert cfg.INTERPUPILLARY_DISTANCE_CM > 0

    def test_focal_length_positive_int(self) -> None:
        assert isinstance(cfg.FOCAL_LENGTH, int)
        assert cfg.FOCAL_LENGTH > 0



class TestLandmarkIndices:
    def test_landmark_indices_are_non_negative_ints(self) -> None:
        for name in ("LEFT_PUPIL", "RIGHT_PUPIL", "LEFT_EYE_TOP", "LEFT_EYE_BOTTOM"):
            value = getattr(cfg, name)
            assert isinstance(value, int), f"{name} should be int"
            assert value >= 0, f"{name} should be non-negative"



class TestDistanceThresholds:
    def test_too_close_less_than_zone_close_max(self) -> None:
        assert cfg.DISTANCE_TOO_CLOSE < cfg.DISTANCE_ZONE_CLOSE_MAX

    def test_zone_close_max_less_than_zone_near_max(self) -> None:
        assert cfg.DISTANCE_ZONE_CLOSE_MAX < cfg.DISTANCE_ZONE_NEAR_MAX



class TestAlertIntervals:
    def test_blink_alert_interval_positive(self) -> None:
        assert cfg.BLINK_ALERT_INTERVAL_MS > 0

    def test_break_alert_interval_positive(self) -> None:
        assert cfg.BREAK_ALERT_INTERVAL_MS > 0

    def test_break_interval_longer_than_blink_interval(self) -> None:
        assert cfg.BREAK_ALERT_INTERVAL_MS > cfg.BLINK_ALERT_INTERVAL_MS



class TestBrightnessConfig:
    def test_brightness_dimmed_in_valid_range(self) -> None:
        assert 0 <= cfg.BRIGHTNESS_DIMMED <= 100


class TestZoomSmoothing:
    def test_zoom_hysteresis_non_negative(self) -> None:
        assert cfg.ZOOM_HYSTERESIS_CM >= 0

    def test_zoom_cooldown_positive(self) -> None:
        assert cfg.ZOOM_COOLDOWN_MS > 0

    def test_zoom_smoothing_alpha_in_range(self) -> None:
        assert 0.0 < cfg.ZOOM_SMOOTHING_ALPHA <= 1.0



class TestNoFaceExit:
    def test_no_face_exit_frames_positive(self) -> None:
        assert cfg.NO_FACE_EXIT_FRAMES > 0
