"""Ballistic / least-squares trajectory estimation for foam balls."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from host.planning.intercept import BallState


@dataclass
class Detection:
    t: float
    x: float
    y: float
    z: float


def fit_ballistic(dets: list[Detection], g: float = 9.81) -> BallState | None:
    """Fit x=x0+vx*t, y=y0+vy*t, z=z0+vz*t-0.5*g*t^2 using first time as epoch."""
    if len(dets) < 3:
        return None
    t0 = dets[0].t
    ts = np.array([d.t - t0 for d in dets])
    xs = np.array([d.x for d in dets])
    ys = np.array([d.y for d in dets])
    zs = np.array([d.z for d in dets])

    A = np.column_stack([np.ones_like(ts), ts])
    x0, vx = np.linalg.lstsq(A, xs, rcond=None)[0]
    y0, vy = np.linalg.lstsq(A, ys, rcond=None)[0]
    # z + 0.5 g t^2 = z0 + vz t
    z_adj = zs + 0.5 * g * ts**2
    z0, vz = np.linalg.lstsq(A, z_adj, rcond=None)[0]
    return BallState(x0, y0, z0, vx, vy, vz, t0=t0)


class SimpleKalmanBall:
    """Constant-velocity XY, constant-accel Z (gravity) linear KF."""

    def __init__(self, g: float = 9.81):
        self.g = g
        self.x = None  # [x,y,z,vx,vy,vz]

    def predict(self, dt: float) -> None:
        if self.x is None:
            return
        F = np.eye(6)
        F[0, 3] = dt
        F[1, 4] = dt
        F[2, 5] = dt
        self.x = F @ self.x
        self.x[5] -= self.g * dt  # vz update already in F on z; apply gravity to vz
        self.x[2] -= 0.5 * self.g * dt * dt

    def update(self, det: Detection) -> BallState:
        z = np.array([det.x, det.y, det.z])
        if self.x is None:
            self.x = np.array([det.x, det.y, det.z, 0, 0, 0], dtype=float)
        else:
            # Light blend — full KF covariance omitted for clarity / Milestone 0
            self.x[0:3] = 0.7 * self.x[0:3] + 0.3 * z
        return BallState(*self.x.tolist(), t0=det.t)
