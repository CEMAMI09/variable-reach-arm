"""Forward and inverse kinematics for the 3-DOF variable-reach arm."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class ArmLimits:
    h: float = 0.65
    L_min: float = 0.70
    L_max: float = 1.20
    L_normal: float = 0.70
    yaw_min: float = math.radians(-70)
    yaw_max: float = math.radians(70)
    pitch_min: float = math.radians(-15)
    pitch_max: float = math.radians(70)


@dataclass
class JointState:
    yaw: float
    pitch: float
    L: float


@dataclass
class Pose:
    x: float
    y: float
    z: float


def forward(q: JointState, lim: ArmLimits | None = None) -> Pose:
    lim = lim or ArmLimits()
    cp = math.cos(q.pitch)
    return Pose(
        x=q.L * cp * math.cos(q.yaw),
        y=q.L * cp * math.sin(q.yaw),
        z=lim.h + q.L * math.sin(q.pitch),
    )


def inverse(p: Pose, lim: ArmLimits | None = None) -> JointState | None:
    lim = lim or ArmLimits()
    dx = p.x
    dy = p.y
    dz = p.z - lim.h
    L = math.sqrt(dx * dx + dy * dy + dz * dz)
    if L < 1e-9:
        return None
    pitch = math.asin(max(-1.0, min(1.0, dz / L)))
    yaw = math.atan2(dy, dx)
    q = JointState(yaw=yaw, pitch=pitch, L=L)
    if not in_workspace(q, lim):
        return clamp_joints(q, lim)
    return q


def clamp_joints(q: JointState, lim: ArmLimits | None = None) -> JointState:
    lim = lim or ArmLimits()
    return JointState(
        yaw=min(max(q.yaw, lim.yaw_min), lim.yaw_max),
        pitch=min(max(q.pitch, lim.pitch_min), lim.pitch_max),
        L=min(max(q.L, lim.L_min), lim.L_max),
    )


def in_workspace(q: JointState, lim: ArmLimits | None = None) -> bool:
    lim = lim or ArmLimits()
    return (
        lim.yaw_min <= q.yaw <= lim.yaw_max
        and lim.pitch_min <= q.pitch <= lim.pitch_max
        and lim.L_min <= q.L <= lim.L_max
    )


def required_reach(p: Pose, lim: ArmLimits | None = None) -> float:
    lim = lim or ArmLimits()
    return math.sqrt(p.x**2 + p.y**2 + (p.z - lim.h) ** 2)
