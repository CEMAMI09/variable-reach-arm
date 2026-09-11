"""Three identical single-joint claws; no net. Dimensions in mm.

Mechanism development parts, not a high-speed release. One actuator pulls three
tendons to open; independent torsion springs close claws. Stops limit travel.
Measured closure time, spring force and pad absorption are release conditions.
"""
import math
import Part
from FreeCAD import Vector


def cylinder(radius,length,pos,axis=(0,1,0)):
    return Part.makeCylinder(radius,length,Vector(*pos),Vector(*axis))


def finger():
    # Ribbed flat profile: thickness8 in tangential direction; root hole bored
    # through solid boss. This is one connected link, not fused moving joints.
    points=[(0,-6),(67,14),(95,8),(103,-4),(112,1),(100,18),(70,24),(0,7)]
    vertices=[Vector(x,-4,z) for x,z in points]
    wire=Part.makePolygon(vertices+[vertices[0]])
    sh=Part.Face(wire).extrude(Vector(0,8,0))
    sh=sh.fuse(cylinder(7,8,(0,-4,0)))
    # Radial operating horn for tendon opening, mechanically integral with root.
    sh=sh.fuse(Part.makeBox(9,8,15,Vector(-4.5,-4,0)))
    sh=sh.cut(cylinder(1.65,10,(0,-5,0)))
    sh=sh.cut(cylinder(1.1,10,(0,-5,12)))
    # Torsion-spring moving leg anchor, separate from the tendon eye.
    sh=sh.cut(cylinder(0.6,10,(0,-5,5)))
    # Two distal M2 pad attachment holes, outside root and main flexure.
    for x,z in [(76,19),(94,13)]:
        sh=sh.cut(cylinder(1.2,10,(x,-5,z)))
    return sh.removeSplitter()


def palm():
    # Annular backplate lies behind pivot bosses so rotating claws do not cut it.
    sh=cylinder(46,4,(-16,0,0),(1,0,0)).cut(cylinder(30,6,(-17,0,0),(1,0,0)))
    for angle in [0,120,240]:
        ears=[]
        for y in [-10,6]:
            ear=Part.makeBox(24,4,16,Vector(-16,y,32))
            ear=ear.cut(cylinder(1.65,6,(0,y-1,40)))
            ear.rotate(Vector(),Vector(1,0,0),angle)
            ears.append(ear)
        for ear in ears:sh=sh.fuse(ear)
        # Metal horn pin follows a radiused slot: hard stops bound the 30deg range.
        # Outer sector lives outside the right ear, clear of the rotating finger.
        stop=Part.makeBox(16,3,12,Vector(-9,10,44))
        bridge=Part.makeBox(16,4,4,Vector(-9,6,44))
        stop=stop.fuse(bridge)
        # Annular slot plus rounded end caps; 0.5deg facets deviate <0.001mm.
        outer=[];inner=[]
        for step in range(61):
            theta=math.radians(-10+step*0.5)
            outer.append(Vector(-13.1*math.sin(theta),9,40+13.1*math.cos(theta)))
            inner.append(Vector(-10.9*math.sin(theta),9,40+10.9*math.cos(theta)))
        points=outer+list(reversed(inner))
        slot=Part.Face(Part.makePolygon(points+[points[0]])).extrude(Vector(0,5,0))
        for limit in (-10,20):
            theta=math.radians(limit)
            slot=slot.fuse(cylinder(1.1,5,(-12*math.sin(theta),9,40+12*math.cos(theta))))
        stop=stop.cut(slot)
        stop.rotate(Vector(),Vector(1,0,0),angle)
        sh=sh.fuse(stop)
        # Guide eye is part of the palm, connected to the rear of the pivot ear.
        guide=Part.makeBox(9,7,10,Vector(-25,-8,45))
        guide=guide.fuse(Part.makeBox(12,7,4,Vector(-20,-8,44)))
        guide=guide.cut(cylinder(1.25,12,(-26,-4.5,52),(1,0,0)))
        guide.rotate(Vector(),Vector(1,0,0),angle)
        sh=sh.fuse(guide)
        # Fixed spring-leg anchor in the right clevis ear.
        spring_hole=cylinder(0.6,6,(-4,5,44))
        spring_hole.rotate(Vector(),Vector(1,0,0),angle)
        sh=sh.cut(spring_hole)
        # Palm-pad screws on36mm radial bolt circle; clearance for M3 + nuts.
        a=math.radians(angle)
        sh=sh.cut(cylinder(1.7,7,(-17,36*math.sin(a),36*math.cos(a)),(1,0,0)))
    for y in [-36,36]:
        sh=sh.cut(cylinder(1.7,7,(-17,y,10),(1,0,0)))
    return sh.removeSplitter()


def pad():
    # Replaceable compliant palm with3 mounting ears. Printed TPU is NOT assumed
    # to provide25mm stroke: foam thickness and load/displacement must be tested.
    sh=cylinder(29,4,(-11,0,0),(1,0,0))
    for angle in [0,120,240]:
        ear=Part.makeBox(4,12,15,Vector(-11,-6,24))
        ear=ear.cut(cylinder(1.7,6,(-12,0,36),(1,0,0)))
        ear.rotate(Vector(),Vector(1,0,0),angle)
        sh=sh.fuse(ear)
    return sh.removeSplitter()


def add_servo_cradle(doc,add,mouth,nose):
    """Removable prototype cradle for the current24x13x29mm body allowance.

    Two top straps restrain the body; common M4 catcher-clamp bolts carry the
    bracket through5mm spacers. Replace dimensions after measuring the actual
    servo. This mounts the allowance body; it does not invent a working tendon
    linkage or servo mounting-flange drawing.
    """
    root=mouth-100
    floor=Part.makeBox(28,21.6,3,Vector(root-67,27.7,-17.5))
    # Four small corner towers support removable retention straps and through M2.
    for x in (root-61,root-47):
        for y in (27.7,45.3):
            tower=Part.makeBox(4,4,29,Vector(x,y,-14.5))
            floor=floor.fuse(tower)
            floor=floor.cut(cylinder(1.2,35,(x+2,y+2,-18),(0,0,1)))
    cy=(25.4+7)/2+5
    foot=Part.makeBox(22,9,3,Vector(nose-22,cy-4.5,15))
    for x in (nose-16,nose-6):
        foot=foot.cut(cylinder(2.25,5,(x,cy,14),(0,0,1)))
    a=Vector(nose-18,cy,16.5)
    elbow=Vector(nose-18,30,16.5)
    b=Vector(root-40,38.5,-16)
    direction=elbow-a
    arm=Part.makeCylinder(3.5,direction.Length,a,direction.normalize())
    direction=b-elbow
    arm=arm.fuse(Part.makeCylinder(3.5,direction.Length,elbow,direction.normalize()))
    cradle=floor.fuse(arm).fuse(foot)
    # Actual body allowance stays clear of the curved support transition.
    clearance=Part.makeBox(24.6,13.6,29.3,Vector(root-65.3,31.7,-14.5))
    # OCC's coplanar splitter removal invalidates this particular cut; keep the
    # valid refined-by-boolean solid rather than accepting invalid topology.
    cradle=cradle.cut(clearance)
    # Keep the curved support above the metal spacer seating faces. The servo
    # bracket also stops before the palm plate rather than sharing its volume.
    for x in (nose-16,nose-6):
        cradle=cradle.cut(cylinder(3.7,5,(x,cy,10),(0,0,1)))
    cradle=cradle.cut(Part.makeBox(100,120,120,Vector(root-16.3,-60,-60)))
    add(doc,'GripperServoCradle',cradle,'slider','PETG fit prototype / qualified ASA or nylon',True,
        'Two M4 common clamp bolts via5mm metal spacers; two M2 retained straps; measured servo SKU required')
    for i,x in enumerate((nose-16,nose-6)):
        spacer=cylinder(3.5,5,(x,cy,10),(0,0,1)).cut(cylinder(2.25,5,(x,cy,10),(0,0,1)))
        add(doc,f'ServoCradleSpacer_{i}',spacer,'slider','Metal spacer5mm',False,
            'Keeps separate mount clear of the catcher strut; include in actual M4 grip-length selection')
    for i,x in enumerate((root-61,root-47)):
        strap=Part.makeBox(4,21.6,2,Vector(x,27.7,14.5))
        for y in (29.7,47.3):strap=strap.cut(cylinder(1.2,4,(x+2,y,13.5),(0,0,1)))
        add(doc,f'ServoRetentionStrap_{i}',strap,'slider','PETG fit prototype',True,
            'M2 through bolts and washers to cradle floor; strap contacts allowance body without overlap')


def spring_shape(open_angle_deg):
    """Spring/formed-leg allowance in the unrotated finger frame (pivot z=40).

    Animation changes the moving leg endpoint; actual elastic stress and coil
    deflection need a qualified spring. No FreeCAD object placement is applied.
    """
    theta=math.radians(open_angle_deg)
    helix=Part.makeHelix(0.55,1.1,2.35)
    edge=Part.makeCircle(0.25,Vector(2.35,0,0),Vector(0,1,0))
    coil=Part.Wire(helix.Edges).makePipeShell([Part.Wire([edge])],True,False)
    coil.rotate(Vector(),Vector(1,0,0),-90)
    coil.translate(Vector(0,4.45,40))
    # Both formed spring legs are represented, including their inserted tips.
    # They sit in the right-side pocket, not across the ball capture opening.
    moving_anchor=Vector(-5*math.sin(theta),4.45,40+5*math.cos(theta))
    routes=[
        [Vector(2.35,4.45,40),Vector(5,4.45,40),Vector(5,4.45,45),
         moving_anchor,Vector(moving_anchor.x,3.5,moving_anchor.z)],
        [Vector(2.35,5.55,40),Vector(5,5.55,40),Vector(5,5.55,44),
         Vector(-4,5.55,44),Vector(-4,7,44)],
    ]
    for route in routes:
        for start,end in zip(route,route[1:]):
            direction=end-start
            wire_segment=Part.makeCylinder(0.25,direction.Length,start,direction.normalize())
            coil=coil.fuse(wire_segment).fuse(Part.makeSphere(0.25,start)).fuse(Part.makeSphere(0.25,end))
    return coil


def stop_eye_pin_shape(open_angle_deg):
    theta=math.radians(open_angle_deg)
    hx,hz=-12*math.sin(theta),40+12*math.cos(theta)
    # Free-spinning smooth pin keeps its tendon eye facing the fixed guide.
    return cylinder(1.0,19,(hx,-5.5,hz)).cut(cylinder(.5,4,(hx-2,-4.5,hz),(1,0,0)))


def add_gripper(doc,add,mouth,open_angle_deg=20):
    """Open mouth nominally nearL; actual swept claw front is aboutL+6mm.
    The planner usesL as nominal entry plane; closing/grasp volume needs calibration.
    """
    if not -10<=open_angle_deg<=20:raise ValueError('claw angle outside study range')
    root=mouth-100
    for name,shape,material in [('GripperPalm',palm(),'PETG/ASA fit prototype'),('PalmContactPad',pad(),'TPU plus replaceable foam')]:
        shape.translate(Vector(root,0,0))
        add(doc,name,shape,'slider',material,True,'Three steel M3 pivot pins; no net or fabric pocket')
    for index,angle in enumerate([0,120,240],1):
        sh=finger()
        sh.rotate(Vector(),Vector(0,1,0),-open_angle_deg)
        sh.translate(Vector(0,0,40))
        sh.rotate(Vector(),Vector(1,0,0),angle)
        sh.translate(Vector(root,0,0))
        add(doc,f'Claw_{index}',sh,'slider','Nylon or PETG prototype + TPU contact pads',True,
            'Single rigid link; steelM3 pin, replaceable torsion spring; one tendon opens each claw')
        pin=cylinder(1.5,25,(0,-12.5,40))
        pin.rotate(Vector(),Vector(1,0,0),angle);pin.translate(Vector(root,0,0))
        add(doc,f'ClawPin_{index}',pin,'slider','Steel M3 shoulder screw',False,'Metal joint pin, washers and locknut')
        for suffix,y in [('L',-6)]:
            spacer=cylinder(3,2,(0,y,40)).cut(cylinder(1.6,2,(0,y,40)))
            spacer.rotate(Vector(),Vector(1,0,0),angle);spacer.translate(Vector(root,0,0))
            add(doc,f'ClawSpacer_{index}_{suffix}',spacer,'slider','Acetal thrust spacer, 2mm nominal',False,
                'Select shim stack for 0.1–0.2mm total measured end play; smooth pin grip must span both ears')
        def place(local):
            local.rotate(Vector(),Vector(1,0,0),angle)
            local.translate(Vector(root,0,0))
            return local
        theta=math.radians(open_angle_deg)
        hx,hz=-12*math.sin(theta),40+12*math.cos(theta)
        # Smooth M2 pin through horn and sector; eye-side washers carry tendon.
        eye_pin=stop_eye_pin_shape(open_angle_deg)
        add(doc,f'ClawStopEyePin_{index}',place(eye_pin),'slider','Steel smooth M2 pin with retained ends',False,
            'Smooth shank spans horn and stop slot;1mm transverse tendon eye outside finger; purchased/prepared pin and retained ends; no thread rubbing')
        # Right-side spring coil and washers replace the former solid 2mm spacer.
        coil=spring_shape(open_angle_deg)
        add(doc,f'ClawSpringCoil_{index}',place(coil),'slider','Spring steel torsion spring allowance',False,
            '0.5mm wire, 4.7mm mean diameter, 2 turns allowance; formed legs seated in separate finger and ear holes; spring rate/preload and bend radii require supplier qualification')
        for j,y in enumerate((4.0,5.8)):
            washer=cylinder(3.0,0.2,(0,y,40)).cut(cylinder(1.6,0.2,(0,y,40)))
            add(doc,f'ClawSpringWasher_{index}_{j}',place(washer),'slider','Steel or acetal thrust washer 0.2mm',False,
                'Spring axial pocket 1.6mm; select shim stack after measured pin and printed ear fit')
        # Straight working tendon span: it leaves the rotating horn on its left
        # side and enters a fixed guide aft of the palm, above the pivot boss.
        a=Vector(hx,-4.5,hz);b=Vector(-25,-4.5,52)
        delta=b-a
        tendon=Part.makeCylinder(0.35,delta.Length,a,delta.normalize())
        add(doc,f'ClawWorkingTendon_{index}',place(tendon),'slider','0.7mm low-stretch braided line allowance',False,
            'Working span only; PTFE-lined Bowden return routing and servo horn termination need measured actuator interface')
    # Packaging only; actual SKU and common cable pull interface not yet released.
    servo=Part.makeBox(24,13,29,Vector(root-65,32,-14.5))
    add(doc,'GripperServoEnvelope',servo,'envelope','Candidate12–20g actuator; model/SKU unselected',False,
        'Sole actuator; opens3 spring-closing claws. Envelope not a mounting drawing.')
    return root
