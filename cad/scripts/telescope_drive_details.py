"""Rear open-belt anchor and captured mechanical stops, nominal millimetres.
Bench-prototype detail only: purchased pin ratings, clamp proof and tube fits
remain physical qualification requirements; no motor or stop-energy approval.
"""
import math
import Part
from FreeCAD import Vector


def box(a,b,c,p):return Part.makeBox(a,b,c,Vector(*p))
def cyl(d,h,p,axis=(0,0,1)):return Part.makeCylinder(d/2,h,Vector(*p),Vector(*axis))
def hexnut(d,af,h,p):
    x,y,z=p;r=af/math.sqrt(3)
    pts=[Vector(x+r*math.cos(math.radians(a)),y+r*math.sin(math.radians(a)),z) for a in range(0,360,60)]
    return Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(Vector(0,0,h)).cut(cyl(d+.1,h,p))
def oriented_y(shape):
    shape.rotate(Vector(),Vector(1,0,0),-90)
    return shape


def drill_outer(sh):
    for x in (-233.5,287):
        for sign in (-1,1):
            sh=sh.cut(cyl(5.1,12,(x,sign*14,12),(0,sign,0)))
    return sh


def drill_inner(sh,tail):
    for x in (tail+8,tail+18):sh=sh.cut(cyl(3.4,7,(x,0,-16)))
    return sh


def belt_shapes(left,right,tail,belt_z):
    # One open belt, two end envelopes meeting with0.6mm gap under common cap.
    seam=tail-15
    shapes=[]
    for lo,hi in ((left,seam-.3),(seam+.3,right)):
        sh=box(hi-lo,9,1.38,(lo,-4.5,belt_z-.69))
        # Locally compressed backing. Actual compatible tooth profile is a gate.
        sh=sh.cut(box(26,9,1,(tail-26,-4.5,belt_z+.51)))
        shapes.append(sh)
    return shapes


def add_details(doc,add,tail):
    created=[]
    def put(name,shape,group,material,printed=False,role=''):
        obj=add(doc,name,shape,group,material,printed,role)
        created.append(obj)
        return obj
    # Close-fit inner plug with open longitudinal nut clearance/service channels.
    plug=box(32,22.025,22.025,(tail,-11.0125,-11.0125))
    for y in (-8,8):
        for z in (-12,6.5):
            plug=plug.cut(box(34,5.8,5.5,(tail-1,y-2.9,z)))
    for y in (-12,6.5):plug=plug.cut(box(34,5.5,6,(tail-1,y,-3)))
    end=box(6,25.4,25.4,(tail-6,-12.7,-12.7))
    for sign in (-1,1):
        end=end.fuse(box(6,3.3,8,(tail-6,12.7 if sign>0 else -16,8)))
    base=box(26,24,6.61,(tail-26,-12,7))
    anchor=plug.fuse(end).fuse(base)
    # Rear-access captive M3 nut slot; no hidden inserted nut in an inaccessible cavity.
    anchor=anchor.cut(box(29,6.4,2.8,(tail-7,-3.2,-8.7)))
    for x in (tail+8,tail+18):anchor=anchor.cut(cyl(3.4,16,(x,0,-14)))
    cap=box(26,24,2.2,(tail-26,-12,14.81))
    for x in (tail-22,tail-9):
        for y in (-8,8):
            anchor=anchor.cut(cyl(2.4,10,(x,y,5)))
            cap=cap.cut(cyl(2.4,4,(x,y,14)))
            cap=cap.cut(Part.makeCone(1.0,2.2,1.2,Vector(x,y,15.81)))
            screw=cyl(2,14.8,(x,y,1.01)).fuse(Part.makeCone(1,2,1.2,Vector(x,y,15.81)))
            put(f'AnchorM2Screw_{x-tail}_{y}',screw,'slider','Steel M2x16 countersunk nominal',role='Four clamp screws; actual head profile and tightening load require proof')
            washer=cyl(4,.3,(x,y,6.7)).cut(cyl(2.2,.3,(x,y,6.7)))
            put(f'AnchorM2Washer_{x-tail}_{y}',washer,'slider','Steel')
            put(f'AnchorM2Nut_{x-tail}_{y}',hexnut(2,4,1.6,(x,y,5.1)),'slider','Steel M2 nut')
    # Pads are mechanically keyed with axial dovetail undercuts open at Z faces.
    for side in (-1,1):
        ylo=12.7 if side>0 else -16
        for which,xface,direction in [('Rear',tail-6,-1),('Front',tail,1)]:
            pad=box(3,3.3,8,(xface-3 if direction<0 else xface,ylo,8))
            # Symmetric side lug: narrow mouth1.2mm widening1.8mm inside the lug.
            yc=side*14.35
            pts=[Vector(xface,yc-.6,9),Vector(xface-direction*1.5,yc-.9,9),
                 Vector(xface-direction*1.5,yc+.9,9),Vector(xface,yc+.6,9)]
            key=Part.Face(Part.makePolygon(pts+[pts[0]])).extrude(Vector(0,0,6))
            pad=pad.fuse(key)
            anchor=anchor.cut(key)
            put(f'StopPad{which}_{side}',pad,'slider','TPU95A experimental;3mm travel',True,
                'Dovetail inserts from open Z face; nominal contact geometry; calibrate key fit and prove compression/retention')
    put('RearAnchorPlug',anchor,'slider','PETG fit / dry nylon qualification candidate',True,
        '32mm bore plug; side/top/bottom guide-nut channels; two bottom M3 bolts; removable cap clamps both open belt ends')
    put('RearAnchorMetalCap',cap,'slider','Drilled2.2mm aluminum or steel clamp cap',False,
        'Four M2 countersunk bolts; belt nominal thickness compressed1.38to1.20mm; tooth-compatible grip proof required')
    for i,x in enumerate((tail+8,tail+18)):
        put(f'PlugM3Nut_{i}',hexnut(3,5.5,2.4,(x,0,-8.5)),'slider','Steel M3 captive nut',role='Insert from open rear central slot before cap assembly')
        washer=cyl(6,.6,(x,0,-13.3)).cut(cyl(3.4,.6,(x,0,-13.3)))
        put(f'PlugM3Washer_{i}',washer,'slider','Steel')
        screw=cyl(3,10,(x,0,-13.3)).fuse(cyl(5.5,3,(x,0,-16.3)))
        put(f'PlugM3Screw_{i}',screw,'slider','Steel M3x10 socket screw',role='Accessible from tube bottom before outer insertion; smooth envelope needs actual drive recess')
    for label,xc in [('Minimum',-233.5),('Maximum',287)]:
        # Collars externally support pins; tube wall is not their sole cantilever root.
        whole=box(30,50.1,50.1,(xc-15,-25.05,-25.05))
        whole=whole.cut(box(32,38.5,38.5,(xc-16,-19.25,-19.25)))
        for y in (-35.05,25.05):whole=whole.fuse(box(30,10,13.6,(xc-15,y,-6.8)))
        whole=whole.cut(box(32,72,.8,(xc-16,-36,-.4)))
        for x in (xc-10,xc+10):
            for y in (-30.05,30.05):whole=whole.cut(cyl(4.5,30,(x,y,-15)))
        for sign in (-1,1):
            whole=whole.cut(cyl(5.1,13,(xc,sign*13,12),(0,sign,0)))
            whole=whole.cut(box(12.4,2.2,26.4,(xc-6.2,25.05 if sign>0 else -27.25,-1.2)))
            # Pin cap M3 nuts entered from top/bottom open service slots.
            for z in (3,21):
                whole=whole.cut(cyl(3.4,9,(xc,sign*18.8,z),(0,sign,0)))
                whole=whole.cut(cyl(5.8,4,(xc,sign*26.8,z),(0,sign,0)))
                whole=whole.cut(box(19.3,3,6.4,(xc-16,20 if sign>0 else -23,z-3.2)))
            capside=box(12,2,26,(xc-6,25.05 if sign>0 else -27.05,-1))
            for z in (3,21):capside=capside.cut(cyl(3.4,4,(xc,sign*24.5,z),(0,sign,0)))
            put(f'{label}PinCap_{sign}',capside,'fixed','Steel2mm drilled cap')
            put(f'{label}StopPin_{sign}',cyl(5,11.05,(xc,sign*14,12),(0,sign,0)),
                'fixed','Steel5mm ground dowel with verified strength',False,
                'Supported by split collar;14mm inner radius clears25.4mm tube; outside cap retains pin')
            for z in (3,21):
                n=hexnut(3,5.5,2.4,(0,0,0));n=oriented_y(n)
                if sign<0:n.rotate(Vector(),Vector(0,0,1),180)
                n.translate(Vector(xc,sign*20.2,z))
                put(f'{label}CapNut_{sign}_{z}',n,'fixed','Steel M3 captive nut')
                screw=cyl(3,8,(xc,sign*19.05,z),(0,sign,0)).fuse(cyl(5.5,3,(xc,sign*27.05,z),(0,sign,0)))
                put(f'{label}CapScrew_{sign}_{z}',screw,'fixed','Steel M3x8 socket screw')
        for half,z in [('Lower',-30),('Upper',.4)]:
            sh=whole.common(box(34,74,29.6,(xc-17,-37,z)))
            put(f'{label}StopCollar{half}',sh,'fixed','ASA or dry nylon qualified collar',True,
                '30mm axial body;6mm nominal radial support; four M4 clamp bolts; pin holes go through outer tube; proof single-pin event')
        for i,x in enumerate((xc-10,xc+10)):
            for sign,y in enumerate((-30.05,30.05)):
                screw=cyl(4,20,(x,y,-12.4)).fuse(cyl(7,4,(x,y,7.6)))
                put(f'{label}CollarBolt_{i}_{sign}',screw,'fixed','Steel M4x20 socket screw')
                for end,z in [('Top',6.8),('Bottom',-7.6)]:
                    w=cyl(9,.8,(x,y,z)).cut(cyl(4.5,.8,(x,y,z)))
                    put(f'{label}CollarWasher{end}_{i}_{sign}',w,'fixed','Steel')
                put(f'{label}CollarNut_{i}_{sign}',hexnut(4,7,3.2,(x,y,-10.8)),'fixed','Steel M4 locknut envelope; confirm actual height')
    return created


def verify_details(doc):
    names=[o for o in doc.Objects if hasattr(o,'Shape') and (o.Name.startswith(('Anchor','RearAnchor','PlugM3','StopPad','Minimum','Maximum')))]
    forbidden=[]
    for obj in names:
        for other in doc.Objects:
            if other.Name==obj.Name or not hasattr(other,'Shape'):continue
            if other in names and other.Name<obj.Name:continue
            if not obj.Shape.BoundBox.intersect(other.Shape.BoundBox):continue
            v=obj.Shape.common(other.Shape).Volume
            if v>1e-5:forbidden.append((obj.Name,other.Name,v))
    assert not forbidden,forbidden
    return {'new_parts':len(names),'unintended_intersections':forbidden,
            'min_pad_contact_extension_mm':-2,'min_rigid_contact_extension_mm':-5,
            'max_pad_contact_extension_mm':501.5,'max_rigid_contact_extension_mm':504.5,
            'status':'Bench-prototype geometry; grip friction teeth/cap contact and single-pin stop load require proof'}


