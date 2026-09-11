"""Compact print-first V1 frame/drive development parts. Millimetres; not released.

Each part is a connected, z-up printable solid. Shaft D-flats must be filed to the
coupon, not assumed present on generic round stock. Involute gears replace belts
on yaw/pitch for this low-speed development set; BOM must follow this revision.
"""
import math
import FreeCAD as App
import Part
from FreeCAD import Vector as V

MODULE=1.2

def box(x,y,z,p=(0,0,0)): return Part.makeBox(x,y,z,V(*p))
def cyl(r,h,p=(0,0,0),axis=(0,0,1)): return Part.makeCylinder(r,h,V(*p),V(*axis))
def hole(s,x,y,d,h=100,z=-1): return s.cut(cyl(d/2,h,(x,y,z)))
def d_bore(d,h,z=-1):
    return cyl(d/2,h,(0,0,z)).common(box(d,d,h,(-d/2,-d/2,z)).cut(box(d,d,h,(d/2-.8,-d/2,z))))
def polygon(points,h):
    p=[V(x,y,0) for x,y in points]
    return Part.Face(Part.makePolygon(p+[p[0]])).extrude(V(0,0,h))
def gear(teeth,bore,width=10):
    rp=MODULE*teeth/2;rb=rp*math.cos(math.radians(20))
    rr=rp-1.25*MODULE;ra=rp+MODULE
    def inv(r):
        t=math.sqrt(max(0,(r/rb)**2-1));return t-math.atan(t)
    half=math.pi/(2*teeth)-0.12/(2*rp);start=max(rr,rb);pts=[]
    for k in range(teeth):
        c=k*2*math.pi/teeth
        flank=half+inv(rp)-inv(start)
        pts.append((rr*math.cos(c-flank),rr*math.sin(c-flank)))
        for i in range(9):
            r=start+(ra-start)*i/8;a=c-half-inv(rp)+inv(r)
            pts.append((r*math.cos(a),r*math.sin(a)))
        for i in range(8,-1,-1):
            r=start+(ra-start)*i/8;a=c+half+inv(rp)-inv(r)
            pts.append((r*math.cos(a),r*math.sin(a)))
        pts.append((rr*math.cos(c+flank),rr*math.sin(c+flank)))
        # Root arc across the next tooth gap; removes polygonal root shortcut.
        end=(k+1)*2*math.pi/teeth-flank
        for j in range(1,4):
            a=c+flank+(end-c-flank)*j/4
            pts.append((rr*math.cos(a),rr*math.sin(a)))
    sh=polygon(pts,width)
    hubr=9 if bore<6 else 12
    sh=sh.fuse(cyl(hubr,width+10))
    if teeth>=80:
        for a in range(0,360,60):
            r=(rr+hubr)/2;rad=max(3,min((rr-hubr)/2-5,r*.40))
            sh=hole(sh,r*math.cos(math.radians(a)),r*math.sin(math.radians(a)),2*rad)
    sh=sh.cut(d_bore(bore,40))
    # Split upper hub: tangential clamp bolt clears shaft, so motor shaft
    # needs no cross-drilling. D bore carries torque; clamp provides retention.
    sh=sh.cut(box(hubr+1,1.2,10.2,(0,-.6,width)))
    bolt_x=5.8 if bore<6 else 8.0
    sh=sh.cut(cyl(1.7,2*hubr+2,(bolt_x,-hubr-1,width+5),(0,1,0)))
    return sh.removeSplitter()

def plate(w,h,t,holes=()):
    s=box(w,h,t,(-w/2,-h/2,0))
    for x,y,d in holes:s=hole(s,x,y,d)
    return s

def bearing_cap():
    s=plate(40,40,4,[(0,0,9),(15,15,3.4),(-15,15,3.4),(15,-15,3.4),(-15,-15,3.4)])
    return s

def bearing_plate(w,h,t):
    s=plate(w,h,t,[(0,0,8.6)])
    s=s.cut(cyl(11.15,7.1,(0,0,t-7.1)))
    for x in(-15,15):
        for y in(-15,15):s=hole(s,x,y,3.4)
    return s

def cheek(outboard=False):
    # Print flat. Local y is assembly height above turret; normal points outboard.
    s=box(170,215,10,(-135,0,0))
    # Broad boxed-frame window leaves20mm/25mm webs and motor-support crossbar.
    s=s.cut(box(70,90,12,(-80,25,-1)))
    for x,y in [(0,190),(-108,190)]:
        s=hole(s,x,y,8.6)
        s=s.cut(cyl(11.15,7.1,(x,y,2.9)))
        for dx,dy in [(15,0),(-15,0),(0,-15)]:s=hole(s,x+dx,y+dy,3.4)
    if outboard:
        s=hole(s,-108,130,22.5)
        for dx in(-15.5,15.5):
            for dy in(-15.5,15.5):s=hole(s,-108+dx,130+dy,3.4)
    for x in(-108,20):
        for y in(18,35):s=hole(s,x,y,4.5)
    for x,y in[(-127,170),(20,170),(-127,100),(20,100)]:s=hole(s,x,y,4.5)
    return s.removeSplitter()

def foot():
    # Right-angle shoe, printed on its triangular side for supported orientation.
    s=polygon([(0,0),(45,0),(45,8),(8,8),(8,45),(0,45)],25)
    gusset=polygon([(8,8),(45,8),(8,45)],5)
    s=s.fuse(gusset)
    other=gusset.copy();other.translate(V(0,0,20));s=s.fuse(other)
    for x in(18,35):s=s.cut(cyl(2.25,12,(x,-1,12.5),(0,1,0)))
    for y in(18,35):s=s.cut(cyl(2.25,12,(-1,y,12.5),(1,0,0)))
    return s

def motor_plate():
    s=plate(64,64,6,[(0,0,22.5)])
    for x in(-15.5,15.5):
        for y in(-15.5,15.5):s=hole(s,x,y,3.4)
    for x in(-25,25):
        for y in(-25,25):s=hole(s,x,y,4.5)
    return s

def spacer(length):
    return hole(plate(16,16,length),0,0,4.5)

def saddle_half():
    # Bottom half atprintZ0; assembled rail length240, bridges two clamping stations.
    s=box(240,58,6,(-120,-29,0))
    # Side rails + tube-facing seats.42.5mm clearance accepts actual42mm outer tube.
    for y in(-29,21.25):s=s.fuse(box(240,7.75,26,(-120,y,0)))
    for x in(-110,110):
        s=s.fuse(box(20,74,6,(x-10,-37,0)))
        for y in(-32,32):s=hole(s,x,y,4.5)
    # Independent8mm stubshaft sockets do notcross telescope bore.
    for sign in(-1,1):
        y=sign*29
        s=s.fuse(cyl(15,17,(0,y,22),(0,sign,0)))
        s=s.cut(cyl(4.15,19,(0,sign*27,22),(0,sign,0)))
        s=s.cut(cyl(1.7,32,(-16,sign*37,22),(1,0,0)))
        s=s.cut(box(3.5,6,6,(-15.1,sign*37-3,19)))
    return s.removeSplitter()

def saddle_cap():
    s=box(20,74,8,(-10,-37,0))
    s=s.fuse(box(20,58,6,(-10,-29,0)))
    for y in(-32,32):s=hole(s,0,y,4.5)
    return s

def saddle_rail():
    # Print in X/Z load plane; thickness isassemblyY. No240mm bridging.
    s=box(240,58,12,(-120,-29,0))
    for x in(-95,20):s=s.cut(box(75,38,14,(x,-19,-1)))
    s=s.fuse(cyl(15,12))
    s=s.cut(d_bore(8.3,9.2,3))
    for x in(-110,110):s=s.cut(cyl(2.25,60,(x,-30,6),(0,1,0)))
    s=s.cut(cyl(1.7,32,(-16,0,7.5),(1,0,0)))
    s=s.cut(box(3.5,6,6,(-15.1,-3,4.5)))
    return s.removeSplitter()

def saddle_crossbar():
    s=plate(20,86,8,[(0,-37,4.5),(0,37,4.5)])
    return s

def cheek_cap():
    s=cyl(20,4)
    for x,y,d in[(0,0,9),(15,0,3.4),(-15,0,3.4),(0,-15,3.4)]:s=hole(s,x,y,d)
    return s

def collar(d):
    s=cyl(10,10).cut(cyl(d/2,12,(0,0,-1)))
    s=s.cut(box(12,1.2,12,(0,-.6,-1)))
    s=s.cut(cyl(1.7,22,(5,-11,5),(0,1,0)))
    return s

def coupon():
    # Six annular cups joined by a low web. Cut pockets AFTER fusing the web
    # so the web cannot obstruct the bearing seats or through bores.
    diameters=[21.9,22.0,22.1,22.2,22.3,22.4]
    s=box(145,5,2,(-72.5,-2.5,0))
    for i,d in enumerate(diameters):
        s=s.fuse(cyl(13.5,8,(-70+i*28,0,0)))
    for i,d in enumerate(diameters):
        x=-70+i*28
        s=s.cut(cyl(d/2,7.1,(x,0,.9)))
        s=hole(s,x,0,8.6)
    return s.cut(box(3,3,3,(-83.5,-1.5,-.1))).removeSplitter()

def parts():
    p={}
    def add(n,s,q,hardware,note):
        p[n]=dict(shape=s.removeSplitter(),qty=q,material='PETG',orientation='As exported; flat face on bed',hardware=hardware,note=note)
    base=bearing_plate(180,160,8)
    for x in(-70,70):
        for y in(-60,60):base=hole(base,x,y,4.5)
    for x in(35,85):
        for y in(-25,25):base=hole(base,x,y,4.5)
    add('V1_Base',base,1,'608 bearing; M4 bolts; two steel bench clamps','Bottom shaft end must not protrude below base')
    top=bearing_plate(180,160,10)
    for x in(-70,70):
        for y in(-60,60):top=hole(top,x,y,4.5)
    add('V1_YawUpperDeck',top,1,'608 bearing and throughbolts','Bearing pocket opens upward; see assembly height stack')
    add('V1_DeckSpacer76',spacer(76),4,'M4x100 throughbolts washers locknuts','Print upright with brim; no plastic threads')
    add('V1_YawMotorPlate',motor_plate(),1,'4M3 motor screws;4M4 throughbolts','NEMA17 pilot22.5;31mm bolt square')
    add('V1_MotorSpacer45',spacer(45),4,'M4x65 throughbolts','Motorface53mm abovebench; gear face63mm')
    turret=plate(240,210,10)
    turret=turret.fuse(cyl(15,22)).cut(d_bore(8.15,30))
    for x in(-108,20):
        for y in(-97,-80,80,97):turret=hole(turret,x,y,4.5)
    add('V1_Turret',turret,1,'8mm filedDshaft; M4 feet','Cheeks innerfacesY+/-52; feet contactouterfacesY+/-62; footbaseholesY+/-80,+/-97')
    add('V1_YokeCheek',cheek(),2,'608 bearings M3 caps M4 feet','One each side; outboard gear support is separate')
    add('V1_OutboardGearPlate',cheek(True),1,'608 bearing NEMA17 motor M4 spacers','Onlyleftside;50mm outboard of inner cheek')
    add('V1_GearPlateSpacer40',spacer(40),4,'M4x70','Two10mmplates plus40mmclearspan')
    add('V1_YokeFoot',foot(),4,'M4 bolts washers locknuts','Organic supports foruppergusset; sideaccessnutpockets; matchingholesX-108,+20 height18,35')
    add('V1_BearingCap608',bearing_cap(),2,'M3 screws washers','Fourholedeckcap; pocketcoupon first')
    add('V1_CheekBearingCap608',cheek_cap(),4,'M3 screws washers','Threeholecapsmatchcheeks')
    for n,t,d,q in [('V1_Pinion20_5mm',20,5.15,2),('V1_Pinion20_8mm',20,8.15,1),('V1_Gear80_8mm',80,8.15,2),('V1_Gear160_8mm',160,8.15,1)]:
        add(n,gear(t,d),q,'M3x25 (5mm hub) or M3x30 (8mm hub) tangential clamp bolt, nut; filed D-shaft','Module1.2 pressureangle20; pitchdrive32:1 yaw4:1; 0.12mm tooth-thickness relief per gear (0.24mm pair); mesh/backlash test before powered use')
    add('V1_SaddleRail',saddle_rail(),2,'Independent8mmstubs;4M4x80clampbolts;M3retainingbolts','240mmlengthfitsCOREOne250X; railsinnerfaceY+/-31 clears60mmflanges; pocketmustberetainedwithpin')
    add('V1_SaddleCrossbar',saddle_crossbar(),4,'M4x80 throughbolts washers locknuts','LocatedatX+/-110; twoaboveandtwobelowtube;0.5mmprintedfitshimsrequired')
    add('V1_Collar8',collar(8.15),6,'M3x25 throughboltandnut','Frictionretention must be backed by ends/keys where gravityloaded')
    add('V1_608FitCoupon',coupon(),1,'One actual608 bearing','PRINT FIRST. Six pockets left to right 21.9/22.0/22.1/22.2/22.3/22.4mm; notched end is21.9; no powereduse')
    return p

if __name__=='__main__':
    for n,spec in parts().items():
        sh=spec['shape'];assert sh.isValid() and len(sh.Solids)==1,(n,sh.isValid(),len(sh.Solids))
        print(n,spec['qty'],round(sh.Volume,2),sh.BoundBox)
