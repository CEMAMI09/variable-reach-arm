"""
Generate manufacturing-ready printable solids and export STL cut-list.

Run inside FreeCAD (GUI or MCP):
  exec(open('/Users/user/Documents/chat/variable-reach-arm/cad/scripts/export_printables.py').read())

Parts are built in print-friendly orientations (Z up) with:
  - bearing pockets / shaft bores
  - NEMA mount patterns
  - heat-set insert holes
  - clamp slots / clearance for real CF tubes
"""

from __future__ import annotations

import math
import os
import sys

import FreeCAD as App
import MeshPart
import Part
from FreeCAD import Placement, Rotation, Vector

SCRIPT_DIR = "/Users/user/Documents/chat/variable-reach-arm/cad/scripts"
STL_DIR = "/Users/user/Documents/chat/variable-reach-arm/cad/stl"
sys.path.insert(0, SCRIPT_DIR)

# --- Hardware constants (mm) ---
INNER_OD = 32.0
OUTER_OD = 40.0
OUTER_ID = 36.0
BEARING_OD = 28.0  # 6001-2RS
BEARING_ID = 12.0
BEARING_W = 8.0
SHAFT_D = 12.0
NEMA23 = 57.0
NEMA23_HOLE = 47.14  # square pitch
NEMA17 = 42.0
NEMA17_HOLE = 31.0
M3_INSERT = 4.0  # heat-set OD drill approx
M4_INSERT = 5.6
M3_CLEAR = 3.4
M4_CLEAR = 4.5
CATCHER_OD = 140.0
CATCHER_ID = 72.0
FUNNEL_DEPTH = 110.0

DEFLECTION = 0.25
ANGULAR = 0.15


def _cyl(r, h, pos=(0, 0, 0), axis=Vector(0, 0, 1)):
    return Part.makeCylinder(r, h, Vector(*pos) if not isinstance(pos, Vector) else pos, axis)


def _box(sx, sy, sz, pos=(0, 0, 0)):
    p = Vector(*pos) if not isinstance(pos, Vector) else pos
    return Part.makeBox(sx, sy, sz, p)


def _nema_holes(pitch: float, depth: float, z0: float = -1.0, d: float = M4_CLEAR):
    """Four through holes on NEMA square pattern, centered on XY origin."""
    h = pitch / 2.0
    holes = []
    for sx, sy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        holes.append(_cyl(d / 2, depth, (sx * h, sy * h, z0)))
    return holes


def _fuse(shapes):
    out = shapes[0]
    for s in shapes[1:]:
        out = out.fuse(s)
    return out.removeSplitter()


def _cut(base, tools):
    out = base
    for t in tools:
        out = out.cut(t)
    return out.removeSplitter()


def seat_on_bed(shape: Part.Shape) -> Part.Shape:
    """Translate so ZMin=0 and XY centered near origin."""
    bb = shape.BoundBox
    shape = shape.copy()
    shape.translate(Vector(-bb.Center.x, -bb.Center.y, -bb.ZMin))
    return shape


def write_stl(shape: Part.Shape, name: str) -> str:
    os.makedirs(STL_DIR, exist_ok=True)
    shape = seat_on_bed(shape)
    path = os.path.join(STL_DIR, f"{name}.stl")
    mesh = MeshPart.meshFromShape(
        Shape=shape, LinearDeflection=DEFLECTION, AngularDeflection=ANGULAR
    )
    mesh.write(path)
    bb = shape.BoundBox
    print(
        f"  STL {name:28} tris~{mesh.CountFacets:6}  "
        f"{bb.XLength:6.1f}x{bb.YLength:6.1f}x{bb.ZLength:6.1f} mm  -> {path}"
    )
    return path


# ---------------------------------------------------------------------------
# Part builders (print orientation: Z up)
# ---------------------------------------------------------------------------

def make_pitch_cheek(side: str = "L") -> Part.Shape:
    """
    Pitch cheek plate with:
      - 6001 bearing pocket (OD) + shaft through
      - NEMA23 motor mount (one cheek carries motor; both get pattern for symmetry)
      - M4 insert holes for cross-bolts to opposite cheek / shaft plate
    Thickness along Z for print flat on large face.
    """
    t = 12.0
    w = 100.0  # X
    h = 80.0   # Y
    body = _box(w, h, t, (-w / 2, -h / 2, 0))

    # Bearing pocket centered; depth 8.2 from outer face (Z=t)
    # Print flat: pocket opens upward (Z)
    pocket = _cyl(BEARING_OD / 2 + 0.15, BEARING_W + 0.4, (0, 0, t - (BEARING_W + 0.2)))
    shaft = _cyl(SHAFT_D / 2 + 0.25, t + 4, (0, 0, -2))

    # NEMA23 pattern offset toward boom side ( +X )
    mx, my = 28.0, 0.0
    motor_boss = _box(NEMA23 + 6, NEMA23 + 6, 3, (mx - (NEMA23 + 6) / 2, my - (NEMA23 + 6) / 2, t - 3))
    body = body.fuse(motor_boss)
    holes = []
    for tool in _nema_holes(NEMA23_HOLE, t + 6, -2, M4_CLEAR):
        tool.translate(Vector(mx, my, 0))
        holes.append(tool)
    # Motor pilot clearance
    holes.append(_cyl(12.0, t + 6, (mx, my, -2)))  # shaft/coupler clearance

    # Clamp / cheek join M4 inserts (4 corners)
    for sx, sy in ((-40, -32), (-40, 32), (40, -32), (40, 32)):
        holes.append(_cyl(M4_INSERT / 2, 6.5, (sx, sy, t - 6.2)))  # insert from top
        holes.append(_cyl(M4_CLEAR / 2, t + 4, (sx, sy, -2)))

    # Boom cradle notch on +X edge (half-round for outer tube nest)
    cradle = _cyl(OUTER_OD / 2 + 0.5, t + 2, (w / 2 - 2, 0, -1), Vector(0, 1, 0))
    # Actually cut a U-slot from +X face
    slot = _box(22, OUTER_OD + 2, t + 2, (w / 2 - 20, -(OUTER_OD + 2) / 2, -1))
    holes.append(slot)

    shaped = _cut(body, [pocket, shaft] + holes)
    # Mirror note: L and R are identical printable; flip in assembly
    _ = side
    return shaped


def make_electronics_enclosure() -> tuple[Part.Shape, Part.Shape]:
    """Open box + separate lid. Interior ~110×70×40 for Teensy + buck + proto."""
    wall = 3.0
    ox, oy, oz = 120.0, 80.0, 50.0
    outer = _box(ox, oy, oz, (0, 0, 0))
    inner = _box(ox - 2 * wall, oy - 2 * wall, oz - wall + 1, (wall, wall, wall))
    body = outer.cut(inner)

    # M3 insert posts in corners
    posts = []
    holes = []
    for x, y in ((8, 8), (ox - 8, 8), (8, oy - 8), (ox - 8, oy - 8)):
        posts.append(_cyl(5.5, oz - wall - 1, (x, y, wall)))
        holes.append(_cyl(M3_INSERT / 2, 6.5, (x, y, oz - wall - 6)))
        holes.append(_cyl(M3_CLEAR / 2, 10, (x, y, oz - 8)))
    body = _fuse([body] + posts)
    body = _cut(body, holes)

    # Cable exits
    body = body.cut(_cyl(6, wall + 4, (-1, oy / 2, 18), Vector(1, 0, 0)))
    body = body.cut(_cyl(6, wall + 4, (ox - wall - 1, oy / 2, 18), Vector(1, 0, 0)))

    # Lid
    lid = _box(ox, oy, 3, (0, 0, 0))
    lid_holes = []
    for x, y in ((8, 8), (ox - 8, 8), (8, oy - 8), (ox - 8, oy - 8)):
        lid_holes.append(_cyl(M3_CLEAR / 2, 8, (x, y, -2)))
    # Vent slots
    for i in range(5):
        lid_holes.append(_box(ox - 30, 3, 6, (15, 20 + i * 10, -1)))
    lid = _cut(lid, lid_holes)
    return body.removeSplitter(), lid.removeSplitter()


def make_guide(name_tag: str = "1") -> Part.Shape:
    """Sliding guide collar: OD seats in outer tube ID area / clamp; ID clears inner OD."""
    _ = name_tag
    length = 45.0
    od = OUTER_ID - 0.4  # slip inside outer tube
    id_ = INNER_OD + 0.6  # clearance before UHMW tape (~0.2 after tape)
    body = _cyl(od / 2, length)
    bore = _cyl(id_ / 2, length + 4, (0, 0, -2))
    # Set-screw flats / M3 insert for anti-rotate pin (optional)
    boss = _box(10, 8, 12, (-5, od / 2 - 2, length / 2 - 6))
    body = body.fuse(boss)
    body = body.cut(bore)
    body = body.cut(_cyl(M3_INSERT / 2, 8, (0, od / 2 - 1, length / 2), Vector(0, 1, 0)))
    return body.removeSplitter()


def make_extension_stop(kind: str = "Min") -> Part.Shape:
    """
    Clamp-on bumper for outer boom OD40.
    Print flat; saddle faces up. Bolt through ears with M3.
    """
    # Rectangular ears + arched saddle
    plate = _box(50, 28, 8, (0, 0, 0))
    # Raised sides
    left = _box(12, 28, 22, (0, 0, 0))
    right = _box(12, 28, 22, (38, 0, 0))
    body = plate.fuse(left).fuse(right)
    # Tube saddle through center (axis along Y)
    body = body.cut(_cyl(OUTER_OD / 2 + 0.6, 32, (25, -2, 22), Vector(0, 1, 0)))
    # M3 holes in ears
    for x in (6, 44):
        for y in (7, 21):
            body = body.cut(_cyl(M3_CLEAR / 2, 40, (x, y, -2)))
    # Strike pad pocket
    if kind == "Max":
        body = body.cut(_box(16, 6, 10, (17, 22, 8)))
    else:
        body = body.cut(_box(16, 6, 10, (17, 0, 8)))
    return body.removeSplitter()


def make_cable_guide() -> Part.Shape:
    body = _box(18, 14, 10, (0, 0, 0))
    # Zip-tie slots
    body = body.cut(_box(12, 3, 12, (3, 5.5, -1)))
    body = body.cut(_box(3, 10, 12, (7.5, 2, -1)))
    # M3 mount
    body = body.cut(_cyl(M3_CLEAR / 2, 14, (9, 7, -2)))
    return body.removeSplitter()


def make_catcher_hub() -> Part.Shape:
    """
    Hub sleeve + mouth flange.
    Print flat on flange face. Clamp slot + 2× M4 for tube grip.
    Finger mount holes on flange PCD.
    """
    hub_len = 60.0
    sleeve_od = INNER_OD + 24.0
    flange_t = 12.0
    flange_od = CATCHER_OD - 8.0

    sleeve = _cyl(sleeve_od / 2, hub_len)
    bore = _cyl(INNER_OD / 2 + 0.25, hub_len + 4, (0, 0, -2))
    flange = _cyl(flange_od / 2, flange_t, (0, 0, hub_len - flange_t))
    body = sleeve.fuse(flange).cut(bore)

    # Clamp split slot
    body = body.cut(_box(3, sleeve_od, hub_len - flange_t + 2, (-1.5, 0, -1)))
    # Clamp M4 through
    body = body.cut(_cyl(M4_CLEAR / 2, sleeve_od + 4, (0, -2, hub_len / 3), Vector(0, 1, 0)))
    body = body.cut(_cyl(M4_CLEAR / 2, sleeve_od + 4, (0, -2, 2 * hub_len / 3), Vector(0, 1, 0)))

    # 3× finger mount M3 inserts on flange (120°)
    rim_r = flange_od / 2 - 10.0
    for i in range(3):
        ang = math.radians(i * 120.0)
        x = rim_r * math.cos(ang)
        y = rim_r * math.sin(ang)
        body = body.cut(_cyl(M3_INSERT / 2, 8, (x, y, hub_len - 7.5)))
        body = body.cut(_cyl(M3_CLEAR / 2, flange_t + 4, (x, y, hub_len - flange_t - 2)))

    # Mouth lead-in chamfer-ish ring cut
    body = body.cut(_cyl(CATCHER_ID / 2 - 2, 6, (0, 0, hub_len - 5)))
    return body.removeSplitter()


def make_catcher_adapter() -> Part.Shape:
    """Fills boom→funnel; slips over inner tube behind hub."""
    length = 90.0
    od = 70.0
    body = _cyl(od / 2, length)
    body = body.cut(_cyl(INNER_OD / 2 + 0.3, length + 4, (0, 0, -2)))
    # Lightening / flex slots
    for i in range(6):
        ang = math.radians(i * 60.0)
        x = 28 * math.cos(ang)
        y = 28 * math.sin(ang)
        body = body.cut(_cyl(6, length - 20, (x, y, 10)))
    return body.removeSplitter()


def make_catcher_funnel() -> Part.Shape:
    """Printable funnel wall (TPU). Open both ends."""
    wall = 4.0
    outer = _cyl(CATCHER_OD / 2, FUNNEL_DEPTH)
    inner = _cyl(CATCHER_ID / 2, FUNNEL_DEPTH + 4, (0, 0, -2))
    body = outer.cut(inner)
    # Flange ring at mouth for screwing to hub
    flange = _cyl(CATCHER_OD / 2 + 4, 6, (0, 0, FUNNEL_DEPTH - 6))
    flange = flange.cut(_cyl(CATCHER_ID / 2, 10, (0, 0, FUNNEL_DEPTH - 8)))
    body = body.fuse(flange)
    rim_r = (CATCHER_OD / 2 + CATCHER_ID / 2) / 2
    for i in range(3):
        ang = math.radians(i * 120.0)
        body = body.cut(
            _cyl(M3_CLEAR / 2, 20, (rim_r * math.cos(ang), rim_r * math.sin(ang), FUNNEL_DEPTH - 10))
        )
    return body.removeSplitter()


def make_catcher_cradle() -> Part.Shape:
    """Soft backstop disk with tube clearance."""
    body = _cyl(CATCHER_ID / 2 + 8, 14)
    body = body.cut(_cyl(INNER_OD / 2 + 1.0, 20, (0, 0, -3)))
    # Drain / flex holes
    for i in range(6):
        ang = math.radians(i * 60.0 + 30)
        r = CATCHER_ID / 2 - 10
        body = body.cut(_cyl(5, 20, (r * math.cos(ang), r * math.sin(ang), -3)))
    return body.removeSplitter()


def make_catcher_rib() -> Part.Shape:
    body = _box(100, 10, 10, (0, 0, 0))
    body = body.cut(_cyl(M3_CLEAR / 2, 14, (12, 5, -2)))
    body = body.cut(_cyl(M3_CLEAR / 2, 14, (88, 5, -2)))
    return body.removeSplitter()


def make_claw_assembly_open() -> Part.Shape:
    import catcher_fingers as CF

    claw, _, _ = CF.make_claw_solid(0.08)
    # Mount screw hole through mount block
    claw = claw.cut(_cyl(M3_CLEAR / 2, 30, (-5, 0, -15), Vector(0, 0, 1)))
    # Hinge pin holes (proximal base + mid joint) — Ø6.1 clearance
    claw = claw.cut(_cyl(3.05, 40, (0, -20, 0), Vector(0, 1, 0)))
    claw = claw.cut(_cyl(3.05, 40, (CF.L_PROX, -20, 0), Vector(0, 1, 0)))
    return claw.removeSplitter()


def make_claw_tip_pad() -> Part.Shape:
    """TPU tip pad that slips over distal sphere."""
    shell = _cyl(14, 18)
    shell = shell.fuse(Part.makeSphere(14).translate(Vector(0, 0, 18)))
    shell = shell.cut(_cyl(9.5, 22, (0, 0, -1)))
    shell = shell.cut(Part.makeSphere(10).translate(Vector(0, 0, 18)))
    return shell.removeSplitter()


def make_hinge_pin() -> Part.Shape:
    """PETG pin Ø6 × 28 with one flange."""
    shank = _cyl(3.0, 28)
    head = _cyl(5.0, 2, (0, 0, 28))
    return shank.fuse(head).removeSplitter()


def make_nema23_mount_plate() -> Part.Shape:
    """Standalone motor plate if not using cheek pattern."""
    t = 6.0
    body = _box(70, 70, t, (-35, -35, 0))
    body = _cut(body, _nema_holes(NEMA23_HOLE, t + 4, -2, M4_CLEAR))
    body = body.cut(_cyl(12, t + 4, (0, 0, -2)))
    # Frame M4 inserts
    for sx, sy in ((-28, -28), (-28, 28), (28, -28), (28, 28)):
        body = body.cut(_cyl(M4_INSERT / 2, 5, (sx, sy, t - 4.8)))
        body = body.cut(_cyl(M4_CLEAR / 2, t + 4, (sx, sy, -2)))
    return body.removeSplitter()


def make_nema17_mount_plate() -> Part.Shape:
    t = 5.0
    body = _box(55, 55, t, (-27.5, -27.5, 0))
    body = _cut(body, _nema_holes(NEMA17_HOLE, t + 4, -2, M3_CLEAR))
    body = body.cut(_cyl(12, t + 4, (0, 0, -2)))
    for sx, sy in ((-22, -22), (-22, 22), (22, -22), (22, 22)):
        body = body.cut(_cyl(M3_INSERT / 2, 5, (sx, sy, t - 4.8)))
    return body.removeSplitter()


def make_yaw_hub_clamp() -> Part.Shape:
    """Printed clamp that bolts to aluminum/steel yaw tube stub."""
    h = 40.0
    od = 90.0
    id_ = 50.0  # over yaw column / tube — adjust to measured stock
    body = _cyl(od / 2, h)
    body = body.cut(_cyl(id_ / 2, h + 4, (0, 0, -2)))
    body = body.cut(_box(4, od, h + 2, (-2, 0, -1)))
    body = body.cut(_cyl(M4_CLEAR / 2, od, (0, -2, h / 3), Vector(0, 1, 0)))
    body = body.cut(_cyl(M4_CLEAR / 2, od, (0, -2, 2 * h / 3), Vector(0, 1, 0)))
    # Pitch cheek interface M4 inserts on top face
    for sx, sy in ((-30, -25), (-30, 25), (30, -25), (30, 25)):
        body = body.cut(_cyl(M4_INSERT / 2, 8, (sx, sy, h - 7.5)))
    return body.removeSplitter()


def make_base_foot_spacer() -> Part.Shape:
    """Optional printed spacer under Al plate (not a substitute for Al base)."""
    body = _cyl(18, 8)
    body = body.cut(_cyl(6.6 / 2, 12, (0, 0, -2)))  # M6 clearance
    return body.removeSplitter()


# ---------------------------------------------------------------------------
# Export all
# ---------------------------------------------------------------------------

MANIFEST = []


def export_all(clean_old: bool = True) -> list[str]:
    global MANIFEST
    MANIFEST = []

    if clean_old:
        for fn in os.listdir(STL_DIR) if os.path.isdir(STL_DIR) else []:
            if fn.endswith(".stl"):
                os.remove(os.path.join(STL_DIR, fn))
                print("  removed old", fn)

    jobs = [
        ("PitchCheek_L", make_pitch_cheek("L"), "PETG", 1, "Bearing pocket + NEMA23 + M4 inserts"),
        ("PitchCheek_R", make_pitch_cheek("R"), "PETG", 1, "Identical to L; mirror in assembly"),
        ("NEMA23_MountPlate", make_nema23_mount_plate(), "PETG", 2, "Extra motor plates (yaw/pitch)"),
        ("NEMA17_MountPlate", make_nema17_mount_plate(), "PETG", 1, "Extension motor"),
        ("YawHubClamp", make_yaw_hub_clamp(), "PETG", 1, "Fits over yaw tube; check ID to stock"),
        ("Guide_1", make_guide("1"), "Nylon or PETG", 1, "UHMW tape ID after print"),
        ("Guide_2", make_guide("2"), "Nylon or PETG", 1, "UHMW tape ID after print"),
        ("ExtensionStop_Min", make_extension_stop("Min"), "PETG", 1, "Retract bumper"),
        ("ExtensionStop_Max", make_extension_stop("Max"), "PETG", 1, "Extend bumper"),
        ("CableGuide", make_cable_guide(), "PETG", 3, "Print 3 from one STL"),
        ("CatcherHub", make_catcher_hub(), "PETG", 1, "Clamp on CF inner tip"),
        ("CatcherAdapter", make_catcher_adapter(), "PETG", 1, "Behind hub on inner tube"),
        ("CatcherFunnel", make_catcher_funnel(), "TPU 95A", 1, "Soft entrance"),
        ("CatcherCradle", make_catcher_cradle(), "TPU 95A", 1, "Soft backstop"),
        ("CatcherRib", make_catcher_rib(), "PETG", 3, "Print 3"),
        ("CatcherFinger", make_claw_assembly_open(), "PETG", 3, "Print 3; Ø6 pins"),
        ("CatcherTipPad", make_claw_tip_pad(), "TPU 95A", 3, "Print 3; glue/slip on tips"),
        ("HingePin", make_hinge_pin(), "PETG", 6, "2 pins × 3 claws (or use steel dowel)"),
        ("BaseFootSpacer", make_base_foot_spacer(), "PETG", 4, "Optional under leveling feet"),
    ]

    # Enclosure pair
    enc, lid = make_electronics_enclosure()
    jobs.append(("ElectronicsEnclosure", enc, "PETG", 1, "Hollow box + insert posts"))
    jobs.append(("ElectronicsEnclosure_Lid", lid, "PETG", 1, "M3 screw-down lid"))

    paths = []
    for name, shape, material, qty, notes in jobs:
        path = write_stl(shape, name)
        paths.append(path)
        MANIFEST.append(
            {
                "file": f"{name}.stl",
                "material": material,
                "qty": qty,
                "notes": notes,
            }
        )

    # Write manifest CSV next to STLs
    man_path = os.path.join(STL_DIR, "MANIFEST.csv")
    with open(man_path, "w", encoding="utf-8") as f:
        f.write("file,qty,material,notes\n")
        for row in MANIFEST:
            f.write(f"{row['file']},{row['qty']},{row['material']},{row['notes']}\n")
    print("MANIFEST", man_path, "parts", len(MANIFEST))
    return paths


def main():
    print("=== export_printables ===")
    export_all(clean_old=True)
    print("DONE")


if __name__ == "__main__":
    main()
