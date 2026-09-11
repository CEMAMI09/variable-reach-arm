"""Rev B telescope study and fit-coupon export, all geometry in millimetres.

Load with importlib from FreeCAD GUI or FreeCADCmd. build(extension_mm=0) returns
a NEW document; never closes/overwrites existing documents. Full robot assembly
release remains blocked: this is an inspectable telescope/clearance study.
"""
from pathlib import Path
import csv
import json
import math
import sys
import FreeCAD as App
import Part
from FreeCAD import Vector

ROOT=Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0,str(Path(__file__).resolve().parent))
import claw_gripper
import telescope_guides
import telescope_drive_details
P=json.loads((ROOT/'engineering/design_parameters.json').read_text())['geometry']
MM=lambda key: P[key]*1000


def box(x,y,z,origin):
    return Part.makeBox(x,y,z,Vector(*origin))


def hole(d,length,pos,axis=(0,0,1)):
    return Part.makeCylinder(d/2,length,Vector(*pos),Vector(*axis))


def square_tube(side,wall,length,start):
    s=side/2
    return box(length,side,side,(start,-s,-s)).cut(box(length+2,side-2*wall,side-2*wall,(start-1,-s+wall,-s+wall)))


def cut_many(shape,tools):
    for t in tools:
        shape=shape.cut(t)
    return shape.removeSplitter()


def split_collar(side,wall=5,length=30,half='bottom'):
    # Longitudinal tube axis X, clamp split at z=0; M4 through bolts avoid insert creep.
    outer=side+2*wall
    block=box(length,outer,outer/2,(0,-outer/2,-outer/2))
    for y in [-outer/2-10,outer/2]:
        block=block.fuse(box(length,10,6,(0,y,-6)))
    bore=box(length+2,side+0.4,side+0.4,(-1,-side/2-0.2,-side/2-0.2))
    shape=block.cut(bore)
    for x in [6,length-6]:
        for y in [-outer/2-5,outer/2+5]:
            shape=shape.cut(hole(4.5,outer,(x,y,-outer/2-1)))
    # Bore clearance0.4mm requires take-up.0.4mm relief per face leaves a visible
    # gap after0.2mm motion per half; halves must not bottom before gripping.
    shape=shape.cut(box(length+2,outer+22,2,(-1,-outer/2-11,-0.4)))
    if half=='top':
        shape.rotate(Vector(0,0,0),Vector(1,0,0),180)
    return shape.removeSplitter()


def gripper_strut(side,sign,nose,palm_root):
    """Separate bolted link:2M4 through clamp at foot,1M3 axial at palm."""
    top=6.0
    cy=sign*((side+7)/2+5)
    a=Vector(nose-11,cy,top+2)
    b=Vector(palm_root-19,sign*36,10)
    delta=b-a
    beam=Part.makeCylinder(3.5,delta.Length,a,delta.normalize())
    foot=box(22,9,4,(nose-22,cy-4.5,top))
    mount=box(6,12,12,(palm_root-22,sign*36-6,4))
    sh=beam.fuse(foot).fuse(mount)
    # The diagonal cylinder otherwise dips below the foot and into the clamp.
    sh=sh.cut(box(22,60,20,(nose-22,-30,-14)))
    if sign>0:
        # Clear the separate servo spacers above the flat foot seating plane.
        for x in (nose-16,nose-6):
            sh=sh.cut(hole(7.4,6,(x,cy,10)))
    for x in [nose-16,nose-6]:
        sh=sh.cut(hole(4.5,8,(x,cy,top-1)))
    sh=sh.cut(hole(3.4,8,(palm_root-23,sign*36,10),(1,0,0)))
    return sh.removeSplitter()


def guide_coupon():
    # Two replaceable pads on each broad face leaving central9mm belt corridor.
    # This coupon checks sliding clearance and bolt access before long parts.
    side=MM('inner_side_m')
    bore=MM('outer_side_m')-2*MM('outer_wall_m')
    outer=bore-0.2
    shape=square_tube(outer,(outer-side-0.2)/2,30,0)
    shape=shape.cut(box(32,12,10,(-1,-6,side/2)))
    # Open top gives one connected U coupon; actual running pads remain separate.
    return shape.removeSplitter()


def add(doc,name,shape,group,material='6061-T6 (verify)',printable=False,role=''):
    if not shape.isValid() or not shape.Solids:
        raise ValueError('invalid solid: '+name)
    obj=doc.addObject('PartDesign::Feature',name)
    obj.Shape=shape
    for key,value in [('MotionGroup',group),('MaterialSpec',material),('ReleaseStatus','DESIGN STUDY / NOT RELEASED'),('Function',role)]:
        obj.addProperty('App::PropertyString',key,'Engineering')
        setattr(obj,key,value)
    obj.addProperty('App::PropertyBool','PrintCandidate','Engineering')
    obj.PrintCandidate=printable
    if App.GuiUp:
        colors={'fixed':(0.55,0.58,0.61),'slider':(0.20,0.40,0.62),'wear':(0.83,0.69,0.37),'envelope':(0.85,0.3,0.2)}
        obj.ViewObject.ShapeColor=colors.get(group,(0.35,0.40,0.42))
        if group=='envelope':obj.ViewObject.Transparency=65
    return obj


def build(extension_mm=0,claw_angle_deg=20):
    if not 0<=extension_mm<=MM('extension_stroke_m'):
        raise ValueError('extension out of range')
    s=extension_mm
    doc=App.newDocument('VRA_Telescope_RevB')
    outer=MM('outer_side_m');ow=MM('outer_wall_m');inner=MM('inner_side_m');iw=MM('inner_wall_m')
    start=MM('outer_start_m');end=MM('outer_end_m')
    rear=MM('inner_retracted_start_m')+s
    nose=rear+MM('inner_length_m')
    mouth=MM('normal_reach_m')+s
    front=MM('front_guide_center_m');rg=MM('rear_guide_retracted_center_m')+s
    fixed=square_tube(outer,ow,end-start,start)
    fixed=telescope_guides.drill_tube(fixed,outer,inner,iw,front)
    fixed=telescope_drive_details.drill_outer(fixed)
    add(doc,'OuterTube',fixed,'fixed',role='Square stock; front holes only, no longitudinal slot')
    moving=square_tube(inner,iw,MM('inner_length_m'),rear)
    moving=telescope_guides.drill_tube(moving,outer,inner,iw,rg,rear=True)
    moving=telescope_drive_details.drill_inner(moving,rear)
    add(doc,'InnerTube',moving,'slider',role='Single moving stage; measured corner radii must clear pads')
    telescope_guides.add_guides(doc,add,outer,ow,inner,iw,front,rg)
    # Belt lower run through central upper annulus; external upper return, no slot in tube.
    pitch=MM('extension_belt_pitch_m');teeth=P['extension_pulley_teeth']
    radius=pitch*teeth/(2*math.pi)
    belt_z=inner/2+1.6
    zc=belt_z+radius
    pulley_x=[start-25,end+25]
    for label,x in zip(['Drive','Idler'],pulley_x):
        sh=hole(2*radius,11,(x,-5.5,zc),(0,1,0)).cut(hole(5,13,(x,-6.5,zc),(0,1,0)))
        add(doc,label+'PulleyPitchEnvelope',sh,'envelope','Purchased36TGT2; pitch envelope only',role='Teeth/flanges/bracket and actual belt supplier rating remain release gates')
    beltparts=telescope_drive_details.belt_shapes(pulley_x[0],pulley_x[1],rear,belt_z)
    for label,sh in zip(('Inside','InsideEnd'),beltparts):
        add(doc,'Belt'+label+'Envelope',sh,'envelope','Purchased open GT2 belt',role='Two ends clamp at rear anchor; nominal compression region and0.6mm seam')
    add(doc,'BeltReturnEnvelope',box(pulley_x[1]-pulley_x[0],9,1.38,(pulley_x[0],-4.5,belt_z+2*radius-.69)),
        'envelope','Purchased open GT2 belt',role='External return; supplier tooth and working load data required')
    telescope_drive_details.add_details(doc,add,rear)
    # Two steel trunnion envelopes: no solid shaft through the sliding-tube bore.
    for sign in [-1,1]:
        y0=outer/2+7 if sign>0 else -outer/2-57
        add(doc,'Trunnion_'+str(sign+1),hole(12,50,(0,y0,0),(0,1,0)),'fixed','Steel; candidate12mm',role='Requires positive flange drive and bearing seat drawings before machining')
    # Split catcher clamp; tube tip remains behind claw palm (mouth-100mm).
    for half in ['bottom','top']:
        sh=split_collar(inner,wall=3.5,length=22,half=half)
        sh.translate(Vector(nose-22,0,0))
        add(doc,'CatcherClamp_'+half,sh,'slider','PETG fit prototype / ASA or nylon after qualification',True,'Four M4 through bolts, no point set screw on thin tube')
    palm_root=claw_gripper.add_gripper(doc,add,mouth,claw_angle_deg)
    for sign in [-1,1]:
        sh=gripper_strut(inner,sign,nose,palm_root)
        add(doc,'CatcherStrut_'+str(sign+1),sh,'slider','PETG/ASA',True,'Two common M4 clamp bolts and one M3 axial palm bolt; through nuts')
    claw_gripper.add_servo_cradle(doc,add,mouth,nose)
    doc.recompute()
    return doc


def verify(doc,extension_mm):
    """Deterministic shape and telescope travel checks; no claim of complete DFM."""
    s=extension_mm
    outer=doc.getObject('OuterTube').Shape;inner=doc.getObject('InnerTube').Shape
    front=MM('front_guide_center_m');rear=MM('rear_guide_retracted_center_m')+s
    tail=MM('inner_retracted_start_m')+s;nose=tail+MM('inner_length_m')
    outer_start=MM('outer_start_m');outer_end=MM('outer_end_m')
    overlap=min(nose,outer_end)-max(tail,outer_start)
    assert overlap>=240-1e-6
    assert outer_start<=rear-15 and rear+15<=outer_end
    assert tail<=front-15 and front+15<=nose
    assert front-rear>=185-1e-6
    assert outer.common(inner).Volume<1e-6
    assert doc.getObject('BeltInsideEnvelope').Shape.common(inner).Volume<1e-6
    assert doc.getObject('BeltInsideEnvelope').Shape.common(outer).Volume<1e-6
    claw_intersections={o.Name: o.Shape.common(doc.getObject('GripperPalm').Shape).Volume
                        for o in doc.Objects if o.Name.startswith('Claw_')}
    assert all(v<1e-6 for v in claw_intersections.values()),claw_intersections
    for name in ['CatcherClamp_top','CatcherClamp_bottom','CatcherStrut_0','CatcherStrut_2','GripperServoEnvelope','GripperServoCradle']:
        sh=doc.getObject(name).Shape
        assert sh.common(inner).Volume<1e-6,(name,'inner collision')
        assert sh.common(outer).Volume<1e-6,(name,'outer collision')
        for drive in ['BeltInsideEnvelope','BeltInsideEndEnvelope','BeltReturnEnvelope','IdlerPulleyPitchEnvelope']:
            assert sh.common(doc.getObject(drive).Shape).Volume<1e-6,(name,drive,'collision')
    for other in ('GripperServoEnvelope','CatcherStrut_2','CatcherClamp_top',
                  'GripperPalm','ServoCradleSpacer_0','ServoCradleSpacer_1'):
        assert doc.getObject('GripperServoCradle').Shape.common(doc.getObject(other).Shape).Volume<1e-5,other
    for name in ('CatcherStrut_0','CatcherStrut_2'):
        assert doc.getObject(name).Shape.common(doc.getObject('CatcherClamp_top').Shape).Volume<1e-5,name
    for name in ('ServoCradleSpacer_0','ServoCradleSpacer_1'):
        assert doc.getObject(name).Shape.common(doc.getObject('CatcherStrut_2').Shape).Volume<1e-5,name
    for obj in doc.Objects:
        if hasattr(obj,'Shape'):
            assert obj.Shape.isValid() and len(obj.Shape.Solids)==1,obj.Name
        if obj.Name.startswith(('FrontShoe_','RearShoe_')):
            for other in ('InnerTube','OuterTube','BeltInsideEnvelope','BeltInsideEndEnvelope','BeltReturnEnvelope'):
                volume=obj.Shape.common(doc.getObject(other).Shape).Volume
                assert volume<1e-5,(obj.Name,other,volume)
    drive_checks=telescope_drive_details.verify_details(doc)
    return dict(drive_details=drive_checks,extension_mm=s,overlap_mm=overlap,guide_span_mm=front-rear,
                valid_shapes=sum(hasattr(o,'Shape') for o in doc.Objects),
                inner_outer_intersection_mm3=outer.common(inner).Volume,claw_palm_intersections_mm3=claw_intersections,
                release='study only; nominal guide/anchor/stops modeled; purchased interfaces, grip/stop proof and complete powered qualification remain open')


def _export_study():
    import MeshPart
    target=ROOT/'cad/review_b'
    target.mkdir(exist_ok=True)
    checks=[]
    for s in [0,250,500]:
        doc=build(s)
        checks.append(verify(doc,s))
        doc.saveAs(str(target/f'Telescope_{s}mm.FCStd'))
        if App.GuiUp:
            import FreeCADGui as Gui
            Gui.activeDocument().activeView().viewAxonometric()
            Gui.activeDocument().activeView().fitAll()
            Gui.activeDocument().activeView().saveImage(str(target/f'Telescope_{s}mm.png'),1600,900,'White')
    # Fit coupons only; these do not release the mechanism for powered use.
    manifest=[]
    parts=[('GuideFitCoupon',guide_coupon()),('ClawFitPrototype',claw_gripper.finger()),
           ('GripperPalmFitPrototype',claw_gripper.palm()),('PalmPadFitPrototype',claw_gripper.pad())]
    for name,shape in parts:
        assert shape.isValid() and len(shape.Solids)==1,name
        sh=shape.copy()
        if name=='ClawFitPrototype':sh.rotate(Vector(),Vector(1,0,0),90)
        elif name in ('GripperPalmFitPrototype','PalmPadFitPrototype'):sh.rotate(Vector(),Vector(0,1,0),90)
        sh.translate(Vector(0,0,-sh.BoundBox.ZMin))
        MeshPart.meshFromShape(Shape=sh,LinearDeflection=0.08,AngularDeflection=0.1).write(str(target/(name+'.stl')))
        manifest.append(dict(file=name+'.stl',volume_mm3=shape.Volume,status='FIT/UNPOWERED PROTOTYPE ONLY'))
    (target/'geometry_checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    (target/'print_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return checks


def export_study():
    """Export without leaving a different document active, including on failure."""
    previous=App.ActiveDocument
    try:
        return _export_study()
    finally:
        if previous and previous.Name in App.listDocuments():
            App.setActiveDocument(previous.Name)
