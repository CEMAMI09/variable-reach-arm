"""Full Rev B robot assembly study, mm. Never modifies the original GUI document.

Builds the detailed telescope/claw module plus physically separated stock plates,
column/braces, paired yaw bearings, external pitch stubs, bolted boom saddles,
supported two-stage belt layouts, motor/brake envelopes, guards and wire corridor.
Purchased drive envelopes have no invented tooth or supplier-qualified interface.
"""
from pathlib import Path
import csv
import json
import math
import sys
import FreeCAD as App
import Part
from FreeCAD import Vector

ROOT = Path(__file__).resolve().parents[2]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_review_telescope as telescope

P = json.loads((ROOT / 'engineering/design_parameters.json').read_text())
G = P['geometry']
H = 1000*G['pivot_height_m']
OUT = ROOT / 'cad/review_b'
STUDY = 'DESIGN STUDY — NOT RELEASED FOR MANUFACTURE OR POWERED CATCHING'
COLORS = {'stationary':(.55,.59,.64), 'yaw':(.22,.44,.57), 'pitch':(.32,.51,.36),
          'bearing':(.72,.73,.75), 'hardware':(.36,.38,.41), 'print':(.80,.52,.24),
          'envelope':(.83,.29,.21), 'guard':(.62,.70,.76), 'wire':(.80,.57,.14)}


def box(x,y,z,origin):
    return Part.makeBox(x,y,z,Vector(*origin))


def cylinder(d,length,origin,axis=(0,0,1)):
    return Part.makeCylinder(d/2,length,Vector(*origin),Vector(*axis))


def cuts(shape,tools):
    for tool in tools:
        shape=shape.cut(tool)
    return shape.removeSplitter()


def annulus(od,ident,width,origin,axis=(0,0,1)):
    v=Vector(*axis)
    return cylinder(od,width,origin,axis).cut(
        cylinder(ident,width+2,tuple(Vector(*origin)-v),axis)).removeSplitter()


def part(doc,name,shape,motion='stationary',material='6061-T6 stock',kind='stationary',
         function='',density=2700,estimated_mass=None,interface='Detailed stock geometry; fits still require coupons'):
    if shape.isNull() or not shape.isValid() or not shape.Solids:
        raise ValueError('Invalid part '+name)
    o=doc.addObject('PartDesign::Feature',name)
    o.Shape=shape
    values={'AssemblyMotion':motion,'MaterialSpec':material,'ReleaseStatus':STUDY,
            'Function':function,'InterfaceStatus':interface,'GeometryKind':kind}
    for key,value in values.items():
        o.addProperty('App::PropertyString',key,'Engineering')
        setattr(o,key,value)
    o.addProperty('App::PropertyFloat','EstimatedMassKg','Engineering')
    o.EstimatedMassKg=shape.Volume*density*1e-9 if estimated_mass is None else estimated_mass
    o.addProperty('App::PropertyFloat','DensityKgM3','Engineering')
    o.DensityKgM3=density
    o.addProperty('App::PropertyString','MassBasis','Engineering')
    o.MassBasis=('solid geometry × assumed density; print mass is an upper screen'
                 if estimated_mass is None else 'explicit allowance, not supplier verified')
    if App.GuiUp:
        o.ViewObject.ShapeColor=COLORS[kind]
        if kind in ('envelope','wire'): o.ViewObject.Transparency=68
        if kind=='guard': o.ViewObject.Transparency=55
    return o


def bolt(doc,name,d,length,origin,axis=(0,0,1),motion='stationary'):
    # Threadless hardware representation. Hole edge distances and wrench access
    # must be checked against the selected screw, nut and washer series.
    normal=Vector(*axis)
    body=cylinder(d,length,origin,axis)
    head=cylinder(1.7*d,.65*d,tuple(Vector(*origin)-normal*.65*d),axis)
    return part(doc,name,body.fuse(head),motion,'Steel purchased screw','hardware',
                'Through bolt; actual thread engagement and washers require hardware drawing',
                7850,interface='Nominal clearance assembly; no printable thread')


def flat_link(a,b,width=25,thickness=3,normal=(0,1,0),hole_d=6.6):
    a,b,n=Vector(*a),Vector(*b),Vector(*normal)
    along=b-a
    along.normalize()
    side=n.cross(along)
    side.normalize()
    points=[a-side*width/2,b-side*width/2,b+side*width/2,a+side*width/2]
    face=Part.Face(Part.makePolygon(points+[points[0]]))
    sh=face.extrude(n*thickness)
    for point in (a,b):
        sh=sh.fuse(Part.makeCylinder(width/2,thickness,point,n))
        sh=sh.cut(Part.makeCylinder(hole_d/2,thickness+2,point-n,n))
    return sh.removeSplitter()


def hole_plate(x,y,t,origin,holes,d=6.6):
    sh=box(x,y,t,origin)
    return cuts(sh,[cylinder(d,t+2,(hx,hy,origin[2]-1)) for hx,hy in holes])


def bearing(doc,name,ident,od,width,origin,axis,motion='yaw'):
    return part(doc,name,annulus(od,ident,width,origin,axis),motion,
                'Purchased sealed ball bearing','bearing','Dimensioned bearing envelope; supplier rating required',
                7850,interface=f'Nominal {ident}×{od}×{width} mm; races, seals and clearance not modeled')


def jack_cartridge(doc,name,center,axis,motion):
    """8mm-wide radial seat and removable3mm outer-race cap before the seat.

    center is the leading bearing face. The following stock plate is the opposite
    shoulder. Two M4 holes are common to cap, carrier and the mating stock plate.
    Actual fits/shims and shaft inner-race collars still require supplier dimensions.
    """
    rotation=App.Rotation(Vector(0,0,1),Vector(*axis))
    carrier=box(44,44,8,(-22,-22,0)).cut(cylinder(28.15,10,(0,0,-1)))
    cap=box(44,44,3,(-22,-22,-3)).cut(cylinder(22,5,(0,0,-4)))
    for x in (-18,18):
        carrier=carrier.cut(cylinder(4.5,10,(x,0,-1)))
        cap=cap.cut(cylinder(4.5,5,(x,0,-4)))
    for suffix,shape in [('Carrier',carrier),('Cap',cap)]:
        shape.Placement=App.Placement(Vector(*center),rotation)
        part(doc,name+suffix,shape,motion,'Nylon fit carrier' if suffix=='Carrier' else '6061-T6 stock',
             'print' if suffix=='Carrier' else ('yaw' if motion=='yaw' else 'stationary'),
             'Full-width radial bearing seat and matching M4 retainer pattern; shaft collars and preload remain gates',
             1250 if suffix=='Carrier' else 2700)


def bearing_cartridge_z(doc,name,ident,od,width,z,motion='stationary'):
    # Shoulder supports outer race; removable metal top cap provides retention.
    base=hole_plate(76,76,width+4,(-38,-38,z),[(x,y) for x in (-29,29) for y in (-29,29)])
    base=base.cut(cylinder(od+.15,width+1,(0,0,z+3)))
    base=base.cut(cylinder(ident+6,width+6,(0,0,z-1)))
    part(doc,name+'Cartridge',base,motion,'Nylon fit prototype / purchased metal housing after qualification',
         'print','Replaceable shoulder bearing cartridge; four M6 tie bolts',1250)
    bearing(doc,name+'Bearing',ident,od,width,(0,0,z+3),(0,0,1),motion)
    cap=hole_plate(76,76,3,(-38,-38,z+width+4),[(x,y) for x in (-29,29) for y in (-29,29)])
    cap=cap.cut(cylinder(od-4,5,(0,0,z+width+3)))
    part(doc,name+'OuterRaceCap',cap,motion,function='3mm metal outer-race retainer; axial shims required')
    return z+3,z+3+width


def pulley(doc,name,teeth,width,center,axis,bore,motion):
    radius=teeth*5/(2*math.pi)
    a=Vector(*axis);start=Vector(*center)-a*width/2
    sh=annulus(2*radius,bore,width,tuple(start),axis)
    return part(doc,name,sh,motion,'Purchased HTD5 pulley; pitch envelope only','envelope',
                f'{teeth} teeth, 5mm pitch, belt center plane explicit; not a machinable tooth model',
                estimated_mass=.04 if teeth<=20 else .12 if teeth<=40 else .24,
                interface='Exact bore, hub, flange, tooth form, belt rating and supplier SKU unresolved')


def belt_stage(doc,name,c1,c2,n1,n2,axis,motion,width=9):
    # Full rings + correct external tangent spans are pitch-path envelopes only.
    a=Vector(*axis);p1,p2=Vector(*c1),Vector(*c2)
    e=p2-p1;distance=e.Length;e.normalize()
    perp=a.cross(e);perp.normalize()
    r1,r2=n1*5/(2*math.pi),n2*5/(2*math.pi)
    ratio=(r1-r2)/distance
    if abs(ratio)>=1: raise ValueError('invalid pulley center spacing')
    shapes=[annulus(2*r1+1.5,2*r1-1.5,width,tuple(p1-a*width/2),axis),
            annulus(2*r2+1.5,2*r2-1.5,width,tuple(p2-a*width/2),axis)]
    for sign in (-1,1):
        n=e*ratio+perp*(sign*math.sqrt(1-ratio*ratio))
        start,end=p1+n*r1,p2+n*r2
        tangent=end-start;tangent.normalize()
        face_points=[start-a*width/2,end-a*width/2,end+a*width/2,start+a*width/2]
        sh=Part.Face(Part.makePolygon(face_points+[face_points[0]])).extrude(n*1.5)
        shapes.append(sh)
    part(doc,name,Part.makeCompound(shapes),motion,'Purchased timing belt pitch path','envelope',
         f'{n1}:{n2}; center spacing {distance:.2f}mm; actual belt length/tension travel not frozen',
         estimated_mass=.025,interface='Pitch-path envelope only; complete rings deliberately overbound actual wrap')
    return dict(name=name,driver_teeth=n1,driven_teeth=n2,center_distance_mm=distance,
                pitch_length_screen_mm=2*distance+math.pi*(r1+r2)+(r2-r1)**2/distance,
                ratio=n2/n1)


def motor(doc,name,center,axis,motion,size=57,length=56,shaft=6.35,mass=1.0):
    # Local motor face z=0; body behind, shaft forward. Transform exactly once.
    sh=box(size,size,length,(-size/2,-size/2,-length))
    sh=sh.fuse(cylinder(38 if size==57 else 22,2,(0,0,0)))
    sh=sh.fuse(cylinder(shaft,22,(0,0,2)))
    rotation=App.Rotation(Vector(0,0,1),Vector(*axis))
    sh.Placement=App.Placement(Vector(*center),rotation)
    return part(doc,name,sh,motion,'Purchased closed-loop motor candidate','envelope',
                'Motor body/shaft packaging only; no claimed torque-speed capacity',estimated_mass=mass,
                interface='Supplier drawing, connector protrusions and mounting register not released')


def build(extension_mm=250,yaw_deg=0,pitch_deg=20,claw_angle_deg=20,
          pivot_height_mm=None, stiffened_yoke=True):
    H=1000*G['pivot_height_m'] if pivot_height_mm is None else pivot_height_mm
    if not math.isfinite(H) or not 650<=H<=900:
        raise ValueError('shoulder study height must be650–900mm')
    if not -70<=yaw_deg<=70 or not -15<=pitch_deg<=70:
        raise ValueError('pose outside design angular range')
    doc=telescope.build(extension_mm,claw_angle_deg)
    # These placeholder shafts are superseded in THIS NEW document only.
    for o in list(doc.Objects):
        if o.Name.startswith('Trunnion_'):doc.removeObject(o.Name)
    doc.Label=f'Variable Reach Arm — full Rev B study — {extension_mm}mm extension'
    for o in list(doc.Objects):
        if not hasattr(o,'Shape'):continue
        o.addProperty('App::PropertyString','AssemblyMotion','Engineering')
        o.AssemblyMotion='pitch'
        # Telescope root objects already contain all local extension/claw transforms.
        sh=o.Shape.copy()
        sh.rotate(Vector(),Vector(0,1,0),-pitch_deg)
        sh.translate(Vector(0,0,H))
        sh.rotate(Vector(),Vector(0,0,1),yaw_deg)
        o.Shape=sh
    existing=set(o.Name for o in doc.Objects)

    # Bench attachment and a short stock column under the yaw bearing cage.
    base=hole_plate(300,300,6,(-150,-150,0),[(x,y) for x in (-130,130) for y in (-130,130)],8.5)
    brace_specs=[((-120,28,24),(0,28,250),(0,1,0)),
                 ((120,31,24),(0,31,250),(0,1,0)),
                 ((28,-120,24),(28,0,360),(1,0,0)),
                 ((31,120,24),(31,0,360),(1,0,0))]
    column_crossings=[(38,(1,0,0)),(50,(0,1,0)),(62,(1,0,0)),
                      (74,(0,1,0)),(250,(0,1,0)),(360,(1,0,0)),(374,(1,0,0))]
    for x,y in [(43,0),(-43,0),(0,43),(0,-43)]+[(a[0],a[1]) for a,_,_ in brace_specs]:
        base=base.cut(cylinder(6.6,8,(x,y,-1)))
    part(doc,'BasePlate300x300x6',base,function='Four M8 bench anchors, stock plate; not a freestanding unanchored base')
    column=box(50,50,392,(-25,-25,6)).cut(box(46,46,394,(-23,-23,5)))
    for z,axis in column_crossings:
        origin=(-26,0,z) if axis==(1,0,0) else (0,-26,z)
        column=column.cut(cylinder(6.6,52,origin,axis))
    part(doc,'Column50x50x2',column,function='Hollow stock column, through-bolted with crush sleeves; no massive solid mast')
    # Four bent/stock angles join column to plate; each has actual clearance bores.
    for i in range(4):
        sh=box(25,30,3,(25,-15,6)).fuse(box(3,30,76,(25,-15,9)))
        sh=sh.cut(cylinder(6.6,5,(43,0,5)))
        for z in ((38,62) if i%2==0 else (50,74)):
            sh=sh.cut(cylinder(6.6,5,(24,0,z),(1,0,0)))
        sh.rotate(Vector(),Vector(0,0,1),90*i)
        part(doc,f'ColumnFootAngle_{i}',sh,function='Cut/drilled 30mm stock angle; base M6 and two cross-column bolts')
    for i,(a,b,normal) in enumerate(brace_specs):
        part(doc,f'ColumnDiagonalBrace_{i}',flat_link(a,b,normal=normal),function='25×3 aluminum flat-stock brace; M6 end holes')
        # Foot angle surrounds base bolt and carries the brace's horizontal bolt.
        if normal==(0,1,0):
            x,plane=a[0],a[1]
            sh=box(30,22,3,(x-15,plane-11,6)).fuse(box(30,3,30,(x-15,plane-3,9)))
            sh=sh.cut(cylinder(6.6,6,(x,plane,5))).cut(cylinder(6.6,5,(x,plane-4,24),(0,1,0)))
        else:
            y,plane=a[1],a[0]
            sh=box(22,30,3,(plane-11,y-15,6)).fuse(box(3,30,30,(plane-3,y-15,9)))
            sh=sh.cut(cylinder(6.6,6,(plane,y,5))).cut(cylinder(6.6,5,(plane-4,y,24),(1,0,0)))
        part(doc,f'BraceFootAngle_{i}',sh,function='Stock angle foot, one vertical base bolt and one transverse brace bolt')
    # One shared upper screw per stacked pair. Orthogonal bolts cannot cross.
    bolt(doc,'BraceUpperBolt_Y',6,66,(0,34,250),(0,-1,0))
    bolt(doc,'BraceUpperBolt_X',6,66,(34,0,360),(-1,0,0))
    part(doc,'BraceUpperStandOff_Y',annulus(12,6.6,3,(0,25,250),(0,1,0)),
         material='Steel spacer',kind='hardware',density=7850,function='Three millimetre spacer between column and first stacked brace')
    part(doc,'BraceUpperStandOff_X',annulus(12,6.6,3,(25,0,360),(1,0,0)),
         material='Steel spacer',kind='hardware',density=7850,function='Three millimetre spacer between column and first stacked brace')
    # Crush tubes support tightening forces across the thin-wall mast.
    for z,axis in column_crossings:
        origin=(-23,0,z) if axis==(1,0,0) else (0,-23,z)
        part(doc,f'ColumnCrushSleeve_{z}',annulus(10,6.6,46,origin,axis),material='Steel tube',
             kind='hardware',density=7850,function='One internal sleeve per actual bolt; orthogonal crossing heights staggered')

    # The left posts must clear the long output-stage tangent, not only the80T disk.
    cage_holes=[(x,y) for x in (-40,40) for y in (-65,65)]
    yaw_jack_posts=[(x,y) for x in (-155,-60) for y in (-70,70)]
    lower=hole_plate(250,220,6,(-170,-130,398),[(x,y) for x in (-29,29) for y in (-29,29)]+cage_holes)
    lower=lower.cut(cylinder(26,8,(0,0,397)))
    lower=lower.cut(cylinder(22,8,(-115,0,397)))
    lower=lower.cut(cylinder(38.5,8,(-85,-85,397)))
    for x in (-85-23.57,-85+23.57):
        for y in (-85-23.57,-85+23.57):lower=lower.cut(cylinder(5.5,8,(x,y,397)))
    for x,y in yaw_jack_posts+[(-133,0),(-97,0)]:lower=lower.cut(cylinder(4.5,8,(x,y,397)))
    part(doc,'YawLowerDeck',lower,function='Stock6mm plate; column-cap/drive deck; finish drilling from selected hardware')
    bearing_cartridge_z(doc,'YawLower',20,47,14,404)
    upper=hole_plate(130,150,6,(-65,-75,490),[(x,y) for x in (-29,29) for y in (-29,29)]+cage_holes)
    upper=upper.cut(cylinder(26,8,(0,0,489)))
    part(doc,'YawUpperDeck',upper,function='Upper bearing deck; four M6 tie rods and spacer columns')
    bearing_cartridge_z(doc,'YawUpper',20,47,14,496)
    for i,(x,y) in enumerate(cage_holes):
        part(doc,f'YawCageSpacer_{i}',annulus(12,6.6,86,(x,y,404)),material='Steel tube',
             kind='hardware',density=7850,function='Bearing-cage spacer; matching M6 holes x±40/y±65mm clear pulley and tangents; supplier flanges still require check')
    yawshaft=cylinder(20,155,(0,0,390))
    yawshaft=yawshaft.cut(box(6,4,130,(-3,7,402)))
    part(doc,'YawKeyedShaft20',yawshaft,'yaw','Steel purchased keyed shaft','hardware',
         '20mm shaft, separate 6mm key stock; bearing span92mm',7850,
         interface='Purchased keyway/shaft shoulders or qualified clamp collars, not hand-filed torque joint')
    part(doc,'YawInnerRaceSpacer',annulus(28,20,4,(0,0,513)),'yaw','Steel inner-race spacer','hardware',
         'Bridges inner race to collar through clearance in outer-race cap',7850)
    part(doc,'YawUpperShaftCollar',annulus(34,20,8,(0,0,517)),'yaw','Purchased split shaft collar','hardware',
         'Retains inner race axial stack; shim and axial-load path require proof',7850)
    hub=annulus(60,20,10,(0,0,525))
    hub=cuts(hub,[cylinder(6.6,12,(x,y,524)) for x,y in ((20,0),(-20,0),(0,20),(0,-20))])
    part(doc,'YawFlangedHub',hub,'yaw','Purchased keyed/clamping flange hub','envelope',
         'Four M6 through bolts transfer flange load into turret plate',estimated_mass=.18,
         interface='Exact rated hub SKU and key engagement pending')
    # Keep the yoke interface height while replacing a broad6mm slab with3mm
    # stock over a local metal hub spacer. The existing foot angles stiffen edges.
    hub_spacer=annulus(60,22,3,(0,0,535))
    hub_spacer=cuts(hub_spacer,[cylinder(6.6,5,(x,y,534)) for x,y in ((20,0),(-20,0),(0,20),(0,-20))])
    part(doc,'YawHubPlateSpacer',hub_spacer,'yaw',kind='yaw',
         function='Local3mm hub spacer under thinner turret; through-bolted load path')
    turret=hole_plate(180,210,3,(-90,-105,538),[(20,0),(-20,0),(0,20),(0,-20)])
    turret=turret.cut(cylinder(22,8,(0,0,534)))
    for x in (-55,55):
        for y in (-94,94):turret=turret.cut(cylinder(6.6,5,(x,y,537)))
    part(doc,'RotatingTurretPlate',turret,'yaw',kind='yaw',
         function='Yaw flange to two pitch cheek plates; metal stock plate and foot angles')
    for i,(x,y) in enumerate(((20,0),(-20,0),(0,20),(0,-20))):
        bolt(doc,f'YawHubM6_{i}',6,20,(x,y,541),(0,0,-1),'yaw')

    # Pitch yoke holds two EXTERNAL stub bearings; the telescope bore stays clear.
    for sign in (-1,1):
        y=79 if sign>0 else -82
        cheek=box(160,3,H+41-544,(-80,y,544))
        cheek=cheek.cut(cylinder(22,8,(0,y-1,H),(0,1,0)))
        # Material removed away from the bearing load path; leave perimeter and root webs.
        cheek=cheek.cut(box(75,8,48,(-37.5,y-1,H-85)))
        if stiffened_yoke and H>750:
            # Keep30mm edge webs and a20mm cross-web below the bearing window.
            # The stock-angle flanges retain section depth; remove the low-load
            # central sheet instead of paying a full solid-web mass penalty.
            cheek=cheek.cut(box(100,8,H-105-585,(-50,y-1,585)))
        for x in (-55,55):
            for z in (553,H+22):
                cheek=cheek.cut(cylinder(6.6,8,(x,y-1,z),(0,1,0)))
        part(doc,f'PitchYokeCheek_{sign+1}',cheek,'yaw',kind='yaw',
             function='3mm stock web; bearing reaction lies in plate plane; foot angles support bottom without overlap')
        bearing_origin=(0,82 if sign>0 else -90,H)
        bearing(doc,f'Pitch6001_{sign+1}',12,28,8,bearing_origin,(0,1,0),'yaw')
        housing_y=82 if sign>0 else -90
        housing=box(48,8,48,(-24,housing_y,H-24))
        housing=housing.cut(cylinder(28.15,10,(0,housing_y-1,H),(0,1,0)))
        for x in (-18,18):
            housing=housing.cut(cylinder(4.5,10,(x,housing_y-1,H),(0,1,0)))
            cheek_hole=cylinder(4.5,8,(x,y-1,H),(0,1,0))
            obj=doc.getObject(f'PitchYokeCheek_{sign+1}')
            obj.Shape=obj.Shape.cut(cheek_hole)
        part(doc,f'PitchBearingCarrier_{sign+1}',housing,'yaw','Nylon fit carrier / qualified metal if required',
             'print','Outer race is radially supported and captured between shoulder plate and removable cap',1250)
        # Split cap/shoulder cartridge interface represented with real two bolt holes.
        cap=box(48,5,48,(-24,90 if sign>0 else -95,H-24))
        cap=cap.cut(cylinder(22,7,(0,89 if sign>0 else -96,H),(0,1,0)))
        for x in (-18,18):
            cap=cap.cut(cylinder(4.5,7,(x,89 if sign>0 else -96,H),(0,1,0)))
        part(doc,f'PitchBearingOuterCap_{sign+1}',cap,'yaw',kind='yaw',
             function='Outer-race capture plate; shim stack and seated bearing housing unresolved')
        angle=box(150,30,3,(-75,76 if sign>0 else -106,541))
        angle=angle.fuse(box(150,3,30,(-75,76 if sign>0 else -79,544)))
        for x in (-55,55):
            angle=angle.cut(cylinder(6.6,5,(x,94 if sign>0 else -94,540)))
            angle=angle.cut(cylinder(6.6,5,(x,75 if sign>0 else -80,553),(0,1,0)))
        part(doc,f'YokeFootAngle_{sign+1}',angle,'yaw',kind='yaw',
             function='30×30×3 stock angle connects cheek to turret; M6 access from outside')
        if stiffened_yoke:
            # External stock-angle edge flanges give the taller web out-of-plane
            # depth. Rear leg is trimmed to15mm to clear the drive backplate.
            for edge in (-1,1):
                x0=-83 if edge<0 else 50
                face=box(33,3,H+30-544,(x0,82 if sign>0 else -85,544))
                depth=15 if edge<0 else 30
                lip=box(3,depth,H+30-544,(-83 if edge<0 else 80,
                         82 if sign>0 else -82-depth,544))
                angle=face.fuse(lip)
                for z in (580,H-70,H+20):
                    axis=(0,-sign,0)
                    origin=(edge*65,sign*86,z)
                    tool=cylinder(5.5,12,origin,axis)
                    angle=angle.cut(tool)
                    cheek_obj=doc.getObject(f'PitchYokeCheek_{sign+1}')
                    cheek_obj.Shape=cheek_obj.Shape.cut(tool)
                    bolt(doc,f'YokeFlangeBolt_{sign}_{edge}_{int(z)}',5,12,
                         (edge*65,sign*85,z),axis,'yaw')
                part(doc,f'YokeEdgeAngle_{sign}_{edge}',angle.removeSplitter(),'yaw',kind='yaw',
                     function='30×30×3 stock angle; rear flange trimmed to15mm; M5 through bolts; stiffness study, no fatigue qualification')

    # Root saddles are mounted to the square outer tube without any cross-bore shaft.
    side=1000*G['outer_side_m']
    for x0 in (-70,40):
        for half in ('bottom','top'):
            sh=telescope.split_collar(side,wall=5,length=30,half=half)
            sh.translate(Vector(x0,0,0))
            part(doc,f'BoomSaddle_{x0}_{half}',sh,'pitch','6061-T6 clamp or qualified nylon saddle',
                 'pitch','Split root collar; four M4 through bolts, no screw crushing the tube')
    for sign in (-1,1):
        y=39.05 if sign>0 else -45.05
        rail=box(140,6,50,(-70,y,-25))
        for x in (-64,-46,46,64):
            # Vertical cross bolts will attach separate saddle ear shoes; do not imply weld.
            rail=rail.cut(cylinder(4.5,8,(x,y-1,17),(0,1,0)))
        for angle in (45,135,225,315):
            x,z=16*math.cos(math.radians(angle)),16*math.sin(math.radians(angle))
            rail=rail.cut(cylinder(4.5,8,(x,y-1,z),(0,1,0)))
        part(doc,f'BoomTrunnionSideRail_{sign+1}',rail,'pitch',kind='pitch',
             function='External rail clears saddle ears; four M4 horizontal shoe bolts plus four flange bolts')
        for x0 in (-70,40):
            # Seven millimetres from vertical M4 bolt axis to upright admits an
            # M4 nut/washer and a small socket; the old2mm offset trapped the nut.
            shoe=box(30,15,3,(x0,24.05,6)).fuse(box(30,3,16,(x0,36.05,9)))
            for x in (x0+6,x0+24):
                shoe=shoe.cut(cylinder(4.5,5,(x,29.05,5)))
                shoe=shoe.cut(cylinder(4.5,5,(x,35.05,17),(0,1,0)))
            if sign<0:shoe.rotate(Vector(),Vector(0,0,1),180);shoe.translate(Vector(2*x0+30,0,0))
            part(doc,f'SaddleRailShoe_{x0}_{sign+1}',shoe,'pitch',kind='pitch',
                 function='Drilled3mm metal angle: vertical common saddle bolts and horizontal rail bolts; no bonded joint')
        hub_y=45.05 if sign>0 else -55.05
        flange=annulus(44,12,10,(0,hub_y,0),(0,1,0))
        flange=flange.cut(box(4,12,3,(-2,hub_y-1,5)))
        for angle in (45,135,225,315):
            x,z=16*math.cos(math.radians(angle)),16*math.sin(math.radians(angle))
            flange=flange.cut(cylinder(4.5,12,(x,hub_y-1,z),(0,1,0)))
        part(doc,f'PitchKeyedFlangeHub_{sign+1}',flange,'pitch','Purchased keyed flanged hub',
             'envelope','Four M4 flange bolts, external12mm keyed stub, no shaft through telescope',estimated_mass=.10,
             interface='Exact clamp/key/hub torque rating and shoulder stack require purchased drawings')
        start=45.05 if sign>0 else -124
        stub=cylinder(12,78.95,(0,start,0),(0,1,0))
        stub=stub.cut(box(4,95,3,(-2,start-.5,4)))
        part(doc,f'PitchKeyedStub12_{sign+1}',stub,'pitch','Steel purchased keyed shaft','hardware',
             'Two separate external shafts; driven bearing to output pulley center20mm',7850)
        part(doc,f'PitchShaftKey_{sign+1}',box(4,18,4,(-2,46 if sign>0 else -64,4)),
             'pitch','Steel4×4 key','hardware','Purchased key fitted to actual shaft/hub tolerances',7850)

    # Two-stage pitch8:1, all axis center planes and jackshaft support explicit.
    stages=[]
    stages.append(belt_stage(doc,'PitchStage1Belt',(-55,132,H-90),(-130,132,H-90),20,40,(0,1,0),'yaw'))
    stages.append(belt_stage(doc,'PitchStage2Belt',(-130,110,H-90),(0,110,H),20,80,(0,1,0),'yaw'))
    for name,n,c in [('PitchMotor20',20,(-55,132,H-90)),('PitchJack40',40,(-130,132,H-90)),
                      ('PitchJack20',20,(-130,110,H-90)),('PitchOutput80',80,(0,110,H))]:
        pulley(doc,name,n,9,c,(0,1,0),6.35 if 'Motor' in name else 12,'yaw')
    motor(doc,'PitchMotorCandidate',(-55,154,H-90),(0,-1,0),'yaw')
    motor_mount=box(74,4,74,(-92,150,H-127))
    motor_mount=motor_mount.cut(cylinder(38.5,6,(-55,149,H-90),(0,1,0)))
    for x in (-55-23.57,-55+23.57):
        for z in (H-90-23.57,H-90+23.57):
            motor_mount=motor_mount.cut(cylinder(5.5,6,(x,149,z),(0,1,0)))
    part(doc,'PitchMotorSlottedPlateStudy',motor_mount,'yaw',kind='yaw',
         function='NEMA23 pattern nominal; adjustment slots/exact register from selected motor')
    drive_back=box(195,3,170,(-163,99,H-128))
    drive_back=drive_back.cut(cylinder(22,8,(0,95,H),(0,1,0)))
    drive_back=drive_back.cut(cylinder(22,8,(-130,95,H-90),(0,1,0)))
    # Bottom edge rests above the turret/foot angle instead of intersecting them.
    drive_back=drive_back.cut(box(140,8,24,(-95,95,H-130)))
    # Remove area between supported corners, retaining connected stock webs.
    drive_back=drive_back.cut(box(55,8,45,(-90,95,H-72)))
    for x in (-18,18):
        drive_back=drive_back.cut(cylinder(4.5,8,(x,95,H),(0,1,0)))
        drive_back=drive_back.cut(cylinder(4.5,8,(-130+x,95,H-90),(0,1,0)))
    pitch_tie_points=[(-154,H-125),(-106,H-125),(-154,H-52)]
    for x,z in pitch_tie_points:drive_back=drive_back.cut(cylinder(4.5,8,(x,95,z),(0,1,0)))
    part(doc,'PitchDriveBackplate',drive_back,'yaw',kind='yaw',
         function='Bolted drive carrier; output bearing/shaft clearance and jackshaft support')
    drive_front=box(70,6,96,(-165,154,H-138))
    drive_front=drive_front.cut(cylinder(22,8,(-130,153,H-90),(0,1,0)))
    for x in (-148,-112):drive_front=drive_front.cut(cylinder(4.5,8,(x,153,H-90),(0,1,0)))
    for x,z in pitch_tie_points:drive_front=drive_front.cut(cylinder(4.5,8,(x,153,z),(0,1,0)))
    part(doc,'PitchJackOuterSupport',drive_front,'yaw',kind='yaw',
         function='Second jackshaft bearing, avoids cantilevered compound pulley')
    for y in (91,146):
        bearing(doc,f'PitchJackBearing_{y}',12,28,8,(-130,y,H-90),(0,1,0),'yaw')
        jack_cartridge(doc,f'PitchJack_{y}',(-130,y,H-90),(0,1,0),'yaw')
    part(doc,'PitchJackshaft12',cylinder(12,76,(-130,88,H-90),(0,1,0)),'yaw',
         'Purchased keyed12mm shaft','hardware','Compound40/20 pulleys between two bearings',7850)
    for x,z in pitch_tie_points:
        part(doc,f'PitchDriveSpacer_{int(x)}_{int(z)}',annulus(10,4.5,52,(x,102,z),(0,1,0)),
             'yaw','Steel spacer tube','hardware','M4 tie bolt through tube to prevent plate bending',7850)
    brake=box(58,35,58,(-84,210,H-119))
    part(doc,'PitchNormallyOnBrakeEnvelope',brake,'yaw','Purchased spring-applied brake','envelope',
         'Candidate1.5Nm motor-side brake allowance; actual adapter/wiring fail-safe qualification required',
         estimated_mass=.35,interface='NOT installed/qualified hardware; added cost and mass gate')

    # Yaw6:1, compound30/20 jackshaft supported around both belt planes.
    stages.append(belt_stage(doc,'YawStage1Belt',(-85,-85,412),(-115,0,412),20,30,(0,0,1),'stationary'))
    stages.append(belt_stage(doc,'YawStage2Belt',(-115,0,448),(0,0,448),20,80,(0,0,1),'stationary'))
    for name,n,c,bore in [('YawMotor20',20,(-85,-85,412),6.35),('YawJack30',30,(-115,0,412),12),
                          ('YawJack20',20,(-115,0,448),12),('YawOutput80',80,(0,0,448),20)]:
        pulley(doc,name,n,9,c,(0,0,1),bore,'yaw' if name=='YawOutput80' else 'stationary')
    motor(doc,'YawMotorCandidate',(-85,-85,398),(0,0,1),'stationary')
    for z in (390,468):
        bearing(doc,f'YawJackBearing_{z}',12,28,8,(-115,0,z),(0,0,1),'stationary')
        jack_cartridge(doc,f'YawJack_{z}',(-115,0,z),(0,0,1),'stationary')
    part(doc,'YawJackshaft12',cylinder(12,94,(-115,0,386)),material='Purchased keyed12mm shaft',
         kind='hardware',density=7850,function='Compound30/20 pulleys, two supported bearing planes')
    yaw_front=hole_plate(115,160,6,(-165,-80,476),yaw_jack_posts+[(-133,0),(-97,0)],4.5)
    yaw_front=yaw_front.cut(cylinder(22,8,(-115,0,475)))
    # This stationary deck passes around the main yaw cage posts with2mm clearance.
    for x,y in cage_holes:yaw_front=yaw_front.cut(cylinder(16,8,(x,y,475)))
    part(doc,'YawJackUpperSupport',yaw_front,function='Second jackshaft support above upper belt; spacer stack to deck')
    for x,y in yaw_jack_posts:
        part(doc,f'YawDriveSpacer_{int(x)}_{int(y)}',annulus(10,4.5,72,(x,y,404)),
             material='Steel spacer',kind='hardware',density=7850,function='M4 tie rods across two bearing planes')
    # Extension motor is proximal on moving pitch assembly, aligned with imported GT2 drive.
    extx=1000*G['outer_start_m']-25
    extr=1000*G['extension_belt_pitch_m']*G['extension_pulley_teeth']/(2*math.pi)
    extz=1000*G['inner_side_m']/2+1.6+extr
    motor(doc,'ExtensionMotorCandidate',(extx,28,extz),(0,-1,0),'pitch',42,40,5,.35)
    extplate=box(52,3,52,(extx-26,25,extz-26))
    extplate=extplate.cut(cylinder(22.5,5,(extx,24,extz),(0,1,0)))
    for x in (extx-15.5,extx+15.5):
        for z in (extz-15.5,extz+15.5):
            extplate=extplate.cut(cylinder(3.5,5,(x,24,z),(0,1,0)))
    # Join the faceplate to the minimum-stop collar with a common bolted foot.
    # The cap-access relief keeps the stop's independently removable metal cap.
    bridge=box(35,10.9,3,(-254,25.1,12.6))
    bridge=bridge.cut(box(13.4,3,5,(-240.2,24.8,11.6)))
    for x in (-243.5,-223.5):
        bridge=bridge.cut(cylinder(4.5,5,(x,30.05,11.6)))
    extplate=extplate.fuse(bridge).removeSplitter()
    part(doc,'ExtensionMotorFacePlate',extplate,'pitch',kind='pitch',
         function='NEMA17 nominal register;3mm foot to minimum-stop collar through two common M4 bolts; supplier motor drawing pending')
    for i,x in enumerate((-243.5,-223.5)):
        # Imported telescope hardware is already posed; replace using the same
        # pitch transform and classify the new spacer as a fixed-boom part.
        fastener=doc.getObject(f'MinimumCollarBolt_{i}_1')
        replacement=cylinder(4,30,(x,30.05,-13.6)).fuse(cylinder(7,4,(x,30.05,16.4)))
        replacement.rotate(Vector(),Vector(0,1,0),-pitch_deg)
        replacement.translate(Vector(0,0,H));replacement.rotate(Vector(),Vector(0,0,1),yaw_deg)
        fastener.Shape=replacement
        washer=doc.getObject(f'MinimumCollarWasherTop_{i}_1')
        replacement=annulus(9,4.5,.8,(x,30.05,15.6))
        replacement.rotate(Vector(),Vector(0,1,0),-pitch_deg)
        replacement.translate(Vector(0,0,H));replacement.rotate(Vector(),Vector(0,0,1),yaw_deg)
        washer.Shape=replacement
        part(doc,f'ExtensionMountSpacer_{i}',annulus(8,4.5,5.8,(x,30.05,6.8)),
             'pitch','Metal spacer','hardware','Common M4x30 clamp/motor bracket bolt; verify measured grip stack',7850)

    # Front idler has two seated bearings and a removable inner retaining cap.
    # The complete split clamp can be shifted about2mm before tightening to set
    # belt tension; recesses admit the existing guide nuts across that adjustment.
    import telescope_guides
    for half in ('bottom','top'):
        collar=telescope.split_collar(side,wall=6,length=30,half=half)
        collar.translate(Vector(490,0,0))
        for angle,tangent,_ in telescope_guides.stations():
            for x in (494,498):
                pocket=box(10,7,5,(x-5,tangent-3.5,18.8))
                pocket.rotate(Vector(0,0,0),Vector(1,0,0),angle)
                collar=collar.cut(pocket)
        if half=='top':
            roof=box(62,42,4,(500,-21,44))
            for y in (-21,15):roof=roof.fuse(box(10,6,19,(500,y,25.05)))
            for sign in (-1,1):
                y=8 if sign>0 else -15
                housing=box(36,7,44-(extz-12),(526,y,extz-12))
                housing=housing.cut(cylinder(16.2,5,(545,8 if sign>0 else -13,extz),(0,1,0)))
                housing=housing.cut(cylinder(10,10,(545,6 if sign>0 else -16,extz),(0,1,0)))
                for x in (530,559):housing=housing.cut(cylinder(3.4,11,(x,5 if sign>0 else -16,extz+6),(0,1,0)))
                roof=roof.fuse(housing)
            collar=collar.fuse(roof).removeSplitter()
        part(doc,'IdlerClamp_'+half,collar,'pitch','Nylon qualified / PETG fit prototype','print',
             'Split clamp; guide-nut relief pockets; lock four M4 bolts after manual tension adjustment; proof grip',1250)
    for sign in (-1,1):
        y=8 if sign>0 else -13
        bearing(doc,f'Idler625Bearing_{sign}',5,16,5,(545,y,extz),(0,1,0),'pitch')
        cap=box(36,2,24,(526,6 if sign>0 else -8,extz-12))
        cap=cap.cut(cylinder(10,4,(545,5 if sign>0 else -9,extz),(0,1,0)))
        for x in (530,559):cap=cap.cut(cylinder(3.4,4,(x,5 if sign>0 else -9,extz+6),(0,1,0)))
        part(doc,f'IdlerBearingCap_{sign}',cap,'pitch',kind='pitch',
             function='2mm metal outer-race retaining plate; two M3 through bolts and nuts; actual fits require coupon')
        for x in (530,559):
            bolt(doc,f'IdlerCapBolt_{sign}_{x}',3,15,(x,sign*15,extz+6),(0,-sign,0),'pitch')
            import telescope_drive_details as td
            nut=td.hexnut(3,5.5,4,(0,0,0));nut=td.oriented_y(nut)
            nut.translate(Vector(x,2 if sign>0 else -6,extz+6))
            part(doc,f'IdlerCapNut_{sign}_{x}',nut,'pitch','Steel M3 locknut envelope','hardware',
                 'Install cap nuts before pulley; actual locknut height and thread engagement need supplier confirmation',7850)
        part(doc,f'IdlerInnerRaceSpacer_{sign}',annulus(8,5.1,2,(545,13 if sign>0 else -15,extz),(0,1,0)),
             'pitch','Metal spacer','hardware','Inner-race-only axial support; shim after supplier bearing fit',7850)
        part(doc,f'IdlerShaftCollar_{sign}',annulus(9,5.1,3,(545,15 if sign>0 else -18,extz),(0,1,0)),
             'pitch','Purchased5mm split shaft collar','hardware','Positive axial retention; exact collar screw envelope pending',7850)
    part(doc,'IdlerShaft5',cylinder(5,40,(545,-20,extz),(0,1,0)),
         'pitch','Ground steel5mm shaft','hardware','Purchased36T pulley clamped to rotating supported shaft',7850)
    for x in (496,514):
        for y in (-30.05,30.05):
            bolt(doc,f'IdlerClampBolt_{x}_{y}',4,20,(x,y,6.8),(0,0,-1),'pitch')
            part(doc,f'IdlerClampWasher_{x}_{y}',annulus(9,4.5,.8,(x,y,6)),
                 'pitch','Steel washer','hardware','Clamp load spreader',7850)
            part(doc,f'IdlerClampNut_{x}_{y}',td.hexnut(4,7,5,(x,y,-11)),
                 'pitch','Steel M4 locknut envelope','hardware','Confirm real grip and nut thread engagement',7850)

    # Practical stationary electronics packaging; actual power layout is a separate release.
    enclosure=box(122,82,55,(-141,-141,9)).cut(box(116,76,54,(-138,-138,12)))
    for x,y in [(-133,-133),(-27,-133),(-133,-67),(-27,-67)]:
        enclosure=enclosure.cut(cylinder(4.5,8,(x,y,7)))
    part(doc,'ElectronicsTray',enclosure,material='ASA/PETG',kind='print',density=1250,
         function='Open serviceable tray; logic/buck/terminal strips only, mains PSU external')
    part(doc,'ElectronicsLid',box(124,84,2,(-142,-142,64)),material='PETG',kind='guard',density=1250,
         function='Removable lid; cable glands, terminal spacing and heat openings require wiring layout')
    part(doc,'EmergencyStopEnvelope',cylinder(38,28,(112,-112,6)),material='Purchased latching mushroom',
         kind='envelope',estimated_mass=.08,function='Operator-accessible location; NC contactor circuit separate from firmware')
    yawguard=box(245,215,2,(-162,-132,485)).cut(cylinder(60,4,(0,0,484)))
    for x,y in cage_holes:yawguard=yawguard.cut(cylinder(16,4,(x,y,484)))
    part(doc,'YawBeltGuardEnvelope',yawguard,material='PETG/clear polycarbonate',
         kind='guard',density=1200,function='Guard cover position; access apertures and screw brackets incomplete')
    part(doc,'PitchBeltGuardEnvelope',box(220,2,205,(-172,250,H-142)),'yaw',
         'PETG/clear polycarbonate','guard','Guard panel location; complete side enclosure required',1200)
    # Swept service-loop corridor is translucent and excluded from structural mass.
    part(doc,'YawCableServiceLoopEnvelope',annulus(105,90,30,(0,0,520)),'yaw',
         'Cable exclusion corridor','wire','Finite140deg yaw service loop; no slip ring required',
         estimated_mass=0,interface='Routing envelope only; bend radius/strain relief and loop sweep not yet validated')

    # Newly added pitch members are expressed in the same local frame as telescope.
    for o in doc.Objects:
        if o.Name in existing or not hasattr(o,'Shape'):continue
        sh=o.Shape.copy()
        if o.AssemblyMotion=='pitch':
            sh.rotate(Vector(),Vector(0,1,0),-pitch_deg)
            sh.translate(Vector(0,0,H))
        if o.AssemblyMotion in ('pitch','yaw'):
            sh.rotate(Vector(),Vector(0,0,1),yaw_deg)
        o.Shape=sh
    sheet=doc.addObject('Spreadsheet::Sheet','FullAssemblyInterfaces')
    rows=[('Revision',P['revision']),('Status',STUDY),('PivotHeight_mm',str(H)),
          ('ReachReference','mouth center; L=700+s'),('Extension_mm',str(extension_mm)),
          ('Yaw_deg',str(yaw_deg)),('Pitch_deg',str(pitch_deg)),('PitchRatio','20:40 × 20:80 = 8:1'),
          ('YawRatio','20:30 × 20:80 = 6:1'),('PitchBearingCenters_y_mm','-86,+86'),
          ('YawBearingCenters_z_mm','414,506'),('MotorCurves','Not qualified'),
          ('FullManufacturingRelease','NO: see docs/full_cad_review.md')]
    for row,(key,value) in enumerate(rows,1):
        sheet.set(f'A{row}',key);sheet.set(f'B{row}',value)
    doc.recompute()
    return doc,stages


def mass_geometry(shape):
    # Compound belt envelopes have no single CenterOfMass attribute. Integrate
    # their solids with uniform volume weighting for this allowance-only screen.
    solids=shape.Solids
    volume=sum(s.Volume for s in solids)
    center=Vector()
    second=0.0
    for s in solids:
        c=s.CenterOfMass
        center += c*s.Volume
        second += s.MatrixOfInertia.A33+s.Volume*(c.x*c.x+c.y*c.y)
    return center/volume,second/volume


def collision_report(doc,threshold_mm3=.5):
    """Broad pairwise screen; never treats all envelopes as safe to intersect.

    Only the explicitly paired belt pitch paths and their own pulley pitch solids
    are ignored. Cable exclusion-corridor contacts are reported separately because
    the annular envelope represents permitted routing space, not a solid wire bundle.
    All other overlaps remain visible even while manufacturing_ready is false.
    """
    intentional={frozenset(pair) for pair in [
        ('PitchStage1Belt','PitchMotor20'),('PitchStage1Belt','PitchJack40'),
        ('PitchStage2Belt','PitchJack20'),('PitchStage2Belt','PitchOutput80'),
        ('YawStage1Belt','YawMotor20'),('YawStage1Belt','YawJack30'),
        ('YawStage2Belt','YawJack20'),('YawStage2Belt','YawOutput80'),
        ('BeltInsideEnvelope','DrivePulleyPitchEnvelope'),
        ('BeltInsideEnvelope','IdlerPulleyPitchEnvelope'),
        ('BeltInsideEndEnvelope','IdlerPulleyPitchEnvelope'),
        ('BeltReturnEnvelope','DrivePulleyPitchEnvelope'),
        ('BeltReturnEnvelope','IdlerPulleyPitchEnvelope')]}
    objects=[o for o in doc.Objects if hasattr(o,'Shape')]
    collisions=[]
    routing=[]
    ignored=[]
    for index,a in enumerate(objects):
        for b in objects[index+1:]:
            if not a.Shape.BoundBox.intersect(b.Shape.BoundBox):continue
            pair=frozenset((a.Name,b.Name))
            if pair in intentional:
                ignored.append([a.Name,b.Name]);continue
            volume=a.Shape.common(b.Shape).Volume
            if volume<=threshold_mm3:continue
            row=dict(part_a=a.Name,part_b=b.Name,overlap_mm3=volume)
            if 'YawCableServiceLoopEnvelope' in pair:routing.append(row)
            else:collisions.append(row)
    return dict(unresolved_part_intersections=sorted(collisions,key=lambda row:-row['overlap_mm3']),
                cable_routing_envelope_contacts=routing,
                intentional_pitch_path_pairs=ignored,
                threshold_mm3=threshold_mm3,
                limitation='Pose-specific solid screen; supplier flanges, tools, wires and missing interfaces still require full sweep')


def verify(doc,stages):
    invalid=[o.Name for o in doc.Objects if hasattr(o,'Shape') and (not o.Shape.isValid() or not o.Shape.Solids)]
    assert not invalid,invalid
    assert math.isclose(stages[0]['ratio']*stages[1]['ratio'],8)
    assert math.isclose(stages[2]['ratio']*stages[3]['ratio'],6)
    # Key requirement: external stubs never intrude into the sliding tube.
    conflicts={}
    for name in ('PitchKeyedStub12_0','PitchKeyedStub12_2','BoomTrunnionSideRail_0','BoomTrunnionSideRail_2'):
        for tube in ('InnerTube','OuterTube'):
            volume=doc.getObject(name).Shape.common(doc.getObject(tube).Shape).Volume
            conflicts[name+'__'+tube]=volume
            assert volume<1e-6,(name,tube,volume)
    masses={}
    yaw_inertia=0.0
    unknown=[]
    for o in doc.Objects:
        if not hasattr(o,'Shape'):continue
        if hasattr(o,'EstimatedMassKg'):
            if o.MassBasis.startswith('solid geometry'):
                o.EstimatedMassKg=o.Shape.Volume*o.DensityKgM3*1e-9
            masses[o.AssemblyMotion]=masses.get(o.AssemblyMotion,0)+o.EstimatedMassKg
            if o.AssemblyMotion=='yaw':
                _,second=mass_geometry(o.Shape)
                yaw_inertia += o.EstimatedMassKg*second*1e-6
        else:
            unknown.append(o.Name)
    collision_screen=collision_report(doc)
    return dict(status=STUDY,valid_solid_objects=sum(hasattr(o,'Shape') for o in doc.Objects),
                ratios_verified={'pitch':8,'yaw':6},belt_stages=stages,
                selected_intersections_mm3=conflicts,
                added_part_mass_screen_kg=masses,
                added_yaw_parts_inertia_screen_kgm2=yaw_inertia,
                broad_collision_screen=collision_screen,
                imported_telescope_objects_excluded_from_mass_screen=unknown,
                remaining_gates=['Complete supplier-specific hubs, bearings, brake and motors',
                  'Saddle/rail shoe bolt length and wrench access; clamp slip and thin-wall tube proof',
                  'Bearing seats, shaft shoulders, tie-bolt patterns and final access drawings',
                  'Final belt SKU lengths, tension slots, flange/tooth geometry and guards',
                  'Weigh parts and reconcile full rigid-body offsets with current mass allowances before procurement',
                  'Full robot swept self-collision including cables and brake',
                  'Qualify modeled rear anchor, stop collars, idler adjustment and motor bracket; complete flexible cable routing'],
                manufacturing_ready=False)


def export(extension_mm=250,yaw_deg=0,pitch_deg=20,claw_angle_deg=20,filename='VariableReachArm_Full_RevB',
           pivot_height_mm=None,stiffened_yoke=True):
    OUT.mkdir(parents=True,exist_ok=True)
    doc,stages=build(extension_mm,yaw_deg,pitch_deg,claw_angle_deg,pivot_height_mm,stiffened_yoke)
    result=verify(doc,stages)
    doc.saveAs(str(OUT/(filename+'.FCStd')))
    (OUT/(filename+'_checks.json')).write_text(json.dumps(result,indent=2)+'\n')
    rows=[]
    for o in doc.Objects:
        if hasattr(o,'EstimatedMassKg'):
            c,_=mass_geometry(o.Shape)
            rows.append(dict(part=o.Name,motion=o.AssemblyMotion,mass_screen_kg=o.EstimatedMassKg,
                             com_x_mm=c.x,com_y_mm=c.y,com_z_mm=c.z,
                             material=o.MaterialSpec,basis=o.MassBasis,release=o.InterfaceStatus))
    with (OUT/(filename+'_mass.csv')).open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
    if App.GuiUp:
        import FreeCADGui as Gui
        Gui.activeDocument().activeView().viewAxonometric()
        Gui.activeDocument().activeView().fitAll()
        Gui.activeDocument().activeView().saveImage(str(OUT/(filename+'.png')),1800,1100,'White')
    return result


if __name__=='__main__':
    print(json.dumps(export(),indent=2))



