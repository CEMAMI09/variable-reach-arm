# Rev B print and stock fabrication guide

Print as much of the useful geometry as practical, while preserving the metal load
paths and bought wear/precision components. This supersedes earlier generic printed
carriers that are absent from the current CAD. The CAD uses square aluminum tubes
and three rigid hinged claws with compliant contact pads, **no net**.

Only the four STL files listed in `cad/review_b/print_manifest.json` are currently
exported fit prototypes. Other parts below describe fabrication intent and require
current CAD exports, exact hardware grip lengths and checks before fabrication.
Do not use legacy `cad/stl/` as a released production pack. None of these process
settings certifies powered operation or high-speed impact strength.

## Common process and acceptance

Starting settings assume a calibrated 0.4 mm nozzle and 0.2 mm layers. Perimeters
provide the load path; infill does not replace ribs, adequate wall thickness or
proper orientation. Use broad washers and captive nuts/through-bolts for primary
loads. Heat-set inserts are appropriate for covers and light adjusters, not the
only tensile retention of a shoulder. Avoid forcing printed press fits. Measure
stock, print a bore coupon, and drill/ream the final fit rather than prescribing a
universal printer compensation. Record filament, conditioning, temperature and
slicer settings. Inspect layer bonding and proof-test actual oriented coupons.

Use PETG for inexpensive cold fit parts and guards. ASA is an alternative where
measured heat/creep demands justify an enclosed print process. Tough dry nylon is
an optional later impact material, not a required third spool. PLA+ suits jigs and
unloaded mockups; avoid it in hot/preloaded mechanisms. CF-filled filament has no
automatic strength credit and is not a substitute for laminated carbon-fiber tube.

## Should be 3D printed

**Rigid claw fingers (three ClawFitPrototype copies):** PETG first, qualified tough
nylon if impact tests demand it. Lay the broad finger face flat so root bending
is in the layer plane. Six perimeters, 35–45% infill, local solid pivot/horn region,
no supports on hinge surfaces. Current finger thickness is 8 mm with nominal
3.3 mm pivot bore for a measured 3 mm smooth steel pin; preserve at least 3 mm
ligament around the pivot and rounded root transitions. Retain pads through M2
holes. Do not print pins or run pivots on screw threads. Failure modes: root/horn
crack, bore wear, tendon abrasion and pad pullout. Test a whole mounted finger,
not only a generic tensile coupon.

**Palm (GripperPalmFitPrototype):** PETG for fit, ASA/qualified nylon for later
service. Plate flat; six perimeters, 35–45% infill. Current ring is 46 mm outer/
30 mm inner radius with a 4 mm plate. The 12 mm clevis gap receives an 8 mm finger
and nominal 2 mm thrust spacers each side. That nominal stack has no endplay: fit
real shims to obtain approximately 0.1–0.2 mm free axial movement without wobble.
Use smooth metal pins with positive retention and M3 broad washers at pad/strut
attachments. Do not tighten a locknut until a pivot binds. Upright clevis ears are
vulnerable to layer peel; strengthen/reorient into a split assembly if proof tests
show peeling. Failures: ear delamination, pin escape and strut-mount cracks.

**Compliant palm/finger pads (PalmPadFitPrototype plus fitted finger pads):** TPU
95A starting material, broad face flat; 3–4 perimeters, 15–25% infill. Mechanically
retain with broad washers and rounded edges; no adhesive-only retention. Current
palm pad is 4 mm thick, mounted with three M3 fixings and 1 mm standoff. It cannot
be credited with 25 mm stopping travel. Test force/displacement, bottoming, rebound
and tear; a trapped foam insert is a separate economical experiment. Do not print
the entire rigid finger in TPU merely because it touches a ball.

**Servo cradle and straps:** PETG cold fit prototype, ASA if measured servo heating
requires it. Cradle floor down, six perimeters and 30–40% infill; straps broad face
down with at least four perimeters. Current allowance body is 24 × 13 × 29 mm;
cradle floor is 3 mm, nominal towers 4 × 4 mm, straps 2 mm. Use M2 through-bolts/
washers for straps and common M4 clamp bolts through two 5 mm metal spacers at the
mount foot. Do not trust towers as printed threads. Fit the actual servo before
printing a service version; horn motion/wiring must clear the whole claw sweep.
Failures: strap/tower splitting, long arm flexure, preload creep and wire pinching.
This cradle supports a packaging envelope; it does not qualify the unknown servo.

**Cable clips, switch/sensor mounts, low-energy finger-access covers, electronics
tray and drill jigs:** PETG, broad mounting face down, 3–4 perimeters, 15–25% infill,
2 mm minimum cover wall and rounded strain-relief edges. M3 inserts/through-bolts,
service loops and tie points on both sides of connectors. Keep heat-producing
resistors/drivers off plastic or provide a rated metal spreader/standoff. Failure
modes: loose sensor datum, cracked tabs, chafed wires and heat distortion. A printed
cover is not validated projectile containment or an electrical fire enclosure.

## Can be printed if designed and qualified correctly

**GuideFitCoupon:** PETG, channel axis vertical as exported, 5–6 perimeters, 30–40%
infill. Compare measured stock face spacing, corner radius, straightness and guide
access. It is a coupon only. Current actual shoes are solid acetal with recessed
M2 hardware, not a PETG carrier plus an unmodeled liner. Do not assemble the coupon
as a sliding structural guide or force it onto stock.

**Split tube/catcher clamps and pitch saddle bodies:** PETG for unpowered fit; ASA
or tested nylon for a qualified hybrid. Print split face down, 6–8 perimeters,
40–50% infill, ribs at bolt ears with rounded roots. Maintain the current 22 mm
catcher-clamp length, approximately 3.5 mm wall, four M4 holes and deliberate split
closure clearance; fit against measured 25.4 mm tube. Pitch saddles fit 38.1 mm
outer stock and must transfer load to metal shoes/rails/stubs with through-bolts.
Use broad washers/locknuts, metal compression stops as needed, no insert-only
primary load path. Failures: clamp slip, split-ear peel, tube crushing and creep.
Nominal CAD clearance does not establish clamping friction or bolt preload.

**Pitch/yaw bearing carriers and caps:** ASA or tested nylon, split/bore axis chosen
so radial bearing load remains in continuous perimeter paths; mounting flange flat
is a coupon starting orientation. Eight perimeters, 40% infill, at least 5 mm
support ribs where geometry permits. Current pitch/jackshaft bearings are 6001 class
12 × 28 × 8 mm; yaw bearings 6204 class 20 × 47 × 14 mm. Preserve actual race
shoulders and metal load spreading. Never clamp inner and outer races together or
hammer bearings into an undersized print. Use metal through-bolts, sleeves and
positive axial caps. Failures: outer-race creep, ovalization, cap pullout and
coaxiality loss. Hot/preloaded carriers may require stock-metal replacement.

**Large reduction pulley webs and flanges:** optional PETG for low-load trials,
ASA/qualified nylon for later service. Shaft axis vertical, 6–8 perimeters,
40–50% infill, locally solid tooth ring and hub bolt region with a ribbed web.
Use a purchased metal clamp hub and through-bolted pattern. A current smooth pitch
envelope is not an exportable timing pulley: generate the actual compatible tooth
profile and check belt seating, runout, tooth loading and thermal creep first.
Do not put a setscrew directly into printed plastic. Failure modes: tooth shear,
ratcheting, eccentricity and hub/web splitting. Do not make a printed pulley the
only power-loss gravity restraint. Savings are not booked until quotes and proof
loads demonstrate the hybrid is worthwhile.

## Should probably be stock metal or purchased polymer

**Small sliding guide shoes:** cut/drill acetal stock; print drill and fit fixtures.
There are six front and six rear shoes, nominal 30 mm axial length; top/bottom
strips are 6 mm wide at ±8 mm centers, giving a 10 mm corridor around a 9 mm belt.
Radial shoe thickness is nominal 4.6625 mm for the present tube pair; actual tube
corner radii and tolerance decide final shimming. Twenty-four recessed M2x8 socket
screws, 24 nuts and 24 thin washers retain them. Keep heads at least 0.5 mm below
the sliding face, verify screws do not protrude and preserve the staggered service
holes. Hand-cycle the full stroke under transverse load before powered testing.
Failures: screw scraping, pad migration, wear, overpreload binding and nut loss.
Cheap generic printed shoes are not automatically economical after repeated jams.

**Motor/tension plates, yoke cheeks, saddle rails/shoes, long column/braces and
base:** use drilled aluminum plate/angle/tube with printed hole jigs. These parts
carry belt preload, heat and long-lever bending; thin stock usually beats thick
FDM in stiffness per mass and print time. Print only temporary motor-envelope
mockups in PETG (six perimeters, 30% infill, flange flat, through-bolts); do not
power-load them on that basis. Current metal CAD needs its actual cut/drill list,
coaxiality, wrench access and material grade checked. Failures include bracket
flexure, slot slip, tube crushing and anchor pullout. A plywood bench fixture is
a possible stationary rig support, not a drop-in rotating-yoke substitution.

**Containment panels:** suitable purchased polycarbonate and anchored frame; printed
edging/clips are acceptable after panel-retention checks. Keep this separate from
cosmetic belt guards. Panel thickness and retention depend on credible projectiles;
there is no blanket safety credit for transparent sheet.

## Should definitely not be consumer-FDM printed

- Outer 38.1 mm and inner 25.4 mm structural telescoping tubes: purchased aluminum,
  nominal 1.5875 mm walls, 770/805 mm cut lengths. Measure actual stock dimensions.
- Steel pitch/yaw/jackshafts, smooth claw pins, shaft collars and loaded metal hubs.
- Rolling bearings, small drive pinions and loaded idler bearing running surfaces.
- Timing belts, load-bearing tendons, torsion/extension springs and spring retainers
  where a printed failure could eject the spring; use metal retention and guards.
- Primary telescope stop straps/contacts and pitch brake/independent fall restraint.
  Print replaceable bumpers around a metal secondary stop only after energy tests.
- Structural screws, nuts, washers, electrical contactors, fuses and bus dump resistor.

These decisions apply to the user's consumer polymer printer. They are not claims
about industrial metal printing. Keeping inexpensive bought hardware is normally
better value than reproducing precision, heat resistance and fatigue properties.

## Before spending on full assemblies

Check the four fit prints and measured tubes first. Weigh complete tip hardware,
servo, springs/tendons and wiring against the model's 170 g distal allowance.
Select actual purchased interfaces before final-fit exports. Hand-assemble and
cycle through every stroke/jaw angle, inspect tool access, record slip/friction,
and proof-test the intended load paths. Powered trials additionally require the
release gates in `docs/bringup.md` and `docs/safety.md`; print settings alone do not
release a subsystem. `docs/value_manufacturing_review.md` records cash totals and
conditional savings without pretending a restrained rig is the full robot.

## Added drive hardware — current baseline

- Rear plug and stop collars: can be printed after fit and load qualification; PETG for fit, qualified tough nylon for cyclic parts. Print collars with tube axis normal to the bed, 6 perimeters and 40% infill, and use through-bolts with metal washers. Collar slip, lug layer separation and creep are principal failures. Measure the actual tube before choosing clearance.
- Front idler bracket: conditional print, 6 perimeters and 40% infill; orient its bridge/load path in the layer plane and split the carrier if necessary. Use metal bearing caps, shaft and spacers. Check bridge bending and bearing-seat creep before powered operation.
- Claw fingers/palm: print as specified above; new spring slots and 2 mm stop pins require fit coupons before a full set. Buy springs and metal pivots; do not print them.
- TPU stop pads: print solid in their small keyed section; do not assume the full 3 mm thickness is usable stopping stroke. Treat pads as replaceable consumables.
- Belt clamp cap, 5 mm stop pins/retainers, shafts, bearings and small toothed pulleys: purchased/cut metal. These inexpensive parts carry concentrated loads and are poor places to save a few dollars by printing.

These additions are CAD prototypes, not released print files. See the telescope and claw design documents for assembly order and unresolved dimensions.
> Compact college V1 override: the user accepts lower performance and maximum
> practical printing. For that separate compact design, bearing caps, belt-clamp
> caps, pulley bodies, base, shoulder and both boom shells are planned as printed
> parts. See `engineering/college_v1_print_manifest.json` and
> `docs/college_v1_named_bom.md`. Metal-only guidance for the larger high-speed
> Rev B must not be applied to V1 by default. Compact printable CAD is not released.
