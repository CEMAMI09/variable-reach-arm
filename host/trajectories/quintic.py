"""Smooth joint-space trajectories (quintic polynomial)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class QuinticSegment:
    t0: float
    T: float
    q0: float
    q1: float
    v0: float = 0.0
    v1: float = 0.0
    a0: float = 0.0
    a1: float = 0.0

    def _coeffs(self) -> np.ndarray:
        T = self.T
        M = np.array(
            [
                [0, 0, 0, 0, 0, 1],
                [T**5, T**4, T**3, T**2, T, 1],
                [0, 0, 0, 0, 1, 0],
                [5 * T**4, 4 * T**3, 3 * T**2, 2 * T, 1, 0],
                [0, 0, 0, 2, 0, 0],
                [20 * T**3, 12 * T**2, 6 * T, 2, 0, 0],
            ],
            dtype=float,
        )
        b = np.array([self.q0, self.q1, self.v0, self.v1, self.a0, self.a1], dtype=float)
        return np.linalg.solve(M, b)

    def sample(self, t: float) -> tuple[float, float, float]:
        tau = min(max(t - self.t0, 0.0), self.T)
        c = self._coeffs()
        q = c[0] * tau**5 + c[1] * tau**4 + c[2] * tau**3 + c[3] * tau**2 + c[4] * tau + c[5]
        v = 5 * c[0] * tau**4 + 4 * c[1] * tau**3 + 3 * c[2] * tau**2 + 2 * c[3] * tau + c[4]
        a = 20 * c[0] * tau**3 + 12 * c[1] * tau**2 + 6 * c[2] * tau + 2 * c[3]
        return float(q), float(v), float(a)


def multi_axis_quintic(
    q0: list[float],
    q1: list[float],
    duration: float,
    t0: float = 0.0,
) -> list[QuinticSegment]:
    return [
        QuinticSegment(t0=t0, T=duration, q0=a, q1=b) for a, b in zip(q0, q1, strict=True)
    ]
