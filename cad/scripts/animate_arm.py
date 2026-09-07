"""
Animate connected VariableReachArm — yaw, pitch, extend, 3×2-joint claw grab.

Critical: every moving part uses the SAME rigid transform from a clean REST pose
so the catcher never floats off the inner boom.
"""

from __future__ import annotations

import math
import os
import sys

import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Placement, Rotation, Vector

SCRIPT_DIR = "/Users/user/Documents/chat/variable-reach-arm/cad/scripts"
sys.path.insert(0, SCRIPT_DIR)

DOC_NAME = "VariableReachArm"
FCSTD = "/Users/user/Documents/chat/variable-reach-arm/cad/freecad/VariableReachArm.FCStd"
FRAME_DIR = "/Users/user/Documents/chat/variable-reach-arm/cad/animations/frames"
PH = 650.0
PIVOT = Vector(0, 0, PH)

FIXED = {
    "BasePlate",
    "YawColumn",
    "YawMotor",
    "ElectronicsEnclosure",
    "Parameters",
}

# Rotate with yaw only
YAW_ONLY = {
    "YawHub",
}

# Rotate with yaw+pitch (shoulder / outer boom)
SHOULDER = {
    "PitchCheek_L",
    "PitchCheek_R",
    "PitchShaft",
    "PitchMotor",
    "OuterBoom",
    "Guide_1",
    "Guide_2",
    "ExtensionMotor",
    "ExtensionPulley",
    "CableGuide_1",
    "CableGuide_2",
    "CableGuide_3",
    "ExtensionStop_Min",
    "ExtensionStop_Max",
}

# Translate with extension, then same yaw+pitch as shoulder
SLIDING = {
    "InnerBoom",
    "CatcherHub",
    "CatcherFunnel",
    "CatcherCradle",
    "CatcherAdapter",
    "CatcherRib_1",
    "CatcherRib_2",
    "CatcherRib_3",
    "CatcherFinger_1",
    "CatcherFinger_2",
    "CatcherFinger_3",
}

_claw_open = 0.15


def ensure_doc():
    if DOC_NAME not in App.listDocuments():
        App.open(FCSTD)
    return App.getDocument(DOC_NAME)


def rebuild_rest_assembly(doc):
    """Full clean rest rebuild so nothing is left mid-pose."""
    import build_arm
    import catcher_fingers as CF
    import importlib

    importlib.reload(build_arm)
    importlib.reload(CF)

    if DOC_NAME in App.listDocuments():
        App.closeDocument(DOC_NAME)
    build_arm.build()
    doc = App.getDocument(DOC_NAME)

    CF.rebuild_catcher(doc, open_frac=0.15)
    CF.export_print_stl()
    doc.recompute()
    doc.saveAs(FCSTD)
    return doc


def capture_rest(doc):
    rest = {}
    for obj in doc.Objects:
        if hasattr(obj, "Placement"):
            rest[obj.Name] = Placement(obj.Placement)
    return rest


def posed_placement(rest_pl: Placement, yaw_deg: float, pitch_deg: float, ext_mm: float) -> Placement:
    """T = Ryaw * Rpitch * Trans_x(ext) applied to rest placement."""
    ext = Placement(Vector(ext_mm, 0, 0), Rotation())
    # Pitch about world Y through pivot: p' = pivot + Ry*(p - pivot)
    # Represent as placement multiply carefully using point mapping of Base and Rotation.

    # First apply extension in rest frame (along boom +X at rest)
    p0 = ext.multiply(rest_pl)

    # Pitch about pivot
    rp = Rotation(Vector(0, 1, 0), pitch_deg)
    base = Vector(p0.Base)
    base_p = PIVOT + rp.multVec(base - PIVOT)
    rot_p = rp.multiply(p0.Rotation)
    p1 = Placement(base_p, rot_p)

    # Yaw about world Z through origin
    ry = Rotation(Vector(0, 0, 1), yaw_deg)
    base_y = ry.multVec(Vector(p1.Base))
    rot_y = ry.multiply(p1.Rotation)
    return Placement(base_y, rot_y)


def set_pose(doc, rest, yaw_deg, pitch_deg, ext_mm):
    global _claw_open
    import catcher_fingers as CF

    for name, pl in rest.items():
        obj = doc.getObject(name)
        if obj is None or name in FIXED:
            continue
        if name in YAW_ONLY:
            obj.Placement = posed_placement(pl, yaw_deg, 0.0, 0.0)
        elif name in SHOULDER:
            obj.Placement = posed_placement(pl, yaw_deg, pitch_deg, 0.0)
        elif name in SLIDING:
            # Fingers: update shape for claw opening, keep rest placement then pose
            if name.startswith("CatcherFinger_"):
                continue
            obj.Placement = posed_placement(pl, yaw_deg, pitch_deg, ext_mm)

    # Claws: refresh geometry at current open_frac, restore REST placement, then pose
    claw_shape, _, _ = CF.make_claw_solid(_claw_open)
    for i in range(1, CF.N_FINGERS + 1):
        name = f"CatcherFinger_{i}"
        obj = doc.getObject(name)
        if not obj or name not in rest:
            continue
        obj.Shape = claw_shape.copy()
        obj.Placement = posed_placement(rest[name], yaw_deg, pitch_deg, ext_mm)
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = (0.1, 0.82, 0.4)

    doc.recompute()


def set_claw_open_frac(frac: float):
    global _claw_open
    _claw_open = max(0.0, min(1.0, frac))


def ease(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def trajectory_demo(frame: int, n: int):
    """Original slower demo: yaw → pitch → extend → claw → retract."""
    u = frame / max(n - 1, 1)
    if u < 0.22:
        s = ease(u / 0.22)
        return -35 + 70 * s, 5.0, 0.0, 0.08
    if u < 0.40:
        s = ease((u - 0.22) / 0.18)
        return 35.0, 5 + 40 * s, 0.0, 0.08
    if u < 0.58:
        s = ease((u - 0.40) / 0.18)
        return 35.0 - 15 * s, 45.0 - 8 * s, 450.0 * s, 0.08
    if u < 0.70:
        s = ease((u - 0.58) / 0.12)
        return 20.0, 37.0, 450.0, 0.08 + 0.90 * s
    if u < 0.80:
        return 20.0, 37.0, 450.0, 0.98
    if u < 0.90:
        s = ease((u - 0.80) / 0.10)
        return 20.0, 37.0, 450.0 * (1 - s), 0.98 - 0.90 * s
    s = ease((u - 0.90) / 0.10)
    return 20.0 * (1 - s), 37.0 * (1 - s) + 5.0 * s, 0.0, 0.08


def ease_out(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * t


def trajectory_catch_fast(frame: int, n: int):
    """
    Longer story beat:
      1) idle with arm pointing DOWN
      2) ball is thrown while arm still down
      3) whip UP + blast extend + snap claws mid-air
      4) hold catch elevated
      5) return
    FreeCAD pitch about +Y: positive = boom DOWN, negative = boom UP.
    """
    u = frame / max(n - 1, 1)

    down = (8.0, 28.0, 30.0, 0.08)  # pointing downward, retracted
    up_aim = (18.0, -42.0, 80.0, 0.05)  # elevated, starting extend
    caught = (18.0, -42.0, 420.0, 0.98)

    # 0–24%: hold downward ready (ball throw begins during this)
    if u < 0.24:
        return down

    # 24–40%: WHIP from down → up (fast reaction once ball is airborne)
    if u < 0.40:
        s = ease_out((u - 0.24) / 0.16)
        return (
            down[0] + (up_aim[0] - down[0]) * s,
            down[1] + (up_aim[1] - down[1]) * s,
            down[2] + (up_aim[2] - down[2]) * s,
            0.05,
        )

    # 40–58%: BLAST extend while aimed up (claw open)
    if u < 0.58:
        s = ease_out((u - 0.40) / 0.18)
        return up_aim[0], up_aim[1], 80.0 + (420.0 - 80.0) * s, 0.05

    # 58–68%: SNAP claws at altitude
    if u < 0.68:
        s = ease_out((u - 0.58) / 0.10)
        return caught[0], caught[1], 420.0, 0.05 + 0.93 * s

    # 68–82%: hold catch in the air + short absorb
    if u < 0.82:
        s = ease((u - 0.68) / 0.14)
        return 18.0, -42.0, 420.0 - 40.0 * s, 0.98

    # 82–100%: return while retaining ball
    s = ease((u - 0.82) / 0.18)
    return (
        18.0 * (1 - s) + down[0] * s,
        -42.0 * (1 - s) + 12.0 * s,
        380.0 * (1 - s) + 40.0 * s,
        0.98,
    )


def ball_world_pos(frame: int, n: int, intercept_tip: Vector, catcher_tip: Vector | None):
    """
    Ball starts visible in thrower's hand, releases while arm is still down,
    arcs high, meets tip during claw snap.
    """
    u = frame / max(n - 1, 1)

    release_u = 0.08  # release early so throw is visible during down-hold
    catch_u = 0.63  # during claw snap

    p_hand = Vector(1550.0, 480.0, 160.0)
    p1 = Vector(intercept_tip)
    ctrl = Vector(
        0.45 * (p_hand.x + p1.x),
        0.50 * (p_hand.y + p1.y),
        max(p_hand.z, p1.z) + 340.0,
    )

    if u < release_u:
        t = u / max(release_u, 1e-6)
        return p_hand + Vector(-30.0 * t, -20.0 * t, 50.0 * t)

    if u < catch_u:
        t = (u - release_u) / (catch_u - release_u)
        t = ease_out(max(0.0, min(1.0, t)))
        omt = 1 - t
        return omt * omt * p_hand + 2 * omt * t * ctrl + t * t * p1

    if catcher_tip is not None:
        return catcher_tip
    return p1


def ensure_ball(doc):
    import Part

    ball = doc.getObject("ThrownBall")
    if ball is None:
        ball = doc.addObject("Part::Feature", "ThrownBall")
    ball.Shape = Part.makeSphere(32.0)  # ~64 mm foam ball (fits claw cage)
    if ball.ViewObject:
        ball.ViewObject.ShapeColor = (1.0, 0.45, 0.05)  # bright orange
        ball.ViewObject.Visibility = True
        try:
            ball.ViewObject.Transparency = 0
        except Exception:
            pass
    return ball


def estimate_catcher_tip(doc) -> Vector:
    """Use closed-claw / funnel mouth region as tip proxy."""
    hub = doc.getObject("CatcherHub")
    if hub is None:
        return Vector(900, 0, 900)
    bb = hub.Shape.BoundBox
    # Slightly past hub along its longest extent from pivot-ish
    return Vector(bb.Center.x + bb.XLength * 0.35, bb.Center.y, bb.Center.z)


def trajectory(frame: int, n: int):
    return trajectory_demo(frame, n)


def animate_and_export(
    n_frames: int = 40,
    width: int = 960,
    height: int = 600,
    mode: str = "demo",
    frame_dir: str | None = None,
    rebuild: bool = True,
    rest=None,
    doc=None,
):
    """
    mode: 'demo' | 'catch_fast'
    """
    if rebuild or doc is None:
        doc = rebuild_rest_assembly(ensure_doc())
    else:
        doc = doc or ensure_doc()

    Gui.ActiveDocument = Gui.getDocument(DOC_NAME)
    view = Gui.activeDocument().activeView()
    view.viewIsometric()
    Gui.SendMsgToActiveView("ViewFit")

    if rest is None:
        rest = capture_rest(doc)

    out_dir = frame_dir or FRAME_DIR
    os.makedirs(out_dir, exist_ok=True)
    for f in os.listdir(out_dir):
        if f.endswith(".png"):
            os.remove(os.path.join(out_dir, f))

    traj = trajectory_catch_fast if mode == "catch_fast" else trajectory_demo
    ball = None
    physics_frames = None
    if mode == "catch_fast":
        import physics_catch as PC
        import importlib

        importlib.reload(PC)
        ball = ensure_ball(doc)
        # Let the held ball read through the hub mouth
        hub = doc.getObject("CatcherHub")
        if hub and hub.ViewObject:
            hub.ViewObject.Transparency = 35
        funnel = doc.getObject("CatcherFunnel")
        if funnel and funnel.ViewObject:
            funnel.ViewObject.Transparency = 25
        # Story length: down hold + throw + whip + catch + short settle
        fps = 24.0
        duration = 2.05
        physics_frames, meta = PC.build_timeline(duration_s=duration, fps=fps)
        n_frames = len(physics_frames)
        print(
            f"physics catch: t_catch={meta['t_catch']:.3f}s travel={meta['travel']:.3f}s "
            f"intercept=({meta['p_catch'].x:.0f},{meta['p_catch'].y:.0f},{meta['p_catch'].z:.0f}) "
            f"reaction={meta['reaction']:.2f}s frames={n_frames}"
        )
        q0 = meta["q0"]
        set_pose(
            doc,
            rest,
            math.degrees(q0.yaw),
            math.degrees(q0.pitch),
            q0.ext,
        )

    paths = []
    for i in range(n_frames):
        if physics_frames is not None:
            t, q, bp = physics_frames[i]
            yaw = math.degrees(q.yaw)
            pitch = math.degrees(q.pitch)
            ext = q.ext
            claw = q.claw
            set_claw_open_frac(claw)
            set_pose(doc, rest, yaw, pitch, ext)
            if ball is not None:
                ball.Placement = Placement(bp, Rotation())
        else:
            yaw, pitch, ext, claw = traj(i, n_frames)
            set_claw_open_frac(claw)
            set_pose(doc, rest, yaw, pitch, ext)

        if i == 0:
            Gui.SendMsgToActiveView("ViewFit")
        out = os.path.join(out_dir, f"frame_{i:03d}.png")
        view.saveImage(out, width, height, "Current")
        paths.append(out)
        print(
            f"[{mode}] frame {i+1}/{n_frames} yaw={yaw:.1f} pitch={pitch:.1f} "
            f"ext={ext:.0f} claw={claw:.2f}"
        )

    set_claw_open_frac(0.08)
    set_pose(doc, rest, 0.0, 0.0, 0.0)
    if ball is not None and ball.ViewObject:
        ball.ViewObject.Visibility = False
    import catcher_fingers as CF

    CF.export_print_stl()
    doc.saveAs(FCSTD)
    print("DONE", mode, len(paths))
    return paths, doc, rest


if __name__ == "__main__":
    animate_and_export(mode="demo")
