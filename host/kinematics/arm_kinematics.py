"""SI kinematics. +X forward, +Y left, +Z up; pitch zero is horizontal.

L is pivot to nominal capture point, NOT encoder extension. Encoder travel is
L - L_min. An unreachable point must never silently turn into another target.
"""

from __future__ import annotations
import math
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArmLimits:
    h: float = 0.85
    L_min: float = 0.70
    L_max: float = 1.20
    L_normal: float = 0.70
    yaw_min: float = math.radians(-70)
    yaw_max: float = math.radians(70)
    pitch_min: float = math.radians(-15)
    pitch_max: float = math.radians(70)
    floor_z: float = 0.0
    swept_radius: float = 0.09  # provisional envelope, not validated CAD clearance
    rear_extent: float = 0.35  # Rev B rear tube/motor allowance, must be CAD-checked

    def __post_init__(self) -> None:
        if not all(math.isfinite(v) for v in self.__dict__.values()):
            raise ValueError("arm limits must be finite")
        if not 0 < self.L_min <= self.L_normal <= self.L_max:
            raise ValueError("require 0 < L_min <= L_normal <= L_max")
        if not -math.pi <= self.yaw_min < self.yaw_max <= math.pi:
            raise ValueError("invalid yaw interval")
        if not -math.pi / 2 < self.pitch_min < self.pitch_max < math.pi / 2:
            raise ValueError("pitch interval must avoid spherical singularities")
        if min(self.swept_radius, self.rear_extent) < 0 or self.h - self.swept_radius < self.floor_z:
            raise ValueError("invalid floor/clearance geometry")

    @classmethod
    def from_design_file(cls, path: str | Path | None = None) -> "ArmLimits":
        """Load shared CAD/engineering geometry; clearance is still provisional."""
        path = Path(path) if path else Path(__file__).resolve().parents[2] / "engineering" / "design_parameters.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1:
            raise ValueError("unsupported engineering parameter schema")
        g = data["geometry"]
        if not math.isclose(g["maximum_reach_m"]-g["normal_reach_m"], g["extension_stroke_m"], abs_tol=1e-9):
            raise ValueError("inconsistent reach and encoder stroke")
        return cls(h=g["pivot_height_m"], L_min=g["normal_reach_m"],
                   L_normal=g["normal_reach_m"], L_max=g["maximum_reach_m"],
                   yaw_min=g["yaw_min_rad"], yaw_max=g["yaw_max_rad"],
                   pitch_min=g["pitch_min_rad"], pitch_max=g["pitch_max_rad"])


@dataclass(frozen=True)
class JointState:
    yaw: float
    pitch: float
    L: float


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    z: float


def _finite(*values: float) -> bool:
    return all(math.isfinite(v) for v in values)


def forward(q: JointState, lim: ArmLimits | None = None) -> Pose:
    lim = lim or ArmLimits.from_design_file()
    if not _finite(q.yaw, q.pitch, q.L) or q.L <= 0:
        raise ValueError("invalid joint state")
    cp = math.cos(q.pitch)
    return Pose(q.L * cp * math.cos(q.yaw), q.L * cp * math.sin(q.yaw),
                lim.h + q.L * math.sin(q.pitch))


def tip_velocity(q: JointState, rates: JointState) -> Pose:
    """Jacobian times [yaw rad/s, pitch rad/s, extension m/s], in m/s."""
    if not _finite(q.yaw, q.pitch, q.L, rates.yaw, rates.pitch, rates.L):
        raise ValueError("invalid joint state or rates")
    cy, sy = math.cos(q.yaw), math.sin(q.yaw)
    cp, sp = math.cos(q.pitch), math.sin(q.pitch)
    return Pose(rates.L * cp * cy - q.L * sp * cy * rates.pitch - q.L * cp * sy * rates.yaw,
                rates.L * cp * sy - q.L * sp * sy * rates.pitch + q.L * cp * cy * rates.yaw,
                rates.L * sp + q.L * cp * rates.pitch)


def inverse(p: Pose, lim: ArmLimits | None = None) -> JointState | None:
    lim = lim or ArmLimits.from_design_file()
    if not _finite(p.x, p.y, p.z):
        return None
    dz = p.z - lim.h
    L = math.hypot(p.x, p.y, dz)
    if L < 1e-9:
        return None
    q = JointState(math.atan2(p.y, p.x), math.atan2(dz, math.hypot(p.x, p.y)), L)
    return q if in_workspace(q, lim) else None


def clamp_joints(q: JointState, lim: ArmLimits | None = None) -> JointState:
    """Explicit projection for visualization/manual UI only; never IK/planning."""
    lim = lim or ArmLimits.from_design_file()
    if not _finite(q.yaw, q.pitch, q.L):
        raise ValueError("invalid joint state")
    return JointState(min(max(q.yaw, lim.yaw_min), lim.yaw_max),
                      min(max(q.pitch, lim.pitch_min), lim.pitch_max),
                      min(max(q.L, lim.L_min), lim.L_max))


def in_workspace(q: JointState, lim: ArmLimits | None = None) -> bool:
    lim = lim or ArmLimits.from_design_file()
    eps = 1e-12  # floating-point boundary roundoff only
    return (_finite(q.yaw, q.pitch, q.L)
            and lim.yaw_min - eps <= q.yaw <= lim.yaw_max + eps
            and lim.pitch_min - eps <= q.pitch <= lim.pitch_max + eps
            and lim.L_min - eps <= q.L <= lim.L_max + eps
            and min(lim.h - lim.rear_extent * math.sin(q.pitch),
                    lim.h + q.L * math.sin(q.pitch)) - lim.swept_radius >= lim.floor_z)


def required_reach(p: Pose, lim: ArmLimits | None = None) -> float:
    lim = lim or ArmLimits.from_design_file()
    return math.hypot(p.x, p.y, p.z - lim.h)

