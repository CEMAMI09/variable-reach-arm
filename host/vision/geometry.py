"""Calibrated metric stereo geometry, independent of image acquisition libraries.

Camera coordinates: +x right, +y down, +z forward. R_world_camera and
t_world_camera map LEFT camera coordinates into arm +X/+Y/+Z world coordinates.
Images must already be undistorted and rectified using this calibration.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from host.estimation.ball_estimator import Detection


@dataclass(frozen=True)
class StereoCalibration:
    fx: float
    fy: float
    cx: float
    cy: float
    baseline_m: float
    R_world_camera: tuple[tuple[float, float, float], ...]
    t_world_camera: tuple[float, float, float]
    calibration_id: str

    def __post_init__(self):
        if not self.calibration_id:
            raise ValueError("an identified calibration is required")
        if len(self.R_world_camera) != 3 or any(len(row) != 3 for row in self.R_world_camera) or len(self.t_world_camera) != 3:
            raise ValueError("expected 3x3 rotation and 3-vector translation")
        values = (self.fx,self.fy,self.cx,self.cy,self.baseline_m,
                  *(x for row in self.R_world_camera for x in row),*self.t_world_camera)
        if not all(math.isfinite(v) for v in values) or min(self.fx,self.fy,self.baseline_m) <= 0:
            raise ValueError("invalid camera calibration")
        r = self.R_world_camera
        if any(abs(sum(a*b for a,b in zip(r[i],r[j]))-(1 if i == j else 0)) > 1e-6
               for i in range(3) for j in range(3)):
            raise ValueError("camera rotation must be orthonormal")
        determinant = (r[0][0]*(r[1][1]*r[2][2]-r[1][2]*r[2][1])
                       -r[0][1]*(r[1][0]*r[2][2]-r[1][2]*r[2][0])
                       +r[0][2]*(r[1][0]*r[2][1]-r[1][1]*r[2][0]))
        if abs(determinant-1) > 1e-6:
            raise ValueError("camera rotation must be right-handed")


@dataclass(frozen=True)
class StereoMeasurement:
    detection: Detection
    depth_m: float
    disparity_px: float
    depth_uncertainty_m: float  # bounded disparity + pair motion error; excludes calibration errors
    exposure_skew_s: float
    age_s: float
    calibration_id: str


def triangulate_rectified(left_uv: tuple[float,float], right_uv: tuple[float,float],
                          left_exposure_s: float, right_exposure_s: float, now_s: float,
                          calibration: StereoCalibration, *, max_skew_s: float = .002,
                          max_age_s: float = .10, max_epipolar_error_px: float = 1.5,
                          disparity_uncertainty_px: float = .5,
                          max_depth_uncertainty_m: float = .02,
                          max_ball_speed_m_s: float | None = None,
                          pair_timestamp_uncertainty_s: float = 0.0,
                          min_depth_m: float = .3, max_depth_m: float = 5.0) -> StereoMeasurement | None:
    """Reject unsynchronized/ill-conditioned pairs before they reach the planner.

    Time values are exposure midpoints mapped to the SAME host monotonic clock.
    Receipt timestamps are not substitutes. Independent USB webcams do not
    become synchronized by invoking this function or specifying nominal FPS.
    Equal principal points and rectified projection intrinsics are required.
    Nonzero pair timing error requires an explicit physical speed bound. A skew
    threshold alone does not bound moving-target depth error. Timestamp uncertainty
    is the bound on the pair's relative exposure-time error, including synchronization.
    """
    if len(left_uv) != 2 or len(right_uv) != 2:
        raise ValueError("pixel coordinates require u,v")
    values = (*left_uv,*right_uv,left_exposure_s,right_exposure_s,now_s)
    if not all(math.isfinite(v) for v in values):
        return None
    gates = (max_skew_s,max_age_s,max_epipolar_error_px,disparity_uncertainty_px,
             max_depth_uncertainty_m,min_depth_m,max_depth_m)
    if not all(math.isfinite(v) and v > 0 for v in gates) or min_depth_m >= max_depth_m:
        raise ValueError("invalid stereo quality gates")
    if not math.isfinite(pair_timestamp_uncertainty_s) or pair_timestamp_uncertainty_s < 0:
        raise ValueError("invalid pair timestamp uncertainty")
    if max_ball_speed_m_s is not None and (not math.isfinite(max_ball_speed_m_s) or max_ball_speed_m_s < 0):
        raise ValueError("invalid physical speed bound")
    skew = abs(left_exposure_s-right_exposure_s)
    timing_bound = skew + pair_timestamp_uncertainty_s
    age = now_s-min(left_exposure_s,right_exposure_s)
    if now_s < max(left_exposure_s,right_exposure_s) or age > max_age_s or timing_bound > max_skew_s:
        return None
    if timing_bound > 0 and max_ball_speed_m_s is None:
        return None
    if abs(left_uv[1]-right_uv[1]) > max_epipolar_error_px:
        return None
    disparity = left_uv[0]-right_uv[0]
    if disparity <= disparity_uncertainty_px:
        return None
    z = calibration.fx*calibration.baseline_m/disparity
    # At left exposure: d*Z = fx*(baseline - delta_x + u_right_normalized*delta_z).
    # Cauchy–Schwarz bounds the unknown 3D displacement by speed*pair timing.
    # Include per-coordinate pixel error conservatively in normalized right u;
    # the caller's disparity bound must bound each coordinate's error as well.
    right_u_bound = abs((right_uv[0]-calibration.cx)/calibration.fx) + disparity_uncertainty_px/calibration.fx
    baseline_error = (max_ball_speed_m_s or 0.0)*timing_bound*math.sqrt(1+right_u_bound**2)
    if baseline_error >= calibration.baseline_m:
        return None
    z_low = calibration.fx*(calibration.baseline_m-baseline_error)/(disparity+disparity_uncertainty_px)
    z_high = calibration.fx*(calibration.baseline_m+baseline_error)/(disparity-disparity_uncertainty_px)
    uncertainty = max(z-z_low,z_high-z)
    if z_low < min_depth_m or z_high > max_depth_m or uncertainty > max_depth_uncertainty_m:
        return None
    local = ((left_uv[0]-calibration.cx)*z/calibration.fx,
             (left_uv[1]-calibration.cy)*z/calibration.fy,z)
    world = [sum(a*b for a,b in zip(row,local))+offset
             for row,offset in zip(calibration.R_world_camera,calibration.t_world_camera)]
    # Estimate belongs to the left-camera exposure; right-pair skew is a separate error.
    return StereoMeasurement(Detection(left_exposure_s,*world),z,disparity,uncertainty,
                             skew,age,calibration.calibration_id)
