"""Projectile + arm kinematics simulation for planner validation."""

from __future__ import annotations

import math
from dataclasses import dataclass

from host.kinematics.arm_kinematics import ArmLimits, JointState
from host.planning.intercept import BallState, plan_intercept, predict_ball


@dataclass
class SimResult:
    intercept_found: bool
    t_intercept: float | None
    extended: bool
    L_cmd: float | None
    ball_path: list[tuple[float, float, float, float]]
    message: str


def run_catch_scenario(
    ball: BallState,
    q0: JointState | None = None,
    lim: ArmLimits | None = None,
) -> SimResult:
    lim = lim or ArmLimits()
    q0 = q0 or JointState(0.0, math.radians(20), lim.L_normal)
    path = []
    for i in range(60):
        t = ball.t0 + i * 0.02
        p = predict_ball(ball, t)
        path.append((t, p.x, p.y, p.z))
        if p.z < 0:
            break

    sol = plan_intercept(ball, q0, lim=lim)
    if sol is None:
        return SimResult(False, None, False, None, path, "no_feasible_intercept")
    return SimResult(
        True,
        sol.t,
        sol.extended,
        sol.L_cmd,
        path,
        f"intercept cost={sol.cost:.3f} extended={sol.extended}",
    )


def demo() -> None:
    # Start roughly aimed to illustrate planner (not cold from zero).
    q0 = JointState(0.0, math.radians(30), 0.70)

    # Case A: ~0.55 m horizontal — remains retracted (L_cmd = L_normal)
    ball_a = BallState(x=0.55, y=0.0, z=1.2, vx=0.0, vy=0.0, vz=1.5)

    # Case B: ~1.0 m — requires partial extension; longer flight time
    ball_b = BallState(x=1.0, y=0.0, z=1.4, vx=0.0, vy=0.0, vz=2.0)

    for name, ball in [("A_normal", ball_a), ("B_extend", ball_b)]:
        r = run_catch_scenario(ball, q0=q0)
        print(
            name,
            r.message,
            "L_cmd",
            None if r.L_cmd is None else round(r.L_cmd, 3),
            "t",
            None if r.t_intercept is None else round(r.t_intercept, 3),
            "extended",
            r.extended,
        )


if __name__ == "__main__":
    demo()
