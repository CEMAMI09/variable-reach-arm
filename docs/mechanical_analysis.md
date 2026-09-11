# Mechanical design, fabrication and physical acceptance

This report covers RevB's telescope and three-finger claw concept. It supersedes the
original unsupported claim of manufacturability and does not release the full robot
for high-speed use. The live CAD study and `engineering/design_parameters.json`
are the geometry references. The complete yaw/pitch transmissions, brake, hard-stop
mounts and detailed electronics still need procurement dimensions and assembly CAD.

## Changes and tradeoffs

1. **Original problem:** round tubes and disconnected guides supplied no credible
anti-rotation or complete sliding load path. **Why it matters:** twist and binding
destroy repeatability and interception. **Implemented:** square purchased aluminum
outer/inner tube study, moving rear shoes and fixed mouth shoes with190mm minimum
spacing/240mm overlap. **Tradeoff:** more mass than high-grade CF, but predictable
isotropic properties, common stock, simple cuts and no drilled composite joints.
The4.7625mm nominal gap permits the belt/clamp; a larger inner tube would be stiffer
but leaves insufficient belt packaging. Do not add a second guide rail by default.

2. **Original problem:** geometry allowed catcher mounting hardware to intersect the
outer at retraction; a through pitch shaft would block the inner. **Implemented:**
outer ends at520mm, the inner now extends to585mm at retraction and the claw clamp
was shifted25mm forward to clear the idler/belt envelope, with revised rear support and separate
external trunnions. **Tradeoff:** rear swing envelope extends to roughly300mm behind
pitch with motor/belt guards. Check this envelope across every yaw/pitch position.

3. **Original problem:** motors were approved using holding torque and a nonexistent
45% balance spring. **Implemented:** reproducible translated-mass dynamics, I_dot,
cross-axis coupling, dynamic guide loads and honest motor requirements. No balance
credit. **Tradeoff:** maximum-speed procurement remains blocked until a measured or
readable exact manufacturer curve is obtained; slower restrained tests are feasible
with a separately qualified drive. This is better use of money than buying the wrong
three motors and compensating with increasingly heavy mechanisms.

4. **Original problem:** passive capture and active retraction had no force budget.
**Implemented:** three curved claws, single servo opening via three tendons, spring
closure concept, TPU pads, steel pivots; force/energy screens at1/2/4m/s relative speed
and signed radial matching. **Tradeoff:** no net, as required by the user; shorter
compliance travel demands much better velocity matching. The servo/tendon routes,
spring rates, retention geometry and stop strength are concept-level until assembled.

5. **Original problem:** sparse BOM understated the bill by$252. **Implemented:**
exact quantity arithmetic, full-spool/stock purchase cost, reduction hardware, brake,
dump, fusing, feedback, guards, harness and reserve. **Tradeoff:** complete cost is
above budget. A restrained single-axis rig is the cost-efficient next purchase.

## Print, fabricate or buy decisions

The settings below are starting **process specifications**, not material strength
certificates. Use a0.4mm nozzle/0.2mm layers unless calibrated otherwise. Continuous
walls/ribs carry load; infill fills space. Structural print proof coupons must use
the same machine, material dryness, orientation, layer height and temperatures.

- **Fixed front guide housing — can be printed if designed correctly.** ASA for
temperature-stable indoor parts, or PETG for first low-speed coupons. Print the split
faces flat so band-clamp compression and bolt load lie mainly in the XY plane.
Use6 perimeters (nominal2.4mm shell),35–45% gyroid,4–5mm ribs and >=3mm fillets.
Nominal housing bore must be fit to measured38.1mm outer stock; do not force a printed
press fit. Use two metal band clamps or M4 through-bolts with captive nuts and broad
washers; heat-set inserts serve covers/adjusters only, not the primary restraint.
Failures: creep preload loss, layer splitting beside clamp ears and pad migration.

- **Moving rear guide carrier — can be printed if designed correctly.** Tough dry
nylon is preferred if the printer can reliably dry/enclose it; PETG is acceptable for
restrained low-speed testing. Print split clamp halves flat,6–8 perimeters and40%
infill,>=3mm webs. The total radial gap4.7625mm must accommodate rigid carrier,
wear pad and running clearance; do not fill this entire gap with soft UHMW tape.
Use replaceable0.5–1mm acetal/UHMW wear faces backed by rigid shims and30mm axial
contact. Top faces around the belt/clamp can be much narrower than the side faces;
the pressure model conservatively uses2.5mm individual-face width until final CAD
contact width is reconciled. Actual corner radii must clear. Captive M3 nuts and
steel clamp plates distribute load. Failures: pad edge wear, swollen nylon, loose
fasteners, carrier creep and binding from excessive four-sided preload.

- **Pitch tube clamp and trunnion carrier — can be printed for bench iteration;
hybrid construction required for high dynamics.** ASA or tested nylon, split faces
flat,8 perimeters,40–50% infill,>=5mm ribs and >=4mm stress-transition radii. The
metal trunnions must have broad bolted flanges or crossbars that carry shaft reaction
through metal hardware into circumferential tube clamps. Use M4/M5 through-bolts,
large washers and locknuts; keep threads/inserts outside tensile peel load paths.
Critical dimensions are12mm shaft support, tube clearance, trunnion coaxiality and
opposed bearing positions. Failures: clamp slip, layer peel, thermal creep, cracked
bolt ears, thin-wall tube crushing. The desk tube stress factor does not approve this
printed component. Local coupon and subassembly proof tests are mandatory.

- **Yaw frame/bearing carriers — can be printed if metal loads bypass weak joints.**
Print ASA bearing blocks with split bores facing up,8 perimeters,40% infill and>=5mm
base ribs. Bore sizing comes from calibrated coupons for actual bearing OD; clamp
around the outer race with a stop gap, never hammer a press fit. Use metal shaft,
real bearings, spacers/collars and M5 through-bolts into the anchored frame.
Avoid large tall printed columns; use low triangulated stock frame. Failures: yaw
wobble from bearing separation too small, bearing creep and unanchored base overturn.

- **Motor brackets — can be printed for mockup; should probably be sheet/angle
metal for powered duty.** Motors concentrate heat and belt preload. Use common
3–4mm aluminum angle/plate drilled with a printed jig; low mass is maintained by
triangulation. If printed for the bench, ASA6–8 perimeters/40% infill, flange down,
M4 through-bolts and a metal spreading plate. Set motor clearance from the *selected*
part drawing, not a generic NEMA cube. Failures: slotted tension mount slips,
plate flex and thermal creep changing belt alignment. Do not bond motor mounts.

- **Large reduction pulley — can be printed after qualification.** ASA or tough
nylon, shaft axis vertical,6–8 perimeters and40–50% infill, solid tooth perimeter
region but ribbed web, metal split-clamp hub and through-bolted pattern. Measure
pitch diameter/runout and confirm vendor-compatible tooth profile. No set screw
cut directly into plastic; no unsupported printed motor pinion. Failures: tooth
shear, layer splitting at hub, creep, belt ratcheting and eccentricity. Treat it as a
replaceable wear part, and do not route the only gravity-fall restraint through it.

- **Small pulleys, idlers, bearings, shafts and pivot pins — should definitely not
be printed.** Buy metal timing pulleys with compatible belts, ball bearings and steel
shafts/pins. A smooth printed cylinder is not a timing pulley. M3 steel shoulder
pins/bolts with smooth bearing surface and positive retention serve claw hinges;
do not rotate on screw threads. Side-loads require spacers and washers.

- **Telescope tubes — should definitely not be printed.** Buy aluminum stock with
certified alloy/temper where possible. FDM seams, creep and poor stiffness per mass
are incompatible with a long sliding structural member. CF could lower boom mass
later, but laminate axial/torsional stiffness, corners, abrasion and fastening need
supplier data and end sleeves. CF-filled filament is not equivalent to a CF tube.
Do not cut a long belt slot into either tube; it reduces torsion stiffness and invites
crack growth. The belt/clamp occupies the annular space instead.

- **Claw carrier and rigid fingers — should be printed.** Tough PETG/ASA or dry
nylon for rigid load-bearing fingers,6 perimeters and30–40% infill with solid hinge
regions. Print each curved finger flat on its broad side so the primary finger-root
bending path lies in the XY plane. Use >=3mm fillets and >=3mm ligaments around
M3 pin holes, with smooth replaceable sleeves/washers. Drill/ream calibrated holes;
do not force pins. The common carrier can use4–6 perimeters/30% infill with metal
clamping hardware. Constrain each jaw with mechanical open/closed stops so the
servo never serves as the hard stop. Failures: hinge-root crack, pin walkout, tendon
abrasion, spring escape, overcenter jamming and finger fatigue.

- **Claw contact pads/compliant inserts — should be printed.** TPU95A, broad contact
face down where possible,3–4 perimeters and10–20% infill,2–3mm walls. Mechanically
trap pads using dovetail/through-hole features plus removable screws; do not rely
only on adhesive. Pad thickness/stroke comes from instrumented foam-ball impact
coupons. The25mm effective stop distance remains unverified. TPU on aluminum/rigid
plastic needs rounded transitions. Failures: tear, bottoming-out, rebound/bounce-out
and creep that changes retention aperture.

- **Tendons, springs, hard stops and critical brake parts — should definitely not
be printed.** Use rated cord/cable, metal torsion springs with captured legs, metal
end-stop strap/screws and a specified brake. Print guards and fixtures around them.
A spring fractured/ejected toward the user is a hazard; enclose it. Printed flexures
are useful compliance coupons, not an unmeasured permanent retention spring.

- **Cable clips, sensor mounts, covers and wire strain relief — should be printed.**
PETG/ASA, broad base flat,3–4 perimeters/15–25% infill,>=2mm wall; M3 inserts are
appropriate here. TPU boots can use3 perimeters/15% infill. Provide tie points on
both sides of connectors, protected flex loops, service labels and removable covers.
Do not run wiring under belt teeth or allow free loops inside the telescope.

- **Base, frame, guards — should probably be stock material.** Rigid bench anchor,
plywood/metal base and aluminum angle avoid printing kilograms. Use metal through
fasteners and triangulation. Transparent containment uses appropriate polycarbonate
sheet/frame; printed edging is fine. Guard adequacy must be evaluated for thrown
balls and failed moving components, not only finger access.

PLA/PLA+ may make dimensional jigs and cold fit-check mockups. Its low-temperature
creep is a poor reason to retain it for hot motor mounts. PETG trades toughness and
ease for creep; ASA adds thermal margin but needs printing control; nylon adds
toughness but changes with moisture. Fiber-filled nylon may improve stiffness and
dimensional stability, but abrasion, layer strength, notch behavior and hardware
compatibility still require coupon testing. None deserves automatic structural credit.

## Assembly and maintenance sequence

1. Measure stock straightness, wall, corner radii and bore. Cut square, deburr and
clean; retain offcuts for fit/fastener coupons. Do not sand aggressively to force fit.
2. Assemble bare inner/outer shoes on the bench with no motor. Adjust one datum pair
and the orthogonal compliant/shimmed pair; check push force and yaw/twist at each
50mm station. Record forward/reverse breakaway and moving friction under tip load.
3. Fit the rear carriage and belt endpoints before fitting removable rear drive
supports. Verify the metal clamp passes every guide and leaves the top belt corridor.
4. Install belt pulleys/tensioner, end stops and switches. Use a thinmetal top strap
secured by two bands for stop threads, not thin-tube-wall threads. Keep stop tips out
of the moving belt strip. Hand-cycle to both physical stops. Confirm software500mm
endpoint is before the proposed515mm hard stop with enough measured braking distance.
5. Assemble claws/pins/springs/tendons/servo while detached, weigh whole tip and test
all jaw angles. Check passive retention in arbitrary orientation and release repeatability.
6. Install in a clamped extension rig behind a guard. Commission at lower than the
proposed150mm/s cap initially. Check independent current/limit/E-stop responses.
7. Build and independently proof the yaw/pitch support, drive and brake before
adding the telescope. Verify power-off drop behavior with a restraint attached.
8. Mount the telescope/claw, route strain-relieved harness, log unloaded/loaded current
and mass, then increase operating limits only after the explicit test gates pass.

Keep guide shoes, fingers, pads and belts accessible and individually replaceable.
Use standard hex hardware with tool access from outside the motion envelope. Do not
bury sensor connectors behind glued shells. Recheck pad preload and belt tension
after the first50,500 and5000 cycles, recording wear and any rising friction.

## Hard-stop and claw timing screen

`review_results.json` contains extension stop energy, equivalent rotor mass and a
two-M4grade8.8-screw screen. The model assumes5mm effective bumper travel,2× average
deceleration load and continued pushing equivalent to0.6Nm extension motor torque.
This is intentionally more demanding than inertial energy alone. Actual motor stall
force/current cutoff, metal strap bending, clamp slip, screw engagement and inner
wall crushing remain release gates. Both screws need load-sharing contact tolerances;
one-first-contact case should also be proof-tested. Metal screw strength does not
prove the thin tube or carrier survives. Do not use bare sharp screw points as impact
faces; spread contact and fit elastomer bumpers with a metal secondary stop.

Numerically the synchronized target-speed example is0.451J and233N illustrative
design load. Two M4 root3.1mm screws with **maximum3mm unsupported length** give
about122MPa equivalent stress and5.23 nominal yield factor at640MPa. If one screw
takes the entire event, that factor falls to about2.61 before further impact
uncertainty. The3mm maximum replaced an inadequate5mm lever after critique.
Maintain this support distance and design the metal strap and bumper for the
single-contact event. This remains a screen, not a released target-speed safeguard.
Low-speed rig operation reduces kinetic energy substantially but still includes
motor-driven pushing. The complete claw now carries a170g weighing allowance
including servo/hardware/wiring; the CAD plastic volume alone is not its mass.

The illustrative claw calculation models18g110mm finger plus4g pad,0.015Nm spring
and0.005Nm friction. It predicts about104ms no-contact closure, while a ball crosses
60mm at4m/s in15ms. Those values are not measured spring specifications, but they
show why contact-triggered closure cannot be assumed. Three tendons require an
illustrative0.10Nm servo opening torque with2× margin at10mm servo horn/12mm finger
horn. Servo speed, horn sweep, tendon take-up, current spike and simultaneous jaw
opening must be measured. Spring force must retain the ball without ejecting it or
causing excessive contact pressure. Use a predicted preposition and passive yielding
capture geometry; do not certify retention from animation alone.

## Desk-design gates versus prototype unknowns

Still solvable before ordering: selected motor/driver torque-speed curves, exact
reduction CAD, brake and DC stop topology, final belt working ratings, hub fastening,
shaft/bearing layout, camera synchronization choice and the cost/requirements decision.
Do not call these physical unknowns to conceal unfinished design.

Physical unknowns after those decisions: as-built guide friction/creep and tube fit,
claw/foam impulse and rebound, true tip mass/stiffness, tendon closure timing,
loaded acceleration/thermal behavior, encoder repeatability, loop stability, vibration,
vision latency and catch success. Test the tube/guide/claw parts first, because those
are cheap to change and determine whether the high-speed ambition is credible.

Likely first failures are finger hinge/pad retention, rear-guide wear/preload drift,
belt clamp slip or tooth skipping, tendon abrasion and printed motor-mount creep.
Contain and instrument those failures during low-energy tests. The design is suitable
for **fit coupons and restrained subsystem experimentation**, not a final manufacturing
release or an autonomous catching build.
