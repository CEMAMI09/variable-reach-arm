"""Interception planner: search future times for reachable catch points."""

from __future__ import annotations

import math
from dataclasses import dataclass

from host.kinematics.arm_kinematics import ArmLimits, JointState, Pose, forward, inverse
from host.planning.reach import select_reach


@dataclass
class BallState:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    t0: float = 0.0


@dataclass
class InterceptSolution:
    t: float
    pose: Pose
    joints: JointState
    L_cmd: float
    extended: bool
    cost: float


@dataclass
class PlannerLimits:
    yaw_vel: float = math.radians(120)
    pitch_vel: float = math.radians(120)
    ext_vel: float = 1.2  # m/s
    yaw_acc: float = math.radians(400)
    pitch_acc: float = math.radians(350)
    ext_acc: float = 4.0


@dataclass
class CostWeights:
    w_t: float = 1.0
    w_e: float = 0.5
    w_a: float = 0.1
    w_v: float = 0.05


def predict_ball(b: BallState, t: float, g: float = 9.81) -> Pose:
    dt = t - b.t0
    return Pose(
        x=b.x + b.vx * dt,
        y=b.y + b.vy * dt,
        z=b.z + b.vz * dt - 0.5 * g * dt * dt,
    )


def _axis_time(dist: float, v_max: float, a_max: float) -> float:
    """Minimum time for bang-coast-bang distance along one axis."""
    dist = abs(dist)
    if dist < 1e-9:
        return 0.0
    t_acc = v_max / a_max
    d_acc = 0.5 * a_max * t_acc * t_acc
    if 2 * d_acc >= dist:
        return 2 * math.sqrt(dist / a_max)
    d_coast = dist - 2 * d_acc
    return 2 * t_acc + d_coast / v_max


def time_to_reach(
    q0: JointState,
    q1: JointState,
    plim: PlannerLimits,
) -> float:
    ty = _axis_time(q1.yaw - q0.yaw, plim.yaw_vel, plim.yaw_acc)
    tp = _axis_time(q1.pitch - q0.pitch, plim.pitch_vel, plim.pitch_acc)
    te = _axis_time(q1.L - q0.L, plim.ext_vel, plim.ext_acc)
    return max(ty, tp, te)


def plan_intercept(
    ball: BallState,
    q0: JointState,
    lim: ArmLimits | None = None,
    plim: PlannerLimits | None = None,
    weights: CostWeights | None = None,
    t_horizon: float = 1.2,
    dt: float = 0.02,
) -> InterceptSolution | None:
    lim = lim or ArmLimits()
    plim = plim or PlannerLimits()
    weights = weights or CostWeights()
    best: InterceptSolution | None = None

    t = ball.t0 + dt
    while t <= ball.t0 + t_horizon:
        p = predict_ball(ball, t)
        if p.z < 0.05:
            break
        reach = select_reach(p, lim)
        if not reach.reachable:
            t += dt
            continue
        L_req = reach.L_req
        if L_req < 1e-6:
            t += dt
            continue
        # Place catcher on the ray to the ball at commanded length
        scale = reach.L_cmd / L_req
        p_cmd = Pose(p.x * scale, p.y * scale, lim.h + (p.z - lim.h) * scale)
        q = inverse(p_cmd, lim)
        if q is None:
            t += dt
            continue
        q = JointState(q.yaw, q.pitch, reach.L_cmd)
        if not (
            lim.yaw_min <= q.yaw <= lim.yaw_max
            and lim.pitch_min <= q.pitch <= lim.pitch_max
        ):
            t += dt
            continue
        travel = time_to_reach(q0, q, plim)
        if travel > (t - ball.t0):
            t += dt
            continue
        # Cost proxies
        A = abs(q.yaw - q0.yaw) + abs(q.pitch - q0.pitch)
        V = abs(q.L - q0.L)
        J = (
            weights.w_t * (t - ball.t0)
            + weights.w_e * max(0.0, q.L - lim.L_normal)
            + weights.w_a * A
            + weights.w_v * V
        )
        sol = InterceptSolution(t, p_cmd, q, reach.L_cmd, reach.extended, J)
        if best is None or sol.cost < best.cost:
            best = sol
        t += dt
    return best
