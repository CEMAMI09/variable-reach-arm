"""Minimal extension with an explicit, measured radial capture allowance."""

from __future__ import annotations
import math
from dataclasses import dataclass
from host.kinematics.arm_kinematics import ArmLimits, Pose, required_reach


@dataclass(frozen=True)
class ReachDecision:
    reachable: bool
    L_cmd: float
    extended: bool
    L_req: float
    reason: str


def select_reach(target: Pose, lim: ArmLimits | None = None,
                 margin_m: float = 0.0, capture_depth_m: float = 0.0) -> ReachDecision:
    """Target must lie at the capture reference or inside its measured pocket.

    Zero depth is the conservative default. A 3-DOF straight arm cannot catch
    arbitrary points inside its minimum-radius shell. Positive overshoot margin
    is only meaningful if a measured pocket accepts that radial displacement.
    Angular limits and approach direction are checked by the planner.
    """
    lim = lim or ArmLimits.from_design_file()
    if not all(math.isfinite(v) and v >= 0 for v in (margin_m, capture_depth_m)):
        raise ValueError("capture depth/margin must be finite and nonnegative")
    if margin_m > capture_depth_m:
        raise ValueError("reach margin cannot exceed calibrated capture depth")
    L_req = required_reach(target, lim)
    if not math.isfinite(L_req):
        return ReachDecision(False, lim.L_normal, False, L_req, "invalid_target")
    if L_req > lim.L_max + 1e-12:
        return ReachDecision(False, lim.L_max, True, L_req, "beyond_L_max")
    if L_req < lim.L_normal - capture_depth_m - 1e-12:
        return ReachDecision(False, lim.L_normal, False, L_req, "inside_normal_capture_shell")
    if L_req <= lim.L_normal + 1e-12:
        return ReachDecision(True, lim.L_normal, False, L_req, "remain_retracted")
    L_cmd = min(lim.L_max, L_req + margin_m)
    return ReachDecision(True, L_cmd, True, L_req, "extend_partial")
