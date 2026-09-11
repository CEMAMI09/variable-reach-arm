# FreeCAD parametric build script — Variable-Reach Catching Arm
# Run inside FreeCAD: exec(open(".../build_arm.py").read())
# Or via FreeCAD MCP execute_code.

import math

import FreeCAD as App
import Part
from FreeCAD import Placement, Rotation, Vector

DOC_NAME = "VariableReachArm"

# --- Parameters (mm) ---
P = {
    "base_xy": 300.0,
    "base_t": 6.0,
    "pivot_height": 650.0,
    "yaw_hub_od": 80.0,
    "yaw_hub_h": 40.0,
    "yaw_bearing_id": 12.0,
    "pitch_bracket_w": 90.0,
    "pitch_bracket_h": 70.0,
    "pitch_bracket_t": 12.0,
    "pitch_shaft_d": 12.0,
    "pitch_shaft_l": 120.0,
    "outer_od": 40.0,
    "outer_id": 36.0,
    "outer_length": 750.0,
    "inner_od": 32.0,
    "inner_id": 28.0,
    "inner_length": 750.0,
    "extension_stroke": 500.0,
    "L_min": 700.0,  # pitch center to catcher center, retracted
    "catcher_od": 140.0,
    "catcher_id": 70.0,
    "catcher_depth": 120.0,
    "guide_len": 40.0,
    "guide_spacing": 180.0,
    "motor_nema23": 57.0,
    "motor_nema17": 42.0,
    "motor_len": 56.0,
    "pulley_pitch_d": 22.0,
    "yaw_range_deg": 140.0,
    "pitch_min_deg": -15.0,
    "pitch_max_deg": 70.0,
}


def clear_doc():
    if DOC_NAME in App.listDocuments():
        App.closeDocument(DOC_NAME)
    doc = App.newDocument(DOC_NAME)
    return doc


def add_box(doc, name, sx, sy, sz, pos, color=(0.6, 0.6, 0.65)):
    obj = doc.addObject("Part::Box", name)
    obj.Length = sx
    obj.Width = sy
    obj.Height = sz
    obj.Placement = Placement(Vector(*pos), Rotation())
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    return obj


def add_cyl(doc, name, r, h, pos, axis=(0, 0, 1), angle=0, color=(0.4, 0.45, 0.5)):
    obj = doc.addObject("Part::Cylinder", name)
    obj.Radius = r
    obj.Height = h
    rot = Rotation(Vector(*axis), angle) if angle else Rotation()
    # Orient cylinder: default along Z
    if axis == (1, 0, 0):
        rot = Rotation(Vector(0, 1, 0), 90)
    elif axis == (0, 1, 0):
        rot = Rotation(Vector(1, 0, 0), -90)
    obj.Placement = Placement(Vector(*pos), rot)
    if hasattr(obj, "ViewObject") and obj.ViewObject:
        obj.ViewObject.ShapeColor = color
    return obj


def add_tube(doc, name, od, id_, length, pos, axis="x", color=(0.15, 0.15, 0.18)):
    """Hollow tube. Default axis +X (boom direction)."""
    if axis == "x":
        direction = Vector(1, 0, 0)
    elif axis == "y":
        direction = Vector(0, 1, 0)
    else:
        direction = Vector(0, 0, 1)
    outer = Part.makeCylinder(od / 2.0, length, Vector(0, 0, 0), direction)
    inner = Part.makeCylinder(id_ / 2.0, length + 2, direction * (-1), direction)
    solid = outer.cut(inner)
    shape_obj = doc.addObject("Part::Feature", name)
    shape_obj.Shape = solid
    shape_obj.Placement = Placement(Vector(*pos), Rotation())
    if hasattr(shape_obj, "ViewObject") and shape_obj.ViewObject:
        shape_obj.ViewObject.ShapeColor = color
    return shape_obj


def _make_claw_finger():
    """Compliant TPU claw: palm + blade + curled tip (print as CatcherFinger.stl)."""
    palm = Part.makeBox(16, 28, 14, Vector(-8, -14, -7))
    blade = Part.makeBox(12, 18, 85, Vector(-6, -9, 0))
    knuckle = Part.makeCylinder(10, 16)
    knuckle.rotate(Vector(0, 0, 0), Vector(1, 0, 0), 90)
    knuckle.translate(Vector(0, 8, 40))
    tip = Part.makeBox(10, 14, 40, Vector(-5, -7, 0))
    tip.rotate(Vector(0, 0, 0), Vector(1, 0, 0), -40)
    tip.translate(Vector(0, -8, 78))
    soft = Part.makeSphere(9)
    soft.translate(Vector(0, -28, 108))
    flap = Part.makeBox(4, 22, 50, Vector(6, -11, 10))
    return palm.fuse(blade).fuse(knuckle).fuse(tip).fuse(soft).fuse(flap).removeSplitter()


def add_params_spreadsheet(doc):
    sheet = doc.addObject("Spreadsheet::Sheet", "Parameters")
    sheet.set("A1", "Parameter")
    sheet.set("B1", "Value_mm_or_deg")
    row = 2
    for k, v in sorted(P.items()):
        sheet.set(f"A{row}", k)
        sheet.set(f"B{row}", str(v))
        row += 1
    return sheet


def build():
    raise RuntimeError('Legacy concept assembly is retained for reference only. Current study: build_review_telescope.py. Full robot is not released.')
    doc = clear_doc()
    add_params_spreadsheet(doc)

    bx = P["base_xy"]
    # Base plate centered at origin, top at z=0
    add_box(
        doc,
        "BasePlate",
        bx,
        bx,
        P["base_t"],
        (-bx / 2, -bx / 2, -P["base_t"]),
        color=(0.55, 0.55, 0.58),
    )

    # Yaw column / hub
    add_cyl(
        doc,
        "YawColumn",
        P["yaw_hub_od"] / 2,
        P["pivot_height"] - 80,
        (0, 0, 0),
        color=(0.45, 0.47, 0.5),
    )
    add_cyl(
        doc,
        "YawHub",
        P["yaw_hub_od"] / 2 + 5,
        P["yaw_hub_h"],
        (0, 0, P["pivot_height"] - 80),
        color=(0.35, 0.55, 0.75),
    )

    # Yaw motor (NEMA23) on base
    m = P["motor_nema23"]
    add_box(
        doc,
        "YawMotor",
        m,
        m,
        P["motor_len"],
        (-bx / 2 + 20, -m / 2, 0),
        color=(0.1, 0.1, 0.12),
    )

    # Pitch bracket (two cheeks)
    ph = P["pivot_height"]
    bw = P["pitch_bracket_w"]
    bh = P["pitch_bracket_h"]
    bt = P["pitch_bracket_t"]
    add_box(
        doc,
        "PitchCheek_L",
        bt,
        bw,
        bh,
        (-45, -bw / 2, ph - bh / 2),
        color=(0.3, 0.65, 0.45),
    )
    add_box(
        doc,
        "PitchCheek_R",
        bt,
        bw,
        bh,
        (45 - bt, -bw / 2, ph - bh / 2),
        color=(0.3, 0.65, 0.45),
    )

    # Pitch shaft along Y
    add_cyl(
        doc,
        "PitchShaft",
        P["pitch_shaft_d"] / 2,
        P["pitch_shaft_l"],
        (0, -P["pitch_shaft_l"] / 2, ph),
        axis=(0, 1, 0),
        color=(0.75, 0.75, 0.78),
    )

    # Pitch motor
    add_box(
        doc,
        "PitchMotor",
        m,
        m,
        P["motor_len"],
        (-m / 2, -bw / 2 - P["motor_len"] - 10, ph - m / 2),
        color=(0.1, 0.1, 0.12),
    )

    # Outer boom along +X from pitch center; retracted catcher at L_min
    # Boom starts slightly forward of shaft
    boom_start_x = 50.0
    add_tube(
        doc,
        "OuterBoom",
        P["outer_od"],
        P["outer_id"],
        P["outer_length"],
        (boom_start_x, 0, ph),
        axis="x",
        color=(0.12, 0.12, 0.14),
    )

    # Inner boom retracted: tip clamped inside catcher hub (does NOT poke through mouth)
    # Hub mouth plane at boom_start + L_min; hub clamp ~25 mm behind mouth
    hub_mouth = boom_start_x + P["L_min"]
    tip_target = hub_mouth - 25.0
    inner_start = tip_target - P["inner_length"]
    add_tube(
        doc,
        "InnerBoom",
        P["inner_od"],
        P["inner_id"],
        P["inner_length"],
        (inner_start, 0, ph),
        axis="x",
        color=(0.2, 0.2, 0.25),
    )

    # Guides (replaceable sleeves) — represented as short rings
    for i, xoff in enumerate([80.0, 80.0 + P["guide_spacing"]]):
        add_cyl(
            doc,
            f"Guide_{i+1}",
            P["outer_id"] / 2 + 0.5,
            P["guide_len"],
            (boom_start_x + xoff, 0, ph),
            axis=(1, 0, 0),
            color=(0.85, 0.55, 0.2),
        )

    # Extension motor near shoulder
    m17 = P["motor_nema17"]
    add_box(
        doc,
        "ExtensionMotor",
        m17,
        m17,
        48.0,
        (boom_start_x - 10, 40, ph - m17 / 2),
        color=(0.1, 0.1, 0.12),
    )
    add_cyl(
        doc,
        "ExtensionPulley",
        P["pulley_pitch_d"] / 2,
        10,
        (boom_start_x + 30, 55, ph),
        axis=(0, 1, 0),
        color=(0.9, 0.75, 0.2),
    )

    # Catcher is built by catcher_fingers.rebuild_catcher() after this script
    # so hub/funnel/claws stay one connected assembly on the inner-boom tip.

    # Electronics enclosure on base
    add_box(
        doc,
        "ElectronicsEnclosure",
        120,
        80,
        50,
        (bx / 2 - 140, bx / 2 - 100, 0),
        color=(0.25, 0.25, 0.28),
    )

    # Cable guide rings along outer boom
    for i, xoff in enumerate([150.0, 350.0, 550.0]):
        add_cyl(
            doc,
            f"CableGuide_{i+1}",
            6,
            8,
            (boom_start_x + xoff, -P["outer_od"] / 2 - 8, ph),
            color=(0.5, 0.5, 0.2),
        )

    # End stops (blocks)
    add_box(
        doc,
        "ExtensionStop_Min",
        8,
        20,
        20,
        (boom_start_x + 20, -10, ph - 10),
        color=(0.8, 0.1, 0.1),
    )
    add_box(
        doc,
        "ExtensionStop_Max",
        8,
        20,
        20,
        (boom_start_x + P["extension_stroke"] + 40, -10, ph - 10),
        color=(0.8, 0.1, 0.1),
    )

    doc.recompute()
    return doc


if __name__ == "__main__":
    build()
    print("VariableReachArm built with parameters:", P)
