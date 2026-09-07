"""Variable-reach selection: extend only as far as necessary."""

from __future__ import annotations

from dataclasses import dataclass

from host.kinematics.arm_kinematics import ArmLimits, Pose, required_reach


@dataclass
class ReachDecision:
    reachable: bool
    L_cmd: float
    extended: bool
    L_req: float
    reason: str


def select_reach(
    target: Pose,
    lim: ArmLimits | None = None,
    margin_m: float = 0.03,
) -> ReachDecision:
    lim = lim or ArmLimits()
    L_req = required_reach(target, lim)
    if L_req > lim.L_max:
        return ReachDecision(False, lim.L_max, True, L_req, "beyond_L_max")
    # Inside minimum reach: still catchable by aiming at L_min along the same ray
    if L_req < lim.L_min:
        return ReachDecision(True, lim.L_min, False, L_req, "inside_L_min_use_Lmin")
    if L_req <= lim.L_normal:
        return ReachDecision(True, lim.L_normal, False, L_req, "remain_retracted")
    L_cmd = min(lim.L_max, L_req + margin_m)
    return ReachDecision(True, L_cmd, True, L_req, "extend_partial")
