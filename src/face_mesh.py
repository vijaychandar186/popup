"""
MediaPipe Tasks face-mesh wrapper compatible with the old cvzone API surface.

This keeps monitor.py stable while allowing Python 3.13 compatibility.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

import cv2
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import FaceLandmarker, FaceLandmarkerOptions, RunningMode
from mediapipe.tasks.python.vision.core.image import Image, ImageFormat

from .config import FACE_LANDMARKER_MODEL


@dataclass
class _DistanceInfo:
    p1: Tuple[int, int]
    p2: Tuple[int, int]


class FaceMeshDetector:
    """Minimal face-mesh detector with cvzone-like methods."""

    def __init__(self, max_faces: int = 1) -> None:
        model_path = _resolve_model_path(FACE_LANDMARKER_MODEL)
        if not model_path.is_file():
            raise FileNotFoundError(
                "Face landmarker model not found. "
                f"Expected at: {model_path}. "
                "Download the MediaPipe face landmarker task file and place it there."
            )

        options = FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=RunningMode.IMAGE,
            num_faces=max_faces,
        )
        self._landmarker = FaceLandmarker.create_from_options(options)

    def findFaceMesh(self, frame, draw: bool = False):
        """Return (frame, faces). Faces are lists of (x, y) pixel coords."""
        if frame is None:
            return frame, []

        height, width = frame.shape[:2]
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)

        faces = []
        for face_landmarks in result.face_landmarks or []:
            points = [
                (int(lm.x * width), int(lm.y * height))
                for lm in face_landmarks
            ]
            faces.append(points)

        return frame, faces

    @staticmethod
    def findDistance(p1: Iterable[int], p2: Iterable[int]):
        """Return Euclidean distance between two points."""
        x1, y1 = p1
        x2, y2 = p2
        dx = x1 - x2
        dy = y1 - y2
        distance = (dx * dx + dy * dy) ** 0.5
        return distance, _DistanceInfo(p1=(x1, y1), p2=(x2, y2))


def _resolve_model_path(model_value: str) -> Path:
    path = Path(model_value)
    if path.is_absolute():
        return path
    # Repo root = .../src/.. relative to this file.
    return Path(__file__).resolve().parents[1] / path
