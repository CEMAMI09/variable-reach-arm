"""Connect executed profiles to the shared extension-dependent engineering model.

Sampled load estimates are diagnostics; extrema between samples, flexibility,
contact and the missing motor torque-speed curves prevent hardware approval.
"""
from __future__ import annotations
from host.kinematics.arm_kinematics import ArmLimits
from host.trajectories.quintic import QuinticSegment


def profile_demand(segments: list[QuinticSegment], lim: ArmLimits,
                   samples: int = 201, loaded: bool = True) -> dict:
    from engineering.review_sizing import parameters, dynamics, guide_load
    if len(segments) != 3 or not isinstance(samples, int) or not 3 <= samples <= 10001:
        raise ValueError("three segments and bounded sample count required")
    if any((s.t0,s.T) != (segments[0].t0,segments[0].T) for s in segments):
        raise ValueError("segments must be synchronized")
    p = parameters()
    geometry = p["geometry"]
    if abs(lim.L_min-geometry["normal_reach_m"]) > 1e-9 or abs(lim.L_max-geometry["maximum_reach_m"]) > 1e-9:
        raise ValueError("simulation and engineering reach references disagree")
    peaks = {"pitch_nm":0.0, "yaw_nm":0.0, "extension_n":0.0}
    inertia_values = []
    friction = p["drivetrain"]
    for i in range(samples):
        t = segments[0].t0+segments[0].T*i/(samples-1)
        states = [s.sample(t) for s in segments]
        q,v,a = [tuple(s[j] for s in states) for j in range(3)]
        extension = q[2]-lim.L_min
        # Only roundoff at endpoints is clamped; out-of-range profiles are errors.
        if not -1e-10 <= extension <= geometry["extension_stroke_m"]+1e-10:
            raise ValueError("profile outside model extension range")
        extension = min(max(extension,0),geometry["extension_stroke_m"])
        demand = dynamics(extension,q[1],v,a,p,loaded)
        guide = guide_load(extension,p=p,pitch=q[1],rates=v,accelerations=a)
        peaks["pitch_nm"] = max(peaks["pitch_nm"],abs(demand["pitch_nm"])+friction["pitch_friction_nm_assumed"])
        peaks["yaw_nm"] = max(peaks["yaw_nm"],abs(demand["yaw_nm"])+friction["yaw_friction_nm_assumed"])
        peaks["extension_n"] = max(peaks["extension_n"],abs(demand["extension_n"])+guide["friction_n"])
        inertia_values.append(demand["pitch_inertia_kgm2"])
    return {"sampled_required_load_peaks":peaks,
            "pitch_inertia_min_max_kgm2":[min(inertia_values),max(inertia_values)],
            "samples":samples, "loaded":loaded, "motor_capacity_qualified":False,
            "limitation":"sampled rigid-body demand with assumed friction/rotor inertia; no contact or motor capacity proof"}
