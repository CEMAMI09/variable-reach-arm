"""Color-threshold ball detection (Phase 2)."""

from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass
class BallBlob:
    u: float
    v: float
    radius_px: float
    area: float
    circularity: float = 0.0
    exposure_s: float | None = None


def detect_ball_bgr(
    frame_bgr: np.ndarray,
    lower_hsv: tuple[int, int, int] = (5, 120, 120),
    upper_hsv: tuple[int, int, int] = (25, 255, 255),
    *,
    exposure_s: float | None = None,
    min_radius_px: float = 3.0,
    max_radius_px: float = 200.0,
    min_circularity: float = 0.65,
) -> BallBlob | None:
    """Pixel-only candidate, never world coordinates or a capture authorization.

    exposure_s must be a calibrated exposure timestamp for live use. The default
    None supports offline images only. Calibrate thresholds at actual exposure.
    """
    try:
        import cv2
    except ImportError as e:
        raise ImportError("opencv-python required for vision") from e

    if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3 or frame_bgr.dtype != np.uint8:
        raise ValueError("expected uint8 HxWx3 BGR frame")
    if not 0 < min_radius_px < max_radius_px or not 0 < min_circularity <= 1:
        raise ValueError("invalid ball geometry gates")
    if exposure_s is not None and not math.isfinite(exposure_s):
        raise ValueError("invalid exposure timestamp")
    hsv = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(lower_hsv), np.array(upper_hsv))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not cnts:
        return None
    candidates = []
    for c in cnts:
        area = float(cv2.contourArea(c))
        perimeter = float(cv2.arcLength(c, True))
        if area < 20 or perimeter <= 0:
            continue
        circularity = 4*math.pi*area/perimeter**2
        (u,v),r = cv2.minEnclosingCircle(c)
        if min_radius_px <= r <= max_radius_px and circularity >= min_circularity:
            candidates.append(BallBlob(float(u),float(v),float(r),area,circularity,exposure_s))
    return max(candidates,key=lambda b:b.circularity*math.sqrt(b.area)) if candidates else None
