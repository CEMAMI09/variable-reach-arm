#!/usr/bin/env python3
"""
Variable-reach catching arm — actuator and structural sizing calculations.

Reproducible engineering estimates for Milestone 0. Run:

    python3 engineering/sizing.py

Units: SI (m, kg, N, Nm, rad, s) unless noted.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

G = 9.81


@dataclass
class Geometry:
    h_pivot: float = 0.65  # m — shoulder height above mount
    L_min: float = 0.70  # m — retracted catcher center
    L_max: float = 1.20  # m — fully extended
    L_normal: float = 0.70  # m — preferred catch length
    extension_stroke: float = 0.50  # m
    min_overlap: float = 0.20  # m
    outer_od: float = 0.040  # m — outer tube OD
    outer_id: float = 0.036  # m
    inner_od: float = 0.032  # m
    inner_id: float = 0.028  # m
    yaw_min_deg: float = -70.0
    yaw_max_deg: float = 70.0
    pitch_min_deg: float = -15.0
    pitch_max_deg: float = 70.0


@dataclass
class Masses:
    catcher: float = 0.14  # kg
    catcher_sensors: float = 0.03  # kg
    inner_tube: float = 0.22  # kg — CF/Al sliding tube + guides portion
    outer_tube: float = 0.35  # kg — fixed to pitch
    extension_drive_moving: float = 0.05  # kg — belt clamp / carriage
    pitch_bracket: float = 0.40  # kg
    yaw_structure: float = 0.80  # kg
    base: float = 2.50  # kg


@dataclass
class DynamicsTargets:
    ext_v: float = 1.2  # m/s
    ext_a: float = 4.0  # m/s^2
    yaw_omega_deg: float = 120.0  # deg/s
    pitch_omega_deg: float = 120.0
    yaw_alpha_deg: float = 400.0  # deg/s^2 — ~0.33 s to peak speed
    pitch_alpha_deg: float = 350.0
    ball_mass: float = 0.05  # kg
    ball_v: float = 4.0  # m/s
    tip_deflection_limit: float = 0.025  # m


def deg(x: float) -> float:
    return math.radians(x)


def tube_mass_estimate(od: float, id_: float, length: float, density: float) -> float:
    area = math.pi / 4.0 * (od**2 - id_**2)
    return density * area * length


def pitch_gravitational_torque(L: float, m: Masses, pitch_rad: float) -> dict:
    """
    Approximate gravity torque about pitch axis.
    Positive pitch = up from horizontal; cos(pitch) lever for gravity when
    pitch=0 is horizontal (max gravity torque for a horizontal boom).
    Spec uses z = h + L*sin(theta_p), so theta_p=0 is horizontal.
    """
    m_tip = m.catcher + m.catcher_sensors + m.extension_drive_moving
    # Inner tube CoM ~ halfway along L for sliding member (conservative: 0.55*L)
    r_inner = 0.55 * L
    r_outer = 0.40 * Geometry.L_min  # outer mostly proximal
    # Gravity torque = sum m*g*r*cos(pitch) when pitch measured from horizontal
    lever = math.cos(pitch_rad)
    tau_tip = m_tip * G * L * lever
    tau_inner = m.inner_tube * G * r_inner * lever
    tau_outer = m.outer_tube * G * r_outer * lever
    tau_total = tau_tip + tau_inner + tau_outer
    return {
        "L_m": L,
        "pitch_deg": math.degrees(pitch_rad),
        "tau_tip_Nm": tau_tip,
        "tau_inner_Nm": tau_inner,
        "tau_outer_Nm": tau_outer,
        "tau_gravity_Nm": tau_total,
    }


def pitch_inertia(L: float, m: Masses) -> dict:
    """Rotational inertia about pitch axis (point-mass + rod approximations)."""
    m_tip = m.catcher + m.catcher_sensors + m.extension_drive_moving
    I_tip = m_tip * L**2
    # Thin rod about end ≈ (1/3) m L^2 for inner; outer shorter fixed length
    I_inner = (1.0 / 3.0) * m.inner_tube * L**2
    L_outer = Geometry.L_min
    I_outer = (1.0 / 3.0) * m.outer_tube * L_outer**2
    I_bracket = 0.5 * m.pitch_bracket * (0.08**2)  # compact bracket
    I_total = I_tip + I_inner + I_outer + I_bracket
    return {
        "L_m": L,
        "I_tip": I_tip,
        "I_inner": I_inner,
        "I_outer": I_outer,
        "I_bracket": I_bracket,
        "I_total_kgm2": I_total,
    }


def yaw_inertia(L: float, m: Masses, pitch_rad: float) -> dict:
    """Yaw inertia about vertical; depends on horizontal reach L*cos(pitch)."""
    r_h = L * abs(math.cos(pitch_rad))
    m_tip = m.catcher + m.catcher_sensors + m.extension_drive_moving
    I_tip = m_tip * r_h**2
    I_inner = (1.0 / 3.0) * m.inner_tube * r_h**2
    I_outer = (1.0 / 3.0) * m.outer_tube * (Geometry.L_min * abs(math.cos(pitch_rad))) ** 2
    I_yaw_struct = 0.5 * m.yaw_structure * (0.12**2)
    I_total = I_tip + I_inner + I_outer + I_yaw_struct
    return {"L_m": L, "pitch_deg": math.degrees(pitch_rad), "I_yaw_kgm2": I_total}


def extension_force(m: Masses, dyn: DynamicsTargets, pitch_rad: float) -> dict:
    """Belt/cable extension force: inertia + friction + gravity component along boom."""
    m_moving = m.catcher + m.catcher_sensors + m.inner_tube + m.extension_drive_moving
    F_accel = m_moving * dyn.ext_a
    # Gravity along boom: m*g*sin(pitch)
    F_grav = m_moving * G * math.sin(pitch_rad)
    F_friction = 2.5  # N — guide friction estimate (replaceable bushings)
    F_peak = F_accel + abs(F_grav) + F_friction
    F_cont = 0.3 * F_accel + abs(F_grav) + F_friction
    return {
        "m_moving_kg": m_moving,
        "F_accel_N": F_accel,
        "F_grav_N": F_grav,
        "F_friction_N": F_friction,
        "F_peak_N": F_peak,
        "F_continuous_N": F_cont,
    }


def belt_drive_sizing(F_peak: float, v_target: float, pulley_d_m: float) -> dict:
    """Timing-belt drive at proximal end."""
    r = pulley_d_m / 2.0
    tau_pulley = F_peak * r
    omega = v_target / r  # rad/s
    rpm = omega * 60.0 / (2.0 * math.pi)
    power_w = F_peak * v_target
    return {
        "pulley_diameter_mm": pulley_d_m * 1000,
        "torque_at_pulley_Nm": tau_pulley,
        "motor_rpm_at_v": rpm,
        "mech_power_W": power_w,
    }


def tip_deflection_cantilever(L: float, F: float, E: float, I_sec: float) -> float:
    """Simple cantilever tip deflection δ = F L^3 / (3 E I)."""
    return F * L**3 / (3.0 * E * I_sec)


def section_I_tube(od: float, id_: float) -> float:
    return math.pi / 64.0 * (od**4 - id_**4)


def motor_selection_pitch(
    tau_g: float,
    I: float,
    alpha: float,
    margin: float = 2.0,
    counterbalance_frac: float = 0.45,
) -> dict:
    """
    Conflict resolution: raw 2× margin on (τg+Ια) exceeds cheap NEMA23+8:1.
    Apply a pitch spring/gas counterbalance cancelling ~45% of gravity torque
    (does not cancel dynamic torque), and use 8:1 HTD5 belt on NEMA23 closed-loop.
    """
    tau_g_net = tau_g * (1.0 - counterbalance_frac)
    tau_dyn = I * alpha
    tau_fric = 0.4  # Nm estimate
    tau_peak = tau_g_net + tau_dyn + tau_fric
    tau_req = margin * tau_peak
    motor_cont = 1.2
    motor_peak = 2.2  # SERVO57-class peak assist
    ratio = 8.0
    capacity = motor_peak * ratio
    return {
        "tau_gravity_raw_Nm": tau_g,
        "counterbalance_fraction": counterbalance_frac,
        "tau_gravity_net_Nm": tau_g_net,
        "tau_dynamic_Nm": tau_dyn,
        "tau_friction_Nm": tau_fric,
        "tau_peak_load_Nm": tau_peak,
        "tau_with_margin_Nm": tau_req,
        "selected_motor": "MKS SERVO57 / NEMA23 closed-loop stepper",
        "motor_cont_Nm": motor_cont,
        "motor_peak_Nm": motor_peak,
        "belt_reduction": ratio,
        "output_peak_capacity_Nm": capacity,
        "ok": capacity >= tau_req,
    }


def motor_selection_yaw(I: float, alpha: float, margin: float = 2.0) -> dict:
    """
    Conflict resolution: NEMA17@5:1 cannot meet yaw Ια with 2× margin.
    Upgrade yaw to NEMA23 closed-loop with 6:1 belt (~+$35 vs NEMA17).
    """
    tau_dyn = I * alpha
    tau_fric = 0.25
    tau_peak = tau_dyn + tau_fric
    tau_req = margin * tau_peak
    motor_peak = 2.2
    ratio = 6.0
    capacity = motor_peak * ratio
    return {
        "tau_peak_load_Nm": tau_peak,
        "tau_with_margin_Nm": tau_req,
        "selected_motor": "MKS SERVO57 / NEMA23 closed-loop stepper (same class as pitch)",
        "motor_peak_Nm": motor_peak,
        "belt_reduction": ratio,
        "output_peak_capacity_Nm": capacity,
        "ok": capacity >= tau_req,
        "note": "NEMA17 rejected: 0.6 Nm × 5 = 3 Nm < 7.2 Nm required",
    }


def motor_selection_extension(F_peak: float, pulley_d: float, margin: float = 2.0) -> dict:
    r = pulley_d / 2.0
    tau = F_peak * r
    tau_req = margin * tau
    motor_peak = 0.6
    # Direct drive on 20mm pulley may need more torque — use 2:1 if needed
    ratio = 1.0 if motor_peak >= tau_req else 2.0
    return {
        "F_peak_N": F_peak,
        "pulley_d_mm": pulley_d * 1000,
        "tau_pulley_Nm": tau,
        "tau_with_margin_Nm": tau_req,
        "selected_motor": "MKS SERVO42C / NEMA17 closed-loop stepper",
        "motor_peak_Nm": motor_peak,
        "reduction": ratio,
        "capacity_Nm": motor_peak * ratio,
        "ok": motor_peak * ratio >= tau_req,
    }


def electrical(power_peak_axes: float, v_bus: float = 24.0) -> dict:
    i_peak = power_peak_axes / v_bus * 1.4  # inefficiency
    i_cont = i_peak * 0.35
    return {
        "v_bus": v_bus,
        "i_peak_A": i_peak,
        "i_cont_A": i_cont,
        "psu_recommendation": "24V 15A meanwell-class (360W)",
        "estop_relay": "Normally-closed e-stop cutting motor DC bus",
    }


def compare_extension_drives(F_peak: float, stroke: float, v: float) -> list[dict]:
    """Option A timing belt vs Option B Dyneema capstan vs lead screw."""
    options = []
    # A: GT2/HTD5 belt
    options.append(
        {
            "name": "Option A — HTD5 / GT2 timing belt",
            "max_force_N": 80,
            "max_velocity_mps": 2.0,
            "backlash_mm": 0.3,
            "elasticity": "low (polyurethane + steel cords)",
            "efficiency": 0.92,
            "moving_mass_penalty": "low — motor proximal",
            "reliability": "high with tensioner",
            "fabrication": "easy — COTS pulleys",
            "cost_usd": 25,
            "meets_dynamics": v <= 2.0 and F_peak <= 80,
            "score": 9,
        }
    )
    # B: Dyneema
    options.append(
        {
            "name": "Option B — Dyneema / Spectra capstan",
            "max_force_N": 200,
            "max_velocity_mps": 2.5,
            "backlash_mm": 1.0,
            "elasticity": "very low stretch but stretch under cyclic load",
            "efficiency": 0.85,
            "moving_mass_penalty": "lowest",
            "reliability": "medium — abrasion, termination",
            "fabrication": "harder terminations / routing",
            "cost_usd": 20,
            "meets_dynamics": True,
            "score": 7,
        }
    )
    # Lead screw — rejected unless dynamics ok
    lead = 0.008  # m/rev — 8mm lead
    v_screw = 3000 / 60 * lead  # 3000 rpm → 0.4 m/s
    options.append(
        {
            "name": "Lead screw (rejected baseline)",
            "max_force_N": 300,
            "max_velocity_mps": v_screw,
            "backlash_mm": 0.1,
            "elasticity": "very stiff",
            "efficiency": 0.4,
            "moving_mass_penalty": "high if nut travels; screw mass",
            "reliability": "high",
            "fabrication": "easy",
            "cost_usd": 35,
            "meets_dynamics": v_screw >= v,
            "score": 3,
        }
    )
    return options


def run_all() -> dict:
    geo = Geometry()
    m = Masses()
    dyn = DynamicsTargets()

    # Update tube masses from geometry if desired (CF density ~1600)
    density_cf = 1600.0
    m.outer_tube = tube_mass_estimate(geo.outer_od, geo.outer_id, geo.L_min + 0.05, density_cf)
    m.inner_tube = tube_mass_estimate(
        geo.inner_od, geo.inner_id, geo.extension_stroke + geo.min_overlap + 0.05, density_cf
    )

    pitch_h = 0.0  # horizontal — worst gravity
    tau_min = pitch_gravitational_torque(geo.L_min, m, pitch_h)
    tau_max = pitch_gravitational_torque(geo.L_max, m, pitch_h)
    I_min = pitch_inertia(geo.L_min, m)
    I_max = pitch_inertia(geo.L_max, m)
    yaw_I = yaw_inertia(geo.L_max, m, pitch_h)

    alpha_p = deg(dyn.pitch_alpha_deg)
    alpha_y = deg(dyn.yaw_alpha_deg)
    omega_p = deg(dyn.pitch_omega_deg)

    pitch_motor = motor_selection_pitch(tau_max["tau_gravity_Nm"], I_max["I_total_kgm2"], alpha_p)
    yaw_motor = motor_selection_yaw(yaw_I["I_yaw_kgm2"], alpha_y)

    ext_force = extension_force(m, dyn, deg(45))  # 45° — significant gravity component
    pulley_d = 0.022  # m — 22 mm pitch diameter
    belt = belt_drive_sizing(ext_force["F_peak_N"], dyn.ext_v, pulley_d)
    ext_motor = motor_selection_extension(ext_force["F_peak_N"], pulley_d)

    # Structural: tip load = catcher weight + 1g accel catch impulse estimate
    E_cf = 70e9  # Pa — conservative for CF tube (varies widely)
    I_sec = section_I_tube(geo.outer_od, geo.outer_id)
    F_static = (m.catcher + m.catcher_sensors) * G
    delta_static = tip_deflection_cantilever(geo.L_max, F_static, E_cf, I_sec)
    # Dual-tube approx: use effective I ~ 0.7 of outer when overlapped partially
    delta_eff = delta_static / 0.55  # knock-down for telescoping discontinuity
    F_dyn_catch = dyn.ball_mass * (dyn.ball_v / 0.05)  # crude 50ms impulse
    delta_dyn = tip_deflection_cantilever(geo.L_max, F_dyn_catch * 0.3, E_cf, I_sec)

    # Bearing loads (pitch shaft)
    r_bearing_span = 0.06  # m
    F_radial = (m.catcher + m.inner_tube + m.outer_tube) * G + F_dyn_catch * 0.2
    M_overhung = tau_max["tau_gravity_Nm"]
    F_bearing = F_radial / 2 + M_overhung / r_bearing_span

    drives = compare_extension_drives(ext_force["F_peak_N"], geo.extension_stroke, dyn.ext_v)
    best = max(drives, key=lambda d: d["score"] if d["meets_dynamics"] else -1)

    # Power
    p_pitch = pitch_motor["tau_peak_load_Nm"] * omega_p
    p_yaw = yaw_motor["tau_peak_load_Nm"] * deg(dyn.yaw_omega_deg)
    p_ext = belt["mech_power_W"]
    elec = electrical(p_pitch + p_yaw + p_ext)

    # Budget conflict notes
    conflicts = [
        {
            "issue": "Pitch peak torque with 2× margin exceeds NEMA23@8:1 without assistance",
            "calculation": "τ_peak≈8.1 Nm → 16.3 Nm required; capacity ~16 Nm borderline",
            "resolution": "Add pitch counterbalance cancelling ~45% of gravity; keep 8:1 HTD5 + SERVO57",
            "parameters_changed": ["counterbalance_fraction=0.45", "pitch_motor_peak=2.2 Nm"],
        },
        {
            "issue": "Yaw NEMA17@5:1 capacity 3 Nm << ~7.2 Nm required with margin",
            "resolution": "Use NEMA23 closed-loop on yaw with 6:1 belt (+~$35)",
            "parameters_changed": ["yaw_motor=NEMA23", "yaw_belt_reduction=6"],
        },
        {
            "issue": "Industrial BLDC servo kit (3 axes) would exceed $500 budget",
            "resolution": "Closed-loop steppers + host PC vision; accept lower continuous power density",
            "parameters_changed": ["actuator_class=closed_loop_stepper"],
        },
    ]
    if not pitch_motor["ok"]:
        conflicts.append(
            {
                "issue": "Pitch still insufficient after counterbalance",
                "change": "Reduce pitch_alpha to 250 deg/s² for v1 or add 10:1 planetary",
            }
        )
    if not yaw_motor["ok"]:
        conflicts.append(
            {
                "issue": "Yaw still insufficient after NEMA23 upgrade",
                "change": "Reduce yaw_alpha or increase reduction to 8:1",
            }
        )
    if delta_eff > dyn.tip_deflection_limit:
        conflicts.append(
            {
                "issue": f"Tip deflection {delta_eff*1000:.1f} mm exceeds {dyn.tip_deflection_limit*1000:.0f} mm",
                "change": "Increase outer tube OD to 45mm OR use thicker CF wall OR accept Al 6061 hybrid",
            }
        )
        # Propose OD increase
        geo2_od, geo2_id = 0.045, 0.040
        I2 = section_I_tube(geo2_od, geo2_id)
        delta2 = tip_deflection_cantilever(geo.L_max, F_static, E_cf, I2) / 0.55
        conflicts[-1]["proposed_delta_mm"] = delta2 * 1000
        conflicts[-1]["proposed_outer_od_mm"] = 45

    if best["name"].startswith("Lead"):
        conflicts.append({"issue": "Lead screw too slow", "change": "Use timing belt"})

    # Energy for one catch cycle (rough)
    E_ext = 0.5 * ext_force["m_moving_kg"] * dyn.ext_v**2 + abs(ext_force["F_grav_N"]) * 0.3
    E_rot = 0.5 * I_max["I_total_kgm2"] * omega_p**2
    energy = {"E_extension_J": E_ext, "E_pitch_J": E_rot, "E_cycle_est_J": E_ext + E_rot + 5}

    result = {
        "geometry": asdict(geo),
        "masses_updated": asdict(m),
        "pitch_gravity_Lmin": tau_min,
        "pitch_gravity_Lmax": tau_max,
        "pitch_inertia_Lmin": I_min,
        "pitch_inertia_Lmax": I_max,
        "yaw_inertia_Lmax_horizontal": yaw_I,
        "extension_force": ext_force,
        "belt_drive": belt,
        "pitch_motor": pitch_motor,
        "yaw_motor": yaw_motor,
        "extension_motor": ext_motor,
        "extension_drive_comparison": drives,
        "selected_extension_drive": best["name"],
        "structure": {
            "I_outer_m4": I_sec,
            "delta_static_ideal_mm": delta_static * 1000,
            "delta_telescoping_est_mm": delta_eff * 1000,
            "delta_catch_impulse_est_mm": delta_dyn * 1000,
            "limit_mm": dyn.tip_deflection_limit * 1000,
            "safety_factor_static_target": 2.5,
            "bearing_radial_est_N": F_bearing,
            "pitch_shaft_recommend_mm": 12,
            "bearings": "2x 6001-2RS or 6801-2RS",
        },
        "electrical": elec,
        "energy": energy,
        "conflicts_and_resolutions": conflicts,
        "assumptions": [
            "Pitch angle 0 = horizontal (matches FK z = h + L sin θp).",
            "Carbon-fiber tube E ≈ 70 GPa (conservative; verify supplier datasheet).",
            "Guide friction ≈ 2.5 N; measure on extension test rig (Milestone 1).",
            "Closed-loop steppers used instead of industrial BLDC servos to stay under $500.",
            "Initial software velocity limits will be ~40% of design targets.",
            "Counterbalance spring deferred until pitch thermal/current data from Milestone 2.",
        ],
    }
    return result


def main() -> None:
    result = run_all()
    out = Path(__file__).resolve().parent / "sizing_results.json"
    out.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
