"""Compact V1 two-finger bench claw. mm; flat printable parts, no nets.
This is a fit-test design, not a released actuator interface. See assembly notes.
"""
import math
import FreeCAD
import Part
from FreeCAD import Vector

PIVOT=22.0
ROD_LENGTH=math.hypot(22,8)

def cyl(r,h,x,y,z=0):
    return Part.makeCylinder(r,h,Vector(x,y,z))

def capsule(a,b,r,h):
    x,y=a; u,v=b
    d=math.hypot(u-x,v-y)
    if d<1e-9:return cyl(r,h,x,y)
    nx=-(v-y)/d*r; ny=(u-x)/d*r
    vs=[Vector(x+nx,y+ny,0),Vector(u+nx,v+ny,0),Vector(u-nx,v-ny,0),Vector(x-nx,y-ny,0)]
    return Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(Vector(0,0,h)).fuse(cyl(r,h,x,y)).fuse(cyl(r,h,u,v)).removeSplitter()

def hole(sh,x,y,d=3.4,h=40):return sh.cut(cyl(d/2,h,x,y,-1))

def palm():
    sh=Part.makeBox(70,54,5,Vector(-35,-40,0))
    # Generous output/body opening: adjustable carrier sets final shaft centre.
    sh=sh.cut(Part.makeBox(38,18,7,Vector(-29,-31,-1)))
    for x in [-22,22]:sh=hole(sh,x,0)
    for x in [-10,10]:
        for y in [0,10]:sh=hole(sh,x,y)
    for x in [-27,7]:
        for y in [-35,-9]:
            slot=capsule((x-5,y),(x+5,y),1.7,7); slot.translate(Vector(0,0,-1)); sh=sh.cut(slot)
    return sh.removeSplitter()

def finger(side):
    # Side=-1 is left; inward tip offset is opposite to side.
    sh=capsule((0,-12),(0,0),5,6)
    sh=sh.fuse(capsule((0,0),(-side*2,30),4,6))
    sh=sh.fuse(capsule((-side*2,30),(-side*8,44),5,6))
    for x,y in [(0,0),(0,-12)]:sh=hole(sh,x,y)
    # Two through-holes for foam-pad tie/string retention; no TPU spool required.
    for y in [34,41]:sh=hole(sh,-side*(2+(y-30)*6/14),y,2.2)
    return sh.removeSplitter()

def rod():
    sh=capsule((0,0),(ROD_LENGTH,0),3.5,3)
    return hole(hole(sh,0,0),ROD_LENGTH,0).removeSplitter()

def spacer(h):return cyl(3.5,h,0,0).cut(cyl(1.7,h+2,0,0,-1))

def crank():
    # Printed plate bolts to bought plastic horn; never prints a servo spline.
    sh=capsule((0,0),(12,0),5,3)
    sh=hole(sh,0,0,6.8)
    sh=hole(sh,12,0,3.4)
    for y in [-2.5,2.5]:
        slot=capsule((5.5,y),(7.5,y),1.1,5);slot.translate(Vector(0,0,-1));sh=sh.cut(slot)
    return sh.removeSplitter()

def carrier():
    # Body insert from below; raised rails carry original servo flange.
    sh=Part.makeBox(44,34,3,Vector(-22,-17,0))
    sh=sh.cut(Part.makeBox(24,14,5,Vector(-12,-7,-1)))
    for x in [-17,17]:
        for y in [-13,13]:sh=hole(sh,x,y)
    # M2.5 mounting flange slots allow 27-33 mm centre spacing.
    for sign in [-1,1]:
        slot=capsule((sign*13.5,0),(sign*16.5,0),1.45,5);slot.translate(Vector(0,0,-1));sh=sh.cut(slot)
    return sh.removeSplitter()

def parts():
    def spec(shape,qty,hardware,note):
        # Normalize only Z; parts can have negative XY coordinates in STL.
        shape=shape.copy();shape.translate(Vector(0,0,-shape.BoundBox.ZMin))
        return dict(shape=shape,qty=qty,material='PETG',orientation='As exported: broad flat face on bed, Z up; 0.20 mm layers, 5 perimeters, 30% gyroid, 5 top/bottom layers.',hardware=hardware,note=note)
    return {
      'V1_Claw_Palm':spec(palm(),1,'4 M3 interface bolts; 2 M3 finger pivots; 4 M3 servo carrier fasteners','Four mounting holes: X=+/-10, Y=0 and 10 mm; 5 mm palm thickness. Servo carrier slides along X to align shaft; measure output height before powered assembly.'),
      'V1_Claw_Finger_Left':spec(finger(-1),1,'M3 pivot and pushrod bolts, washer, locknut; foam pad','Flat XY print. Left at X=-22. Foam-pad thickness establishes final grip.'),
      'V1_Claw_Finger_Right':spec(finger(1),1,'M3 pivot and pushrod bolts, washer, locknut; foam pad','Flat XY print. Right at X=22.'),
      'V1_Claw_Pushrod':spec(rod(),2,'M3 pivot screws, washers, locknuts','23.4094 mm hole-centre distance; rods stacked in separate Z planes.'),
      'V1_Claw_Crank_Adapter':spec(crank(),1,'Bought MG90S horn; 2 M2 bolts; M3 common rod pin','FIT TEST ONLY: attach to supplied horn through slots; measure/drill horn if required. Do not rely on centre screw friction to transmit torque.'),
      'V1_Claw_Servo_Carrier':spec(carrier(),1,'2 M2.5 flange bolts/nuts; 4 M3 carrier fasteners','FIT TEST ONLY: 24x14 mm body window, 27-33 mm flange-hole spacing; Carrier centre nominal (-10,-22), adjustable +/-5 mm X; measure actual output height.'),
      'V1_Claw_Spacer_1mm':spec(spacer(1),5,'M3 smooth shank','Flat print; measure thickness; washer may replace.'),
      'V1_Claw_Spacer_2mm':spec(spacer(2),1,'M3 smooth shank','Left finger-to-rod separation.'),
      'V1_Claw_Spacer_6mm':spec(spacer(6),1,'M3 smooth shank','Right finger-to-rod separation.'),
    }

def linkage(servo_deg=0):
    """Actual single-crank/two-rod geometry. Return continuous near-zero roots."""
    if not -25 <= servo_deg <= 25:raise ValueError('Bench motion range only: +/-25 degrees')
    a=math.radians(servo_deg)
    # 12 mm horn from centre (-12,-20). Neutral common pin=(0,-20).
    pin=(-12+12*math.cos(a),-20+12*math.sin(a))
    result={}
    for side in [-1,1]:
        def f(t):
            x=side*PIVOT+12*math.sin(t);y=-12*math.cos(t)
            return (x-pin[0])**2+(y-pin[1])**2-ROD_LENGTH**2
        roots=[];prev=-math.pi/4;fp=f(prev)
        for k in range(1,901):
            nxt=-math.pi/4+k*math.pi/1800;fn=f(nxt)
            if fp*fn<=0:
                lo,hi=prev,nxt
                for _ in range(45):
                    mid=(lo+hi)/2
                    if f(lo)*f(mid)<=0:hi=mid
                    else:lo=mid
                roots.append((lo+hi)/2)
            prev,fp=nxt,fn
        if not roots:raise ValueError('Linkage cannot assemble at requested angle')
        t=min(roots,key=abs)
        result[side]={'angle_deg':math.degrees(t),'pin':(side*PIVOT+12*math.sin(t),-12*math.cos(t))}
    return {'common_pin':pin,'fingers':result}

def assembly(servo_deg=0):
    """Located printed motion parts; carrier location remains measured fit gate."""
    geom=linkage(servo_deg); out={'Palm':palm()}
    sh=crank();sh.rotate(Vector(),Vector(0,0,1),servo_deg);sh.translate(Vector(-12,-20,10));out['Crank']=sh
    for side,label,z in [(-1,'Left',14),(1,'Right',18)]:
        d=geom['fingers'][side]
        sh=finger(side);sh.rotate(Vector(),Vector(0,0,1),d['angle_deg']);sh.translate(Vector(side*22,0,6));out['Finger_'+label]=sh
        pin=geom['common_pin'];target=d['pin'];angle=math.degrees(math.atan2(target[1]-pin[1],target[0]-pin[0]))
        sh=rod();sh.rotate(Vector(),Vector(0,0,1),angle);sh.translate(Vector(pin[0],pin[1],z));out['Rod_'+label]=sh
    return out
