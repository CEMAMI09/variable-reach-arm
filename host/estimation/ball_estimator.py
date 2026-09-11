"""Residual-gated ballistic least squares for calibrated SI detections.

Latest exposure epoch, centered time arithmetic and finite/gap checks are
deliberate. No Kalman filter is claimed; a covariance model is not yet measured.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from host.planning.intercept import BallState


@dataclass(frozen=True)
class Detection:
    t: float  # exposure midpoint mapped into host monotonic time, never decode time
    x: float
    y: float
    z: float


@dataclass(frozen=True)
class FitResult:
    state: BallState
    samples: int
    span_s: float
    rms_residual_m: float
    peak_residual_m: float


def fit_ballistic_result(dets: list[Detection], g: float = 9.81,
                         max_rms_m: float = 0.025, min_span_s: float = 0.02,
                         max_gap_s: float = 0.06, max_span_s: float = 0.30,
                         max_peak_m: float = 0.05) -> FitResult | None:
    """Fit a short trajectory; reject stale gaps, degenerate times and outliers.

    Thresholds are provisional measurement-quality gates, not confidence bounds.
    Foam-ball drag, rolling shutter and biased calibration can evade residual
    checks; validate predictions against held-out frames at the required horizon.
    """
    if not all(math.isfinite(v) and v > 0 for v in
               (g, max_rms_m, min_span_s, max_gap_s, max_span_s, max_peak_m)):
        raise ValueError("positive finite estimator parameters required")
    if min_span_s > max_span_s:
        raise ValueError("invalid estimator span limits")
    if len(dets) < 3:
        return None
    if not all(math.isfinite(v) for d in dets for v in (d.t,d.x,d.y,d.z)):
        return None
    gaps = [b.t-a.t for a,b in zip(dets,dets[1:])]
    span = dets[-1].t-dets[0].t
    if any(gap <= 0 or gap > max_gap_s for gap in gaps) or not min_span_s <= span <= max_span_s:
        return None
    epoch = dets[-1].t
    ts = [d.t-epoch for d in dets]
    mt = math.fsum(ts)/len(ts)
    denominator = math.fsum((t-mt)**2 for t in ts)
    if denominator <= 1e-15:
        return None
    def fit(values):
        mean = math.fsum(values)/len(values)
        velocity = math.fsum((t-mt)*(v-mean) for t,v in zip(ts,values))/denominator
        return mean-velocity*mt, velocity
    x,vx = fit([d.x for d in dets])
    y,vy = fit([d.y for d in dets])
    z,vz = fit([d.z+.5*g*t*t for d,t in zip(dets,ts)])
    if not all(math.isfinite(v) for v in (x,y,z,vx,vy,vz)):
        return None
    residuals = [math.hypot(x+vx*t-d.x, y+vy*t-d.y, z+vz*t-.5*g*t*t-d.z)
                 for d,t in zip(dets,ts)]
    rms = math.sqrt(math.fsum(r*r for r in residuals)/len(residuals))
    peak = max(residuals)
    if rms > max_rms_m or peak > max_peak_m:
        return None
    return FitResult(BallState(x,y,z,vx,vy,vz,epoch),len(dets),span,rms,peak)


def fit_ballistic(dets: list[Detection], g: float = 9.81,
                  max_rms_m: float = 0.025, min_span_s: float = 0.02) -> BallState | None:
    result = fit_ballistic_result(dets,g,max_rms_m,min_span_s)
    return result.state if result else None


class BallisticTracker:
    """Small rolling fit; dropout/order faults invalidate the existing estimate."""
    def __init__(self, max_samples: int = 12, max_gap_s: float = 0.06):
        if max_samples < 3 or not math.isfinite(max_gap_s) or max_gap_s <= 0:
            raise ValueError("invalid tracker limits")
        self.max_samples = max_samples
        self.max_gap_s = max_gap_s
        self.detections: list[Detection] = []
        self.result: FitResult | None = None

    def update(self, detection: Detection) -> FitResult | None:
        if not all(math.isfinite(v) for v in detection.__dict__.values()):
            self.detections.clear()
            self.result = None
            return None
        if self.detections:
            gap = detection.t-self.detections[-1].t
            if gap <= 0:
                self.detections.clear()
                self.result = None
                return None
            if gap > self.max_gap_s:
                self.detections.clear()
        self.detections.append(detection)
        self.detections = self.detections[-self.max_samples:]
        # Keep the physical ballistic fit short even at low variable frame rates.
        self.detections = [d for d in self.detections if detection.t-d.t <= .30]
        self.result = fit_ballistic_result(self.detections, max_gap_s=self.max_gap_s)
        return self.result

    def current(self, now: float, max_age_s: float = .10) -> BallState | None:
        if not math.isfinite(now) or not math.isfinite(max_age_s) or max_age_s < 0:
            raise ValueError("invalid freshness query")
        if self.result is None or not 0 <= now-self.result.state.t0 <= max_age_s:
            return None
        return self.result.state


class SimpleKalmanBall:
    """Compatibility error for the former blend that never estimated velocity."""
    def __init__(self, g: float = 9.81):
        raise NotImplementedError("Legacy class was not a Kalman filter; use BallisticTracker or fit_ballistic.")
