"""Compact low-energy V1 telescope. mm; prototype fit qualification required.
All exports are individually connected solids, upright or open face on bed.
No fair-version CAD is altered. Root assembly uses x-axis for boom length.
"""
import math
import Part
from FreeCAD import Vector
OUTER=42.; BORE=34.8; INNER=30.; INNER_BORE=23.6
OUTER_LENGTH=380.; INNER_LENGTH=400.; STROKE=200.

def box(a,b,c,p): return Part.makeBox(a,b,c,Vector(*p))
def cyl(r,h,p,axis=(0,0,1)): return Part.makeCylinder(r,h,Vector(*p),Vector(*axis))
def square_tube(width,bore,length): return box(width,width,length,(-width/2,-width/2,0)).cut(box(bore,bore,length+2,(-bore/2,-bore/2,-1)))
def hex_prism(af,length,origin,axis='x'):
    r=af/math.sqrt(3)
    pts=[Vector(0,r*math.cos(math.pi*i/3),r*math.sin(math.pi*i/3)) for i in range(6)]
    sh=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(Vector(length,0,0))
    if axis=='y': sh.rotate(Vector(),Vector(0,0,1),90)
    sh.translate(Vector(*origin)); return sh

def outer_segment(index):
    L=OUTER_LENGTH/3
    sh=square_tube(OUTER,BORE,L)
    wires=[]
    for w,z in ((42,L-17),(60,L-8)):
        vertices=[Vector(-w/2,-w/2,z),Vector(w/2,-w/2,z),Vector(w/2,w/2,z),Vector(-w/2,w/2,z)]
        wires.append(Part.makePolygon(vertices+[vertices[0]]))
    ramp=Part.makeLoft(wires,True).cut(box(BORE,BORE,20,(-BORE/2,-BORE/2,L-18)))
    sh=sh.fuse(ramp)
    for z in (0,L-8):
        flange=box(60,60,8,(-30,-30,z)).cut(box(BORE,BORE,10,(-BORE/2,-BORE/2,z-1)))
        sh=sh.fuse(flange)
        for x in (-25,25):
            for y in (-25,25): sh=sh.cut(cyl(1.7,10,(x,y,z-1)))
    if index==2:
        # Captive rear guide shoulder, 18 mm behind the mouth. Cap is separate.
        sh=sh.fuse(box(34.8,34.8,2,(-17.4,-17.4,L-20)).cut(box(30.8,30.8,4,(-15.4,-15.4,L-21))))
        for x in (-18,18):
            for y in (-18,18): sh=sh.cut(cyl(1.25,14,(x,y,L-13)))
        # Radial M3 adjustment screws in external hex nut pockets.
        for angle in (0,90,180,270):
            hole=cyl(1.7,18,(14,0,L-10),(1,0,0))
            nut=hex_prism(5.7,3,(26.5,0,L-10))
            hole.rotate(Vector(),Vector(0,0,1),angle); nut.rotate(Vector(),Vector(0,0,1),angle)
            sh=sh.cut(hole).cut(nut)
    return sh.removeSplitter()

def inner_segment(index):
    L=INNER_LENGTH/3
    sh=square_tube(INNER,INNER_BORE,L)
    if index<2:
        # Bonded internal spigot, OD23.2 into ID23.6: 0.2 mm radial glue gap.
        sp=box(23.2,23.2,34,(-11.6,-11.6,L-4)).fuse(box(30,30,4,(-15,-15,L-4))).cut(cyl(5,36,(0,0,L-5)))
        # Each M3 nut enters from the central axial access bore before joining.
        for z,rot in ((L+10,0),(L+22,90)):
            hole=cyl(1.7,14,(0,0,z),(1,0,0))
            nut=hex_prism(5.7,7,(1.6,0,z))
            hole.rotate(Vector(),Vector(0,0,1),rot); nut.rotate(Vector(),Vector(0,0,1),rot)
            sp=sp.cut(hole).cut(nut)
        sh=sh.fuse(sp)
    if index>0:
        for z,rot in ((10,0),(22,90)):
            hole=cyl(1.7,5,(11,0,z),(1,0,0))
            # 90 degree flat-head screw, max6.2 mm head OD; must sit flush.
            cs=Part.makeCone(1.7,3.2,1.5,Vector(13.5,0,z),Vector(1,0,0))
            hole.rotate(Vector(),Vector(0,0,1),rot); cs.rotate(Vector(),Vector(0,0,1),rot)
            sh=sh.cut(hole).cut(cs)
    return sh.removeSplitter()

def joint_coupon(male):
    # Crop exact mating ends from production shapes, retaining actual nut access.
    if male:
        sh=inner_segment(0).common(box(40,40,50,(-20,-20,INNER_LENGTH/3-20)))
    else:
        sh=inner_segment(1).common(box(40,40,40,(-20,-20,0)))
    sh.translate(Vector(0,0,-sh.BoundBox.ZMin))
    return sh.removeSplitter()

def front_cap():
    sh=box(42,42,4,(-21,-21,0)).cut(box(30.8,30.8,6,(-15.4,-15.4,-1)))
    for x in (-18,18):
        for y in (-18,18):sh=sh.cut(cyl(1.7,6,(x,y,-1)))
    return sh

def guide_pad():
    # Flat on contact face, 0.13mm nominal bonded PTFE; outer screw dimple.
    sh=box(16,18,1.6,(0,0,0))
    return sh.cut(cyl(1.8,.5,(8,9,1.2)))

def rear_shoe_half():
    # Two channel halves screw together; longitudinal split prints open upward.
    sh=box(16,34.2,3.5,(0,-17.1,0))
    for y in (-17.1,15):sh=sh.fuse(box(16,2.1,13.6,(0,y,3.5)))
    # Counterbored flush M2 heads, mating nuts captured in other half.
    for x in (4,12):
        for y in (-16.05,16.05): sh=sh.cut(cyl(.85,18,(x,y,-.2)))
    return sh.removeSplitter()

def tether_cap(width,bore):
    sh=box(width,width,5,(-width/2,-width/2,0)).fuse(box(bore-.4,bore-.4,10,(-(bore-.4)/2,-(bore-.4)/2,4)))
    sh=sh.cut(cyl(2,16,(0,0,-1)))
    # Cord passes two bores and around an 8 mm printed bridge; knot outside.
    sh=sh.cut(cyl(2,16,(8,0,-1)))
    return sh.removeSplitter()

def parts():
    d={}
    def add(name,shape,qty,note,hardware='',orientation='As exported, z=0; no model scaling'):
        shape=shape.removeSplitter()
        d[name]={'shape':shape,'qty':qty,'material':'PETG','orientation':orientation,'hardware':hardware,'note':note}
    for i in range(3): add('Telescope_Outer_%d'%(i+1),outer_segment(i),1,'Vertical; 6 perimeters, 25% gyroid, 0.20 mm layers, 8 mm brim. Upper flange has45-degree underside ramps; supports off. Drill horizontal adjustment bores after print.', 'M3x20 flange bolts, M3 washers/nuts; front M3x8 cap screws and M3x16 adjusters')
    for i in range(3):add('Telescope_Inner_%d'%(i+1),inner_segment(i),1,'Vertical; 6 perimeters, 30% gyroid. Bond spigots with plastic-compatible epoxy after coupon; 4 flush M3x12 countersunk screws total. Sand seam flush. No high-speed rating.','M3x12 DIN965 screws and M3 DIN934 nuts, epoxy')
    add('Telescope_Front_Guide_Cap',front_cap(),1,'Flat; 6 walls, 40% infill; 4x M3x8 self-tap into2.5 pilot; repeated removal needs inserts redesign.')
    add('Telescope_Front_Guide_Pad',guide_pad(),4,'Flat; solid thin pad; 0.13 mm PTFE tape including adhesive nominal. Measure actual tape; adjust until free running without shake.')
    add('Telescope_Rear_Guide_Ring',square_tube(34.14,30.3,16),1,'Vertical; 6 walls; bond to rear16 mm of slider, apply measured0.13 mm PTFE tape to four outer faces. Finished OD34.4 leaves0.4 mm total nominal bore clearance. Rear cap traps ring axially against bonded tube surface.')
    add('Telescope_Rear_Tether_Cap',tether_cap(42,34.8),1,'Cap fit coupon first; bonded retention; redundant external tether required for powered trials.','Low-stretch 2 mm cord, through two bores; knots outside')
    add('Telescope_Inner_Rear_Cap',tether_cap(30,23.6),1,'Fit at inner rear, bonded; cap outer30 leaves guide travel clear.','Low-stretch 2 mm cord')
    add('Telescope_Outer_Fit_Coupon',square_tube(42,34.8,20),1,'PRINT FIRST: fit gauge, not assembly')
    add('Telescope_Inner_Fit_Coupon',square_tube(30,23.6,20),1,'PRINT FIRST: fit gauge, not assembly')
    add('Telescope_Joint_Male_Fit_Coupon',joint_coupon(True),1,'PRINT FIRST: exact30mm spigot and nut pockets, cropped to20mm tube; coupon only.')
    add('Telescope_Joint_Female_Fit_Coupon',joint_coupon(False),1,'PRINT FIRST: exact receiving joint cropped to40mm; check M3x12 screws sit flush and nuts can be inserted before bonding.')
    return d
