"""Nominal removable wear shoes and metal retention hardware, millimetres.

Front shoes screw outwards through the outer tube to external nuts. Opposing
fasteners are staggered; service holes admit a long1.5mm hex key with slider out.
Rear shoes screw inward through the inner tube to nuts reached from its open tail.
This is a dimensional prototype, not a fastener or wear-life qualification.
"""
import math
import Part
from FreeCAD import Vector


def cyl(d,h,p,axis=(0,0,1)):
    return Part.makeCylinder(d/2,h,Vector(*p),Vector(*axis))


def nut(x,y,z):
    radius=4/math.sqrt(3)
    points=[Vector(x+radius*math.cos(math.radians(a)),y+radius*math.sin(math.radians(a)),z)
            for a in range(0,360,60)]
    return Part.Face(Part.makePolygon(points+[points[0]])).extrude(Vector(0,0,1.6)).cut(cyl(2.05,1.6,(x,y,z)))


def stations():
    # Top/bottom strips flank the9mm belt with0.5mm nominal lateral clearance.
    # Measured stock corner radii and nut clearance must be checked before drilling.
    for angle in (0,180,90,270):
        for tangent in ((-8,8) if angle in (0,180) else (0,)):
            yield angle,tangent,6 if angle in (0,180) else 18


def transformed(shape,angle,xc):
    shape.rotate(Vector(),Vector(1,0,0),angle)
    shape.translate(Vector(xc,0,0))
    return shape


def drill_tube(shape,outer,inner,wall,xc,rear=False):
    for angle,tangent,_ in stations():
        xs=(-8,8) if rear or angle in (0,90) else (-4,4)
        if not rear:xs=(-8,-4,4,8)  # also opposing-key service holes
        for x in xs:
            tool=cyl(2.4,12,(x,tangent,inner/2-4))
            shape=shape.cut(transformed(tool,angle,xc))
    return shape.removeSplitter()


def add_guides(doc,add,outer,outer_wall,inner,inner_wall,front,rear):
    for region,xc,is_rear in [('Front',front,False),('Rear',rear,True)]:
        r0=inner/2+(0 if is_rear else .1)
        r1=outer/2-outer_wall-(.1 if is_rear else 0)
        for angle,tangent,width in stations():
            xs=(-8,8) if is_rear or angle in (0,90) else (-4,4)
            sh=Part.makeBox(30,width,r1-r0,Vector(-15,tangent-width/2,r0))
            for x in xs:
                sh=sh.cut(cyl(2.4,8,(x,tangent,r0-1)))
                if is_rear:sh=sh.cut(cyl(4.2,2.5,(x,tangent,r1-2.5)))
                else:sh=sh.cut(cyl(4.2,2.5,(x,tangent,r0)))
            if not is_rear:
                for x in ((-4,4) if angle in (0,90) else (-8,8)):
                    sh=sh.cut(cyl(2.4,8,(x,tangent,r0-1)))
            name=f'{region}Shoe_{angle}_{tangent}'
            add(doc,name,transformed(sh,angle,xc),'wear','Machined acetal strip',False,
                'Two recessed M2x8 socket screws; front staggered key access; rear nuts installed before slider insertion')
            for i,x in enumerate(xs):
                if is_rear:
                    base=r1-2.5
                    screw=cyl(2,8,(x,tangent,base),(0,0,-1)).fuse(cyl(3.8,2,(x,tangent,base)))
                    wz=inner/2-inner_wall-.3
                    nz=wz-1.6
                else:
                    base=r0+2.5
                    screw=cyl(2,8,(x,tangent,base)).fuse(cyl(3.8,2,(x,tangent,base-2)))
                    wz=outer/2
                    nz=wz+.3
                washer=cyl(4,.3,(x,tangent,wz)).cut(cyl(2.2,.3,(x,tangent,wz)))
                for suffix,hardware in [('Screw',screw),('Washer',washer),('Nut',nut(x,tangent,nz))]:
                    add(doc,f'{name}_{suffix}_{i}',transformed(hardware,angle,xc),
                        'slider' if is_rear else 'fixed','Steel purchased M2 hardware',False,
                        'Nominal smooth envelope; verify actual head and nut dimensions, tool access, preload and loosening')
