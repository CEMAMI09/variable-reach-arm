"""Analytic quintics and exact rest-to-rest derivative limits.

No numerical linear solve per sample; all units SI. Profiles are bounded-jerk
(jerk steps at the endpoints), not continuous-jerk splines.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field


def minimum_duration(distance: float, velocity: float, acceleration: float, jerk: float) -> float:
    """Exact minimum T for this quintic, not for all possible motion profiles."""
    if not all(math.isfinite(v) for v in (distance, velocity, acceleration, jerk)):
        raise ValueError("trajectory inputs must be finite")
    if min(velocity, acceleration, jerk) <= 0:
        raise ValueError("derivative limits must be positive")
    d = abs(distance)
    return max(1.875 * d / velocity,
               math.sqrt((10 * math.sqrt(3) / 3) * d / acceleration),
               (60 * d / jerk) ** (1 / 3))


@dataclass(frozen=True)
class QuinticSegment:
    t0: float
    T: float
    q0: float
    q1: float
    v0: float = 0.0
    v1: float = 0.0
    a0: float = 0.0
    a1: float = 0.0
    _c: tuple[float, ...] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not all(math.isfinite(v) for v in (self.t0, self.T, self.q0, self.q1,
                                               self.v0, self.v1, self.a0, self.a1)) or self.T <= 0:
            raise ValueError("finite endpoints and strictly positive duration required")
        c0, c1, c2 = self.q0, self.T * self.v0, self.T**2 * self.a0 / 2
        d = self.q1 - c0 - c1 - c2
        v = self.T * self.v1 - c1 - 2 * c2
        a = self.T**2 * self.a1 - 2 * c2
        object.__setattr__(self, "_c", (c0, c1, c2, 10*d - 4*v + a/2,
                                       -15*d + 7*v - a, 6*d - 3*v + a/2))

    def sample(self, t: float) -> tuple[float, float, float]:
        if not math.isfinite(t):
            raise ValueError("sample time must be finite")
        if t < self.t0 or t > self.t0+self.T:
            if any((self.v0,self.v1,self.a0,self.a1)):
                raise ValueError("moving-boundary segment sampled outside its time domain")
            return (self.q0 if t < self.t0 else self.q1),0.0,0.0
        u = min(max((t - self.t0) / self.T, 0.0), 1.0)
        c0, c1, c2, c3, c4, c5 = self._c
        q = c0 + u * (c1 + u * (c2 + u * (c3 + u * (c4 + u * c5))))
        v = (c1 + u * (2*c2 + u * (3*c3 + u * (4*c4 + u * 5*c5)))) / self.T
        a = (2*c2 + u * (6*c3 + u * (12*c4 + u * 20*c5))) / self.T**2
        return q, v, a

    def jerk(self, t: float) -> float:
        if not math.isfinite(t):
            raise ValueError("sample time must be finite")
        if t < self.t0 or t > self.t0+self.T:
            if any((self.v0,self.v1,self.a0,self.a1)):
                raise ValueError("moving-boundary segment sampled outside its time domain")
            return 0.0
        u = min(max((t - self.t0) / self.T, 0.0), 1.0)
        return (6*self._c[3] + u * (24*self._c[4] + u * 60*self._c[5])) / self.T**3

    def rest_to_rest_peaks(self) -> tuple[float, float, float]:
        if any((self.v0, self.v1, self.a0, self.a1)):
            raise ValueError("peak formula requires zero boundary derivatives")
        d = abs(self.q1 - self.q0)
        return 1.875*d/self.T, (10*math.sqrt(3)/3)*d/self.T**2, 60*d/self.T**3


def multi_axis_quintic(q0: list[float], q1: list[float], duration: float,
                       t0: float = 0.0) -> list[QuinticSegment]:
    return [QuinticSegment(t0, duration, a, b) for a, b in zip(q0, q1, strict=True)]
