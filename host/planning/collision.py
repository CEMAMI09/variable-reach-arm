"""Conservative swept-volume checks against explicit external keep-out boxes.

A straight boom plus a radius envelope is represented. CAD self-collision,
finger motion, flex, cables, humans, and the real base are NOT inferred here.
"""
from __future__ import annotations
import math
from dataclasses import dataclass
from host.kinematics.arm_kinematics import ArmLimits, JointState, in_workspace


@dataclass(frozen=True)
class KeepoutBox:
    minimum: tuple[float, float, float]
    maximum: tuple[float, float, float]

    def __post_init__(self):
        if len(self.minimum) != 3 or len(self.maximum) != 3:
            raise ValueError("box requires three coordinates")
        if any(not math.isfinite(a) or not math.isfinite(b) or a > b
               for a, b in zip(self.minimum, self.maximum)):
            raise ValueError("invalid keep-out box")


def _trig_range(a, b, fn):
    points = [a, b]
    # All sin/cos extrema over the configured angular interval.
    points += [k * math.pi / 2 for k in range(-4, 5) if a <= k * math.pi / 2 <= b]
    values = [fn(x) for x in points]
    return min(values), max(values)


def _multiply(a, b):
    values = [x*y for x in a for y in b]
    return min(values), max(values)


def motion_clear(q0: JointState, q1: JointState, lim: ArmLimits,
                 keepouts: tuple[KeepoutBox, ...] = (), subdivisions: int = 32,
                 *, collision_model: str = "full_assembly") -> bool:
    """Fail closed for the full assembly; optionally analyze an ideal straight boom.

    Each joint moves monotonically through the same scalar progress value, so
    interval boxes contain the entire swept boom between neighboring progress
    values. Unlike point sampling this cannot skip a thin obstacle. Boxes can
    conservatively reject a safe move; a mesh collision engine would reduce that.
    The full assembly has known interference and no validated continuous envelope.
    Neither a configuration status edit nor isolated clear CAD poses qualifies it.
    Only explicit ideal_boom mode runs the simplified external-obstacle analysis.
    """
    if collision_model not in ("full_assembly", "ideal_boom"):
        raise ValueError("unknown collision model")
    if not isinstance(subdivisions, int) or not 1 <= subdivisions <= 1000:
        raise ValueError("invalid collision subdivision count")
    if collision_model == "full_assembly":
        return False  # No revision-bound, continuous self-collision validator exists.
    if not in_workspace(q0, lim) or not in_workspace(q1, lim):
        return False
    for i in range(subdivisions):
        states = [JointState(*(a + (b-a)*s for a, b in zip(
            (q0.yaw, q0.pitch, q0.L), (q1.yaw, q1.pitch, q1.L))))
            for s in (i/subdivisions, (i+1)/subdivisions)]
        yaw = sorted(q.yaw for q in states)
        pitch = sorted(q.pitch for q in states)
        length = (-lim.rear_extent, max(q.L for q in states))
        cp = _trig_range(*pitch, math.cos)
        xyz = [_multiply(length, _multiply(cp, _trig_range(*yaw, math.cos))),
               _multiply(length, _multiply(cp, _trig_range(*yaw, math.sin))),
               _multiply(length, _trig_range(*pitch, math.sin))]
        low = [min(0, bounds[0])-lim.swept_radius for bounds in xyz]
        high = [max(0, bounds[1])+lim.swept_radius for bounds in xyz]
        low[2] += lim.h
        high[2] += lim.h
        if low[2] < lim.floor_z:
            return False
        if any(all(low[j] <= box.maximum[j] and high[j] >= box.minimum[j]
                   for j in range(3)) for box in keepouts):
            return False
    return True
