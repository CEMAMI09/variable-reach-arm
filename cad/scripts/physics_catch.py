"""
Physics-based mid-air catch animation for FreeCAD.

- Ball: real ballistic flight (gravity)
- Arm: acceleration-limited trapezoidal joint profiles (engineering limits)
- Reaction delay, then simultaneous yaw/pitch/extend toward intercept
- Claw closes near contact based on approach timing
"""

from __future__ import annotations

import math
from dataclasses import dataclass


class Vec3:
    __slots__ = ("x", "y", "z")

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __iter__(self):
        yield self.x
        yield self.y
        yield self.z


try:
    from FreeCAD import Vector as _FCVector  # type: ignore

    def Vector(x=0.0, y=0.0, z=0.0):  # noqa: N802
        if hasattr(x, "x"):
            return _FCVector(x.x, x.y, x.z)
        return _FCVector(x, y, z)

except Exception:
    def Vector(x=0.0, y=0.0, z=0.0):  # noqa: N802
        if isinstance(x, Vec3):
            return x
        return Vec3(x, y, z)

G_MM = 9810.0  # mm/s^2
PH = 650.0
PIVOT = Vector(0.0, 0.0, PH)


@dataclass
class BallStateMM:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float


@dataclass
class JointLimits:
    # Burst rates for foam-ball intercept (geared NEMA23, light boom).
    # Short peaking above continuous ratings — used for the whip-catch move.
    yaw_v: float = math.radians(180)  # rad/s
    pitch_v: float = math.radians(240)
    ext_v: float = 1600.0  # mm/s (~1.6 m/s)
    yaw_a: float = math.radians(600)  # rad/s^2
    pitch_a: float = math.radians(800)
    ext_a: float = 5500.0  # mm/s^2 (~5.5 m/s^2)


@dataclass
class JointPose:
    yaw: float  # rad, FreeCAD convention
    pitch: float  # rad, + = boom tip DOWN
    ext: float  # mm stroke from retracted (0 = L_min visual)
    claw: float  # 0 open .. 1 closed


def boom_dir(q: JointPose) -> Vector:
    """Unit boom direction in world (from pitch pivot toward tip)."""
    cp, sp = math.cos(q.pitch), math.sin(q.pitch)
    cy, sy = math.cos(q.yaw), math.sin(q.yaw)
    lx, ly, lz = cp, 0.0, -sp
    return Vector(cy * lx - sy * ly, sy * lx + cy * ly, lz)


# Mouth plane is at L0+ext; claw cage holds the ball ahead of the hub face.
GRASP_AHEAD_MM = 95.0


def tip_from_joints(q: JointPose, L0: float = 700.0) -> Vector:
    """FK mouth-plane point (hub face) in FreeCAD animation frame."""
    L = L0 + q.ext
    d = boom_dir(q)
    return Vector(PIVOT.x + L * d.x, PIVOT.y + L * d.y, PIVOT.z + L * d.z)


def grasp_from_joints(q: JointPose, L0: float = 700.0, ahead: float = GRASP_AHEAD_MM) -> Vector:
    """Ball center when held in the closed claw cage (ahead of hub mouth)."""
    mouth = tip_from_joints(q, L0)
    d = boom_dir(q)
    return Vector(mouth.x + ahead * d.x, mouth.y + ahead * d.y, mouth.z + ahead * d.z)


def joints_from_grasp(grasp: Vector, L0: float = 700.0, L_max: float = 1200.0, ahead: float = GRASP_AHEAD_MM) -> JointPose | None:
    """IK so the claw grasp center reaches `grasp`."""
    vx = grasp.x - PIVOT.x
    vy = grasp.y - PIVOT.y
    vz = grasp.z - PIVOT.z
    Lg = math.sqrt(vx * vx + vy * vy + vz * vz)
    if Lg < 1e-6:
        return None
    # Mouth lies `ahead` short of the grasp along the same ray
    L_mouth = Lg - ahead
    if L_mouth < L0 - 20 or L_mouth > L_max + 20:
        L_mouth = min(max(L_mouth, L0), L_max)
    yaw = math.atan2(vy, vx)
    r = math.sqrt(vx * vx + vy * vy)
    pitch = math.atan2(-vz, max(r, 1e-6))
    ext = max(0.0, L_mouth - L0)
    return JointPose(yaw, pitch, ext, 0.0)


def joints_from_tip(tip: Vector, L0: float = 700.0, L_max: float = 1200.0) -> JointPose | None:
    vx = tip.x - PIVOT.x
    vy = tip.y - PIVOT.y
    vz = tip.z - PIVOT.z
    L = math.sqrt(vx * vx + vy * vy + vz * vz)
    if L < L0 - 20 or L > L_max + 20:
        L = min(max(L, L0), L_max)
    yaw = math.atan2(vy, vx)
    r = math.sqrt(vx * vx + vy * vy)
    # pitch: cos p = r/L, sin p = -vz/L  (+pitch lowers tip)
    pitch = math.atan2(-vz, max(r, 1e-6))
    ext = max(0.0, L - L0)
    return JointPose(yaw, pitch, ext, 0.0)


def ball_at(b: BallStateMM, t: float) -> Vector:
    return Vector(
        b.x + b.vx * t,
        b.y + b.vy * t,
        b.z + b.vz * t - 0.5 * G_MM * t * t,
    )


def ball_vel(b: BallStateMM, t: float) -> Vector:
    return Vector(b.vx, b.vy, b.vz - G_MM * t)


def trap_profile(dist: float, v_max: float, a_max: float, t: float) -> float:
    """
    Position along 1D bang-coast-bang from 0→dist at time t.
    Returns signed progress in [0, dist].
    """
    s = abs(dist)
    if s < 1e-9:
        return 0.0
    sign = 1.0 if dist >= 0 else -1.0
    t_acc = v_max / a_max
    d_acc = 0.5 * a_max * t_acc * t_acc
    if 2 * d_acc >= s:
        # triangular (never reaches v_max)
        t_h = math.sqrt(s / a_max)
        T = 2 * t_h
        d_h = 0.5 * s  # peak halfway
        if t <= 0:
            return 0.0
        if t >= T:
            return dist
        if t < t_h:
            return sign * 0.5 * a_max * t * t
        td = t - t_h
        # decelerate from v_peak = a_max * t_h
        return sign * (d_h + a_max * t_h * td - 0.5 * a_max * td * td)
    # trapezoid
    d_coast = s - 2 * d_acc
    t_coast = d_coast / v_max
    T = 2 * t_acc + t_coast
    if t <= 0:
        return 0.0
    if t >= T:
        return dist
    if t < t_acc:
        return sign * 0.5 * a_max * t * t
    if t < t_acc + t_coast:
        return sign * (d_acc + v_max * (t - t_acc))
    td = t - (t_acc + t_coast)
    return sign * (d_acc + d_coast + v_max * td - 0.5 * a_max * td * td)


def trap_duration(dist: float, v_max: float, a_max: float) -> float:
    s = abs(dist)
    if s < 1e-9:
        return 0.0
    t_acc = v_max / a_max
    d_acc = 0.5 * a_max * t_acc * t_acc
    if 2 * d_acc >= s:
        return 2 * math.sqrt(s / a_max)
    return 2 * t_acc + (s - 2 * d_acc) / v_max


def sync_move(q0: JointPose, q1: JointPose, lim: JointLimits, t: float) -> JointPose:
    """All axes start together; each follows its own trap profile."""
    dy = q1.yaw - q0.yaw
    dp = q1.pitch - q0.pitch
    de = q1.ext - q0.ext
    return JointPose(
        q0.yaw + trap_profile(dy, lim.yaw_v, lim.yaw_a, t),
        q0.pitch + trap_profile(dp, lim.pitch_v, lim.pitch_a, t),
        q0.ext + trap_profile(de, lim.ext_v, lim.ext_a, t),
        q0.claw,
    )


def sync_move_in_time(
    q0: JointPose, q1: JointPose, lim: JointLimits, t: float, T: float
) -> JointPose:
    """
    Reach q1 in exactly T seconds by time-scaling each axis profile.
    Uses the full intercept window (smoother than racing then waiting).
    """
    if T < 1e-6:
        return JointPose(q1.yaw, q1.pitch, q1.ext, q0.claw)
    nat = move_duration(q0, q1, lim)
    # If physically impossible at limits, fall back to uncapped traps
    if nat > T + 1e-6:
        return sync_move(q0, q1, lim, t)
    # Map wall time so each axis completes at T (scale profile time)
    u = 0.0 if t <= 0 else (1.0 if t >= T else t / T)
    # Evaluate each profile at fraction u of its natural duration
    dy = q1.yaw - q0.yaw
    dp = q1.pitch - q0.pitch
    de = q1.ext - q0.ext
    ty = trap_duration(dy, lim.yaw_v, lim.yaw_a)
    tp = trap_duration(dp, lim.pitch_v, lim.pitch_a)
    te = trap_duration(de, lim.ext_v, lim.ext_a)
    return JointPose(
        q0.yaw + trap_profile(dy, lim.yaw_v, lim.yaw_a, u * max(ty, 1e-9)),
        q0.pitch + trap_profile(dp, lim.pitch_v, lim.pitch_a, u * max(tp, 1e-9)),
        q0.ext + trap_profile(de, lim.ext_v, lim.ext_a, u * max(te, 1e-9)),
        q0.claw,
    )


def move_duration(q0: JointPose, q1: JointPose, lim: JointLimits) -> float:
    return max(
        trap_duration(q1.yaw - q0.yaw, lim.yaw_v, lim.yaw_a),
        trap_duration(q1.pitch - q0.pitch, lim.pitch_v, lim.pitch_a),
        trap_duration(q1.ext - q0.ext, lim.ext_v, lim.ext_a),
    )


def plan_physics_catch(
    q_start: JointPose,
    ball: BallStateMM,
    lim: JointLimits | None = None,
    reaction_s: float = 0.18,
    t_max: float = 1.6,
    dt: float = 0.02,
    prefer_elevated: bool = True,
) -> dict:
    """
    Search ballistic times for a reachable intercept after reaction delay.
    Prefer elevated catches (z well above base / negative pitch).
    """
    lim = lim or JointLimits()
    best = None
    t = reaction_s + 0.05
    while t <= t_max:
        p = ball_at(ball, t)
        if p.z < 350:  # below useful mid-air window
            t += dt
            continue
        if p.z > 1550:
            t += dt
            continue
        q = joints_from_grasp(p)
        if q is None:
            t += dt
            continue
        # workspace soft limits
        if abs(math.degrees(q.yaw)) > 70:
            t += dt
            continue
        if not (-70 <= math.degrees(q.pitch) <= 35):
            t += dt
            continue
        if q.ext > 500 or q.ext < 0:
            t += dt
            continue
        # Verify grasp actually near ball (after clamp)
        g = grasp_from_joints(q)
        miss = math.sqrt((g.x - p.x) ** 2 + (g.y - p.y) ** 2 + (g.z - p.z) ** 2)
        if miss > 40.0:
            t += dt
            continue
        travel = move_duration(q_start, q, lim)
        # must arrive by t, starting after reaction
        if travel <= (t - reaction_s):
            pitch_deg = math.degrees(q.pitch)
            # Strongly reward mid-air lofted, long-reach intercepts
            elev = max(0.0, p.z - 700.0)
            loft = max(0.0, -pitch_deg - 8.0)  # tip angled up
            reach = max(0.0, q.ext - 280.0)  # prefer near-full extension
            if prefer_elevated and elev < 150 and loft < 4:
                t += dt
                continue
            cost = (
                0.35 * t
                + 0.25 * travel
                - 0.0010 * elev
                - 0.040 * loft
                - 0.0012 * reach
            )
            cand = {
                "t_catch": t,
                "q_catch": q,
                "p_catch": p,
                "travel": travel,
                "cost": cost,
            }
            if best is None or cost < best["cost"]:
                best = cand
        t += dt
    return best


def claw_close_profile(t_rel: float, close_duration: float = 0.09) -> float:
    """Smooth open→closed over close_duration seconds relative to contact."""
    if t_rel <= -0.04:
        return 0.05
    if t_rel >= close_duration:
        return 0.98
    # start closing slightly before contact
    u = (t_rel + 0.04) / (close_duration + 0.04)
    u = max(0.0, min(1.0, u))
    # smoothstep
    u = u * u * (3 - 2 * u)
    return 0.05 + 0.93 * u


def build_timeline(
    duration_s: float = 2.8,
    fps: float = 24.0,
) -> tuple[list[tuple[float, JointPose, Vector]], dict]:
    """
    Returns list of (t, joint_pose, ball_pos_mm) and plan metadata.

    Story beat:
      1) arm held pointing down (retracted)
      2) ball thrown on a long ballistic loft
      3) after reaction delay — fast pitch-up + full extension whip
      4) claw snap at intercept, short absorb, settle while holding
    """
    lim = JointLimits()
    # Clear downward ready pose (retracted) — the “before” beat
    q0 = JointPose(
        yaw=math.radians(8),
        pitch=math.radians(32),
        ext=25.0,
        claw=0.05,
    )

    # Long-hang loft (~6 m/s up): ball rises into view while arm still down,
    # then descending/apex window allows a near-full-reach elevated catch.
    ball = BallStateMM(
        x=1450.0,
        y=350.0,
        z=220.0,
        vx=-390.0,
        vy=-240.0,
        vz=6000.0,
    )

    reaction = 0.38  # hold down pose while throw is visible
    plan = plan_physics_catch(
        q0, ball, lim, reaction_s=reaction, t_max=1.8, prefer_elevated=True
    )
    if plan is None:
        ball = BallStateMM(1500.0, 380.0, 180.0, -420.0, -260.0, 5800.0)
        plan = plan_physics_catch(
            q0, ball, lim, reaction_s=reaction, t_max=1.8, prefer_elevated=True
        )
    if plan is None:
        plan = plan_physics_catch(
            q0, ball, lim, reaction_s=reaction, t_max=1.8, prefer_elevated=False
        )
    if plan is None:
        raise RuntimeError("No feasible physics intercept found")

    t_catch = plan["t_catch"]
    q_catch = plan["q_catch"]
    p_catch = plan["p_catch"]

    # Absorb: short boom retract while holding (impulse compliance)
    q_hold = JointPose(
        q_catch.yaw,
        q_catch.pitch + math.radians(5),
        max(0.0, q_catch.ext - 110.0),
        0.98,
    )
    # Settle still somewhat elevated (show the catch succeeded)
    q_home = JointPose(
        yaw=math.radians(6),
        pitch=math.radians(-8),
        ext=max(120.0, q_catch.ext * 0.35),
        claw=0.98,
    )
    T_home = max(move_duration(q_hold, q_home, lim), 0.55)

    n = int(round(duration_s * fps)) + 1
    frames = []
    for i in range(n):
        t = i / fps

        if t < reaction:
            # Beat 1–2: arm down; ball already in flight
            q = JointPose(q0.yaw, q0.pitch, q0.ext, 0.05)
            bp = ball_at(ball, t)
        elif t < t_catch:
            # Beat 3: max-rate whip (not time-stretched) — arrives fast
            tau = t - reaction
            q = sync_move(q0, q_catch, lim, tau)
            if tau >= move_duration(q0, q_catch, lim):
                q = JointPose(q_catch.yaw, q_catch.pitch, q_catch.ext, q.claw)
            q.claw = claw_close_profile(t - t_catch, close_duration=0.11)
            free = ball_at(ball, t)
            grasp = grasp_from_joints(q)
            # Soft capture: last 90 ms, pull ball into the claw cage
            lead = t_catch - t
            if lead < 0.09:
                u = 1.0 - lead / 0.09
                u = u * u * (3 - 2 * u)
                bp = Vector(
                    free.x + u * (grasp.x - free.x),
                    free.y + u * (grasp.y - free.y),
                    free.z + u * (grasp.z - free.z),
                )
            else:
                bp = free
        elif t < t_catch + 0.25:
            # contact + compliance retract — ball locked in grasp
            tau = t - t_catch
            u = min(1.0, tau / 0.25)
            u = u * u * (3 - 2 * u)
            q = JointPose(
                q_catch.yaw,
                q_catch.pitch + u * (q_hold.pitch - q_catch.pitch),
                q_catch.ext + u * (q_hold.ext - q_catch.ext),
                0.98,
            )
            bp = grasp_from_joints(q)
        else:
            tau = t - (t_catch + 0.25)
            q = sync_move_in_time(q_hold, q_home, lim, tau, T_home)
            q.claw = 0.98
            q.ext = max(0.0, q.ext)
            bp = grasp_from_joints(q)

        if bp.z < 40:
            bp = Vector(bp.x, bp.y, 40)
        frames.append((t, q, bp))

    meta = {
        "t_catch": t_catch,
        "reaction": reaction,
        "p_catch": p_catch,
        "q_catch": q_catch,
        "q0": q0,
        "travel": plan["travel"],
        "ball": ball,
        "fps": fps,
        "duration": duration_s,
        "grasp_ahead": GRASP_AHEAD_MM,
    }
    return frames, meta
