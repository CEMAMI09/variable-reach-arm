# Compact V1 printed telescope: assembly and limits

This is a new compact **low-speed fit prototype**, not the existing full-size fair assembly. All dimensions are millimetres. Mesh validity and printer-envelope checks do not establish structural strength or a powered-motion release.

## Geometry

- Outer boom: 380 long, 42 square, 34.8 square bore; three 126.667-long segments. Assembly span X=-180 to200.
- Outer joint flange:60 square,8 thick, four3.4 clearance holes at +/-25 in both cross-sectional directions. Upper flange underside uses a45-degree ramp; each part stands upright on its lower flange.
- Inner boom:400 long,30 square,23.6 square bore; three133.333-long segments. First two have30-long internal23.2-square bonded spigots, so the tallest print is163.333. Assembly span X=-130+extension to270+extension.
- Normal commanded stroke:200. Nominal remaining tube overlap at maximum stroke:130. This must be enforced by controller and a separately qualified travel restraint. Guide contact alone does not stop at200.
- Front pad shoulder lies at X180..182; pads occupy X182..198 and the removable guide cap X200..204. Inner tube-to-cap clearance is0.4 per face, before print error and deflection. Nominal rear guide ring centre X=-122+extension; guide spacing is312 mm retracted and112 mm extended.
- Local model Z becomes assembly X with a+90 degree rotation aroundY. All exported models rest on Z=0. Nothing requires a build envelope greater than60x60x163.333.

## Print first: fit coupons

Print the outer and inner coupons in the same PETG, layer height, extrusion calibration and orientation intended for the long parts. Use0.20 layers, six perimeters,0.4 nozzle baseline. Do not scale meshes to correct fits; change the relevant dimensions and regenerate. Check that the30 mm inner coupon slides squarely in the outer without rotation-sensitive binding. Actual Prusa model, nozzle and filament profile remain to be selected in PrusaSlicer.

Next print one front pad, the rear guide ring and the short male and female joint coupons as fit checks. The outer-to-inner free gap is intentionally taken up by guides. Measure the PTFE tape including adhesive: nominal0.13 mm. Rear ring outside34.14 plus tape on both faces makes34.4, leaving0.4 total nominal clearance in34.8 bore. If your tape differs, adjust ring dimensions. Do not substitute an arbitrary tape thickness.

## Inner joints

Use four M3x12 DIN965/ISO7046 90-degree countersunk screws, four M3 DIN934 nuts and plastic-compatible epoxy for the two joints. On each spigot insert two nuts through the10 mm axial access bore into the radial pockets before mating. The two screw axes are90 degrees apart, at10 and22 from the joint. Test access and engagement on a coupon before bonding. The screw head must be flush or below the30 mm outside surface. A protruding screw or glue ridge can jam the front guide. Do not countersink so deeply that the shell cracks.

The spigot has0.2 mm adhesive allowance per face. Degrease using a filament-compatible process, roughen only the bonding surfaces, align on a flat reference, and clamp straight through cure. PETG adhesive strength is formulation-dependent: perform a sacrificial joint bending test; the geometry is not a bonded-joint strength certification. The joint remains a first-likely failure location because upright prints load interlayer bonds in boom bending. Move slowly and retain the arm while testing.

## Outer joints and guides

Use eight M3x20 bolts, sixteen M3 washers and eight M3 nuts across the two flange joints. Assemble around a straight temporary mandrel or use the completed straight inner tube as an alignment reference without glue contact. Slightly loose3.4 holes allow alignment; tighten evenly. Do not use bolt force to straighten warped prints.

Bond the rear guide ring over the rear16 mm of the inner tube and apply PTFE on its outer four faces. The rear cap is mounted after the ring. Keep the seam and tape edges flush. The rear cap plate sits X=-135+extension to-130+extension; its plug projects into the bore. Outer rear cap plate sits X=-185..-180. Caps currently use bonded plug retention; they are not certified impact-stop mounts.

Insert the inner tube from the front before attaching its claw. Place the four front guide pads between the printed shoulder and removable cap, PTFE against the inner tube. Orient each pad's16 mm dimension along the boom. Four M3x16 screws through the outer flange adjust the pads; M3 nuts in the external hex pockets provide threads. Fit M3 jam nuts externally if screw length and access permit. The pad dimple receives the screw tip. The front cap uses four M3x8 screws in2.5 mm printed pilot holes. Drill the pilots to measured suitable size; start with a coupon and do not overtorque plastic threads.

Adjust until the unloaded telescope traverses the entire200 mm stroke by hand with no catching or excessive shake. Recheck under a modest transverse hand load. A guide screw is an adjustment, not a structural bolt: crushing a pad increases friction and creep.

## Travel restraint, drive and outstanding interfaces

The rear caps provide two4 mm cord bores. A low-stretch2 mm stop cord between the caps can be arranged to become taut at200 mm extension (nominal anchor separation250 mm). Measure the actual installed anchor locations and knot take-up: do not cut a250 mm cord and assume it produces250 mm working length. A separate external redundant restraint is required during powered testing because cap glue and knots are unqualified. Keep cord slack contained behind the moving rear guide; prove it cannot enter the guide or drive. This is not an energy absorber or a precision homing switch. Normal motion must decelerate before the cord is taut.

External belt motor/idler mounts, belt attachment, limit switches and a robust adjustable hard stop are NOT yet implemented in the compact assembly. They remain design work, not merely physical validation. No powered-release claim is made for this standalone subsystem. Do not run open-loop extension until the complete assembly supplies those items and a loss-of-power restraint.

## Validation performed

FreeCAD1.1 shape checks:15 unique parts, all valid, each one connected solid, all at bedZ=0 and within180 mm in every dimension. Upper flange ramps avoid long horizontal support shelves. Horizontal radial holes may require drilling; nut pockets and spigot fit require a physical coupon. Full slicer preview must verify first-layer contact, perimeters and bridges using the actual printer profile. No G-code or universal printer profile is implied.
