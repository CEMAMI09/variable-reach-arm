"""
Connected catcher + 3× two-joint articulated claws.

Why 2-joint claws (not continuum / not 4 soft tentacles):
- Tripod of 3 fingers is the stable minimum for a sphere.
- Two revolute joints (proximal + distal) give a real open/close cage,
  printable as rigid links + TPU tip pads (or living hinges).
- Continuum bead-fingers looked disconnected, were hard to pose, and are
  worse for predictable retention timing than a simple claw close.
- Keep the funnel+cradle as a forgiving backstop behind the claws.

Assembly (all on boom +X, connected):
  InnerBoom tip → CatcherHub → Funnel/Cradle + 3 claw mounts
  Each claw: Mount → Proximal link → Distal link → Tip pad
"""

from __future__ import annotations

import math

import FreeCAD as App
import MeshPart
import Part
from FreeCAD import Placement, Rotation, Vector

PH = 650.0
BOOM_START = 50.0
# Retracted: catcher hub face (mouth plane) distance from pitch center along +X
L_HUB = 700.0
INNER_OD = 32.0
CATCHER_OD = 140.0
CATCHER_ID = 72.0
FUNNEL_DEPTH = 110.0
N_FINGERS = 3

# Link lengths (mm) — chunky so joints read in screenshots/GIF
L_PROX = 58.0
L_DIST = 52.0
LINK_W = 22.0
LINK_T = 14.0


def _clear_catcher(doc):
    for name in list(o.Name for o in doc.Objects):
        if name.startswith("Catcher"):
            doc.removeObject(name)


def _box_link(length, width, thick):
    """Link along +X from 0..length, centered in YZ."""
    return Part.makeBox(length, width, thick, Vector(0, -width / 2, -thick / 2))


def _joint_sphere(r=6.0):
    return Part.makeSphere(r)


def make_claw_solid(open_frac: float):
    """
    Single claw in local frame:
      origin at mount hinge on rim, +X forward (out of mouth),
      closes by rotating about +Y (curl toward -Z in this local frame;
      world placement will map -Z to radial inward).

    open_frac: 0 = fully open (catch ready), 1 = fully closed (grab).
    """
    # Joint angles (deg): open flares slightly outward; closed curls INWARD toward axis.
    # Local +Y rotation: +angle moves tip toward local -Z, which placement maps to radial inward.
    q1_open, q1_closed = -32.0, 52.0   # proximal
    q2_open, q2_closed = -22.0, 68.0   # distal
    q1 = q1_open + (q1_closed - q1_open) * open_frac
    q2 = q2_open + (q2_closed - q2_open) * open_frac

    mount = Part.makeBox(20, 28, 16, Vector(-10, -14, -8))
    j0 = _joint_sphere(9)
    prox = _box_link(L_PROX, LINK_W, LINK_T)
    j1 = _joint_sphere(8)
    j1.translate(Vector(L_PROX, 0, 0))
    dist = _box_link(L_DIST, LINK_W * 0.92, LINK_T * 0.92)
    tip = Part.makeSphere(11)
    tip.translate(Vector(L_DIST, 0, 0))

    # Assemble distal chain at origin, then place with joint rotations
    distal_asm = dist.fuse(tip)
    # rotate distal about Y at its base (joint1), then move to end of proximal
    distal_asm.rotate(Vector(0, 0, 0), Vector(0, 1, 0), q2)
    distal_asm.translate(Vector(L_PROX, 0, 0))

    prox_asm = prox.fuse(j1).fuse(distal_asm)
    prox_asm.rotate(Vector(0, 0, 0), Vector(0, 1, 0), q1)

    claw = mount.fuse(j0).fuse(prox_asm)
    return claw.removeSplitter(), q1, q2


def rebuild_catcher(doc, open_frac: float = 0.15):
    """
    Build catcher rigidly on the retracted inner-boom tip.
    Hub center on axis at x = BOOM_START + L_HUB - small; mouth faces +X.
    """
    _clear_catcher(doc)

    # Inner boom tip / hub location (retracted rest). Match InnerBoom if present.
    hub_x = BOOM_START + L_HUB  # mouth plane ~ here
    # Funnel extends backward toward shoulder from mouth
    back_x = hub_x - FUNNEL_DEPTH

    # --- Hub sleeve clamped on inner tube (long engagement so it never looks floating) ---
    hub_len = 55.0
    hub_outer = Part.makeCylinder(
        INNER_OD / 2 + 12, hub_len, Vector(hub_x - hub_len - 5, 0, PH), Vector(1, 0, 0)
    )
    hub_bore = Part.makeCylinder(
        INNER_OD / 2 + 0.2, hub_len + 4, Vector(hub_x - hub_len - 7, 0, PH), Vector(1, 0, 0)
    )
    flange = Part.makeCylinder(CATCHER_OD / 2 - 5, 10, Vector(hub_x - 12, 0, PH), Vector(1, 0, 0))
    flange_bore = Part.makeCylinder(INNER_OD / 2 + 0.2, 14, Vector(hub_x - 14, 0, PH), Vector(1, 0, 0))
    hub = doc.addObject("Part::Feature", "CatcherHub")
    hub.Shape = hub_outer.cut(hub_bore).fuse(flange.cut(flange_bore))
    if hub.ViewObject:
        hub.ViewObject.ShapeColor = (0.35, 0.35, 0.38)

    # --- Funnel (connected to hub) ---
    outer = Part.makeCylinder(CATCHER_OD / 2, FUNNEL_DEPTH, Vector(back_x, 0, PH), Vector(1, 0, 0))
    inner = Part.makeCylinder(CATCHER_ID / 2, FUNNEL_DEPTH + 4, Vector(back_x - 2, 0, PH), Vector(1, 0, 0))
    # Open front face at hub_x; leave mouth open
    funnel = doc.addObject("Part::Feature", "CatcherFunnel")
    funnel.Shape = outer.cut(inner)
    if funnel.ViewObject:
        funnel.ViewObject.ShapeColor = (0.25, 0.72, 0.88)

    # Structural ribs connecting hub to funnel (so it doesn't look floating)
    for i in range(N_FINGERS):
        ang = i * (360.0 / N_FINGERS)
        rad = math.radians(ang)
        r = (INNER_OD / 2 + CATCHER_OD / 2) / 2
        y = r * math.cos(rad)
        z = PH + r * math.sin(rad)
        rib = Part.makeBox(FUNNEL_DEPTH - 10, 8, 8, Vector(back_x + 5, y - 4, z - 4))
        obj = doc.addObject("Part::Feature", f"CatcherRib_{i+1}")
        obj.Shape = rib
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = (0.3, 0.55, 0.65)

    # Cradle at back
    cradle = doc.addObject("Part::Feature", "CatcherCradle")
    cradle.Shape = Part.makeCylinder(
        CATCHER_ID / 2 + 6, 12, Vector(back_x, 0, PH), Vector(1, 0, 0)
    )
    if cradle.ViewObject:
        cradle.ViewObject.ShapeColor = (0.92, 0.42, 0.28)

    # Solid adapter filling boom→funnel so catcher never looks floating
    adapter_outer = Part.makeCylinder(70, FUNNEL_DEPTH - 20, Vector(back_x, 0, PH), Vector(1, 0, 0))
    adapter_bore = Part.makeCylinder(
        INNER_OD / 2 + 0.05, FUNNEL_DEPTH, Vector(back_x - 2, 0, PH), Vector(1, 0, 0)
    )
    adapter = doc.addObject("Part::Feature", "CatcherAdapter")
    adapter.Shape = adapter_outer.cut(adapter_bore)
    if adapter.ViewObject:
        adapter.ViewObject.ShapeColor = (0.28, 0.42, 0.52)

    # --- 3 articulated claws on mouth rim ---
    claw_shape, _, _ = make_claw_solid(open_frac)
    rim_r = CATCHER_OD / 2 - 6
    for i in range(N_FINGERS):
        ang = i * (360.0 / N_FINGERS)  # 0, 120, 240
        rad = math.radians(ang)
        y = rim_r * math.cos(rad)
        z = PH + rim_r * math.sin(rad)
        x = hub_x - 2
        # Local -Z → radial inward
        r_spin = Rotation(Vector(1, 0, 0), ang - 90.0)

        obj = doc.addObject("Part::Feature", f"CatcherFinger_{i+1}")
        obj.Shape = claw_shape.copy()
        obj.Placement = Placement(Vector(x, y, z), r_spin)
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = (0.1, 0.82, 0.4)

    doc.recompute()
    return hub_x, back_x


def set_claw_open(doc, open_frac: float):
    """Update claw solids in place; keep each finger Placement."""
    claw_shape, _, _ = make_claw_solid(open_frac)
    for i in range(1, N_FINGERS + 1):
        obj = doc.getObject(f"CatcherFinger_{i}")
        if not obj:
            continue
        pl = Placement(obj.Placement)
        obj.Shape = claw_shape.copy()
        obj.Placement = pl
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = (0.1, 0.82, 0.4)
    doc.recompute()


def export_print_stl():
    """Export one open claw for printing (link assembly)."""
    claw, _, _ = make_claw_solid(0.1)
    bb = claw.BoundBox
    claw.translate(Vector(-bb.XMin, -bb.Center.y, -bb.ZMin))
    path = "/Users/user/Documents/chat/variable-reach-arm/cad/stl/CatcherFinger.stl"
    mesh = MeshPart.meshFromShape(Shape=claw, LinearDeflection=0.3, AngularDeflection=0.1)
    mesh.write(path)
    # Also hub
    return path


CATCHER_PARTS = [
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
]
