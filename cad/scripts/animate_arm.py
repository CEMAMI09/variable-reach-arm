"""Render the actual full review CAD without touching the original document.

FreeCAD GUI script. Motion is prescribed kinematics, never a physics or catching
success simulation. Build once, then transform each rest solid by its motion group.
"""
from pathlib import Path
import importlib
import json
import math
import sys

import FreeCAD as App
from FreeCAD import Placement, Rotation, Vector

ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
OUT = ROOT / 'cad/animations'
_SPRING_CACHE = {}


def ease(t):
    t = max(0.0, min(1.0, t))
    return t*t*t*(10+t*(-15+6*t))


def trajectory(frame, count, mode='demo'):
    """Yaw/pitch degrees, extension mm, claw opening degrees; positive pitch UP."""
    if mode == 'demo':
        keys = [(0,0,5,0,20), (.18,-40,25,0,20), (.40,35,50,500,20),
                (.58,35,50,500,-10), (.72,0,20,250,-10), (.88,-20,5,0,20), (1,0,5,0,20)]
    elif mode == 'catch_fast':
        # Retain old filename for repository links, but remove fabricated catch.
        keys = [(0,-20,5,0,20), (.15,-20,5,0,20), (.45,25,48,420,20),
                (.60,25,48,420,-10), (.72,25,48,380,-10), (1,-20,5,0,20)]
    else:
        raise ValueError('mode must be demo or catch_fast')
    u = frame / max(count-1, 1)
    for a,b in zip(keys, keys[1:]):
        if u <= b[0]:
            w = ease((u-a[0])/(b[0]-a[0]))
            return tuple(a[k]+(b[k]-a[k])*w for k in range(1,5))
    return keys[-1][1:]


def about(point, axis, degrees):
    rotation = Rotation(axis, degrees)
    return Placement(point-rotation.multVec(point), rotation)


def capture_rest(doc):
    return {o.Name: Placement(o.Placement) for o in doc.Objects if hasattr(o,'Shape')}


def set_pose(doc, rest, yaw_deg, pitch_deg, ext_mm, claw_deg, pivot_height_mm=850):
    pivot = Vector(0,0,pivot_height_mm)
    yaw = about(Vector(), Vector(0,0,1), yaw_deg)
    shoulder = yaw.multiply(about(pivot, Vector(0,1,0), -pitch_deg))
    slider = shoulder.multiply(Placement(Vector(ext_mm,0,0),Rotation()))
    for name, placement in rest.items():
        obj = doc.getObject(name)
        motion = getattr(obj,'AssemblyMotion','stationary')
        if motion == 'stationary':
            transform = Placement()
        elif motion == 'yaw':
            transform = yaw
        else:
            slides = (getattr(obj,'MotionGroup','') == 'slider' or name == 'GripperServoEnvelope'
                      or name.startswith('RearShoe_'))
            transform = slider if slides else shoulder
            if name.startswith('Claw_') and name.rsplit('_',1)[1].isdigit():
                radial = Rotation(Vector(1,0,0), (int(name.rsplit('_',1)[1])-1)*120)
                hinge = pivot + Vector(600,0,0) + radial.multVec(Vector(0,0,40))
                axis = radial.multVec(Vector(0,1,0))
                transform = transform.multiply(about(hinge,axis,20-claw_deg))
        if name.startswith('ClawWorkingTendon_'):
            import Part
            theta=math.radians(claw_deg)
            a=Vector(-12*math.sin(theta),-4.5,40+12*math.cos(theta))
            b=Vector(-25,-4.5,52)
            delta=b-a
            shape=Part.makeCylinder(0.35,delta.Length,a,delta.normalize())
            shape.rotate(Vector(),Vector(1,0,0),(int(name.rsplit('_',1)[1])-1)*120)
            shape.translate(Vector(600,0,pivot_height_mm))
            obj.Placement=Placement()
            obj.Shape=shape
        if name in ('BeltInsideEnvelope','BeltInsideEndEnvelope'):
            import telescope_drive_details
            shapes=telescope_drive_details.belt_shapes(-275,545,-220+ext_mm,14.3)
            shape=shapes[0 if name=='BeltInsideEnvelope' else 1]
            shape.translate(Vector(0,0,pivot_height_mm))
            obj.Placement=Placement()
            obj.Shape=shape
        if name.startswith('ClawSpringCoil_'):
            import claw_gripper
            if claw_deg not in _SPRING_CACHE:
                _SPRING_CACHE[claw_deg]=claw_gripper.spring_shape(claw_deg)
            shape=_SPRING_CACHE[claw_deg].copy()
            shape.rotate(Vector(),Vector(1,0,0),(int(name.rsplit('_',1)[1])-1)*120)
            shape.translate(Vector(600,0,pivot_height_mm))
            obj.Placement=Placement()
            obj.Shape=shape
        if name.startswith('ClawStopEyePin_'):
            import claw_gripper
            shape=claw_gripper.stop_eye_pin_shape(claw_deg)
            shape.rotate(Vector(),Vector(1,0,0),(int(name.rsplit('_',1)[1])-1)*120)
            shape.translate(Vector(600,0,pivot_height_mm))
            obj.Placement=Placement()
            obj.Shape=shape
        obj.Placement = transform.multiply(placement)
    doc.recompute()


def animate_and_export(n_frames=96, width=1100, height=820, mode='demo',
                       frame_dir=None, pivot_height_mm=850, stiffened_yoke=True):
    """Build current review modules; preserve the full active document on any error.

    Returned PNGs have a matching metadata sidecar. Use make_gif.py to apply the
    mandatory on-image prototype and kinematic disclaimers.
    """
    if n_frames < 2:
        raise ValueError('at least two frames required')
    import FreeCADGui as Gui
    previous = App.ActiveDocument
    doc = None
    import build_review_robot as robot
    importlib.reload(robot)
    _SPRING_CACHE.clear()
    folder = Path(frame_dir) if frame_dir else OUT / ('frames' if mode=='demo' else 'frames_catch_fast')
    folder.mkdir(parents=True,exist_ok=True)
    try:
        doc,_ = robot.build(0,0,0,20,pivot_height_mm=pivot_height_mm,stiffened_yoke=stiffened_yoke)
        doc.Label = 'Full arm animation — clearance prototype'
        rest = capture_rest(doc)
        # Frame all animation poses at once with a temporary bound object. The
        # camera remains fixed throughout the clip, so scale never implies speed.
        import Part
        bounds = App.BoundBox()
        poses = [trajectory(i,n_frames,mode) for i in range(n_frames)]
        for q in poses:
            set_pose(doc,rest,*q,pivot_height_mm)
            for obj in doc.Objects:
                if hasattr(obj,'Shape'): bounds.add(obj.Shape.BoundBox)
        set_pose(doc,rest,*poses[0],pivot_height_mm)
        guide = doc.addObject('Part::Feature','AnimationFramingOnly')
        guide.Shape = Part.makeBox(bounds.XLength+80,bounds.YLength+80,bounds.ZLength+80,
                                   Vector(bounds.XMin-40,bounds.YMin-40,bounds.ZMin-40))
        guide.ViewObject.Transparency=100
        view = Gui.activeDocument().activeView()
        view.viewAxonometric()
        view.fitAll()
        doc.removeObject(guide.Name)
        doc.recompute()
        paths=[]
        for i,q in enumerate(poses):
            set_pose(doc,rest,*q,pivot_height_mm)
            Gui.updateGui()
            view.redraw()
            output = folder / f'frame_{i:03d}.png'
            view.saveImage(str(output),width,height,'White')
            paths.append(str(output))
        metadata = dict(mode=mode,frames=[dict(file=Path(p).name,yaw_deg=q[0],pitch_deg=q[1],
                          extension_mm=q[2],claw_angle_deg=q[3]) for p,q in zip(paths,poses)],
                        pivot_height_mm=pivot_height_mm,stiffened_yoke=stiffened_yoke,
                        status='CLEARANCE PROTOTYPE — KINEMATIC DEMONSTRATION',
                        limitation='Prescribed motion; not measured performance, controller execution, or catch success.',
                        geometry_source='cad/scripts/build_review_robot.py and its current imported modules')
        (folder/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8')
        return paths
    finally:
        if doc is not None and doc.Name in App.listDocuments():
            App.closeDocument(doc.Name)
        if previous is not None and previous.Name in App.listDocuments():
            App.setActiveDocument(previous.Name)
            if Gui.activeDocument(): Gui.activeDocument().activeView().redraw()


if __name__=='__main__':
    animate_and_export()




