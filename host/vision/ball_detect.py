"""Color-threshold ball detection (Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BallBlob:
    u: float
    v: float
    radius_px: float
    area: float


def detect_ball_bgr(
    frame_bgr: np.ndarray,
    lower_hsv: tuple[int, int, int] = (5, 120, 120),
    upper_hsv: tuple[int, int, int] = (25, 255, 255),
) -> BallBlob | None:
    """Detect bright orange/yellow foam ball. Requires OpenCV at runtime."""
    try:
        import cv2
    except ImportError as e:
        raise ImportError("opencv-python required for vision") from e

    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    c = max(cnts, key=cv2.contourArea)
    area = float(cv2.contourArea(c))
    if area < 20:
        return None
    (u, v), r = cv2.minEnclosingCircle(c)
    return BallBlob(u=float(u), v=float(v), radius_px=float(r), area=area)
