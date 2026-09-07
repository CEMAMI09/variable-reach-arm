"""Projectile helpers."""

from __future__ import annotations

from host.planning.intercept import BallState, predict_ball


def time_of_flight_to_height(ball: BallState, z_target: float, g: float = 9.81) -> list[float]:
    """Solve z0 + vz t - 0.5 g t^2 = z_target for t>0."""
    a = -0.5 * g
    b = ball.vz
    c = ball.z - z_target
    disc = b * b - 4 * a * c
    if disc < 0:
        return []
    import math

    s = math.sqrt(disc)
    roots = [(-b + s) / (2 * a), (-b - s) / (2 * a)]
    return sorted(t for t in roots if t > 1e-6)


__all__ = ["BallState", "predict_ball", "time_of_flight_to_height"]
