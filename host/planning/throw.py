"""Throw planning (Milestone 12 stretch) — release timing along a joint trajectory."""

from __future__ import annotations

import math
from dataclasses import dataclass

from host.kinematics.arm_kinematics import ArmLimits, JointState, Pose, forward
from host.trajectories.quintic import multi_axis_quintic


@dataclass
class ThrowPlan:
    q_start: JointState
    q_release: JointState
    duration: float
    release_time: float
    release_pose: Pose
    release_speed_est: float


def plan_throw_toward(
    target: Pose,
    q_start: JointState,
    lim: ArmLimits | None = None,
    duration: float = 0.45,
) -> ThrowPlan:
    """Heuristic: swing toward target azimuth/elevation and release near peak speed."""
    lim = lim or ArmLimits()
    yaw = math.atan2(target.y, target.x)
    pitch = math.radians(35)
    L = min(lim.L_max, max(lim.L_normal, 0.9))
    q_rel = JointState(yaw=yaw, pitch=pitch, L=L)
    segs = multi_axis_quintic(
        [q_start.yaw, q_start.pitch, q_start.L],
        [q_rel.yaw, q_rel.pitch, q_rel.L],
        duration,
    )
    # Sample mid-late for release
    t_rel = 0.7 * duration
    samples = [s.sample(t_rel) for s in segs]
    speed = math.sqrt(sum(v * v for _, v, _ in samples))
    pose = forward(q_rel, lim)
    return ThrowPlan(q_start, q_rel, duration, t_rel, pose, speed)
