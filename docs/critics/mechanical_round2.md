# Independent mechanical/CAD critic — round 2

Review: 2026-09-07. Snapshot: `build_review_robot.py` producing 219 solid objects at
250mm extension, yaw 0°, pitch 20°; current `telescope_guides.py` and telescope/claw
source. The original GUI assembly was not accessed or modified. This audit used
FreeCADCmd 1.1.3 and broad-phase bounding boxes followed by solid intersection
booleans. It did not change implementation files. Several parts are deliberately
supplier envelopes or NOT RELEASED studies; those statuses are preserved here.

## Verdict and scores

The full model now represents the robot's architecture, but it cannot yet be
assembled as drawn. The first telescope collision and clamping issues were addressed;
the new full assembly introduces major preventable intersections and disconnected
bearing interfaces. These are desk-design issues, not uncertainty requiring powered
prototype testing. Do not call the full model manufacturable or infer approval from
its 219 valid objects.

Scores for this snapshot: mechanics 4/10; full CAD/manufacturing readiness 3/10;
3D-print design 5/10; cost efficiency against the requested complete-machine budget
3/10. Approval scope remains isolated unpowered fit/guide/claw experiments. The
new ESP32/servo ownership information improves the phased rig budget but does not
close the complete-machine budget or hardware qualification.

S/L/P/C below mean severity, likelihood, performance impact, and cost of fixing later,
each 1–5. These are ordinal design-review priorities, not probabilistic estimates.

## Resolved or improved since round 1

- The inner tube is 805mm and reaches x=585mm when retracted, moving its collar
  away from the front belt/idler. The intended 700mm mouth reference remains.
- The collar has 0.4mm relief per split face and shorter external ears; the previous
  flange bottoming defect is addressed geometrically. Clamp friction/crush proof remains.
- Claw hinges now include two 2mm spacers around each 8mm link in its 12mm clevis.
- Acetal front/rear shoes now have recessed M2 retention screws, washers, nuts,
  staggered opposing service holes, and documented assembly access. This is a real
  improvement over floating pads. Actual preload, wear, straightness and fastener
  durability remain physical test gates.
- Major support frames, bearing spacings, reductions, motors, brake and guarding
  are now represented in a full assembly. The model no longer relies on a solid
  shaft passing through the telescoping tube. New geometry errors follow below.

## Major concrete findings

### R2-M1 — yaw output pulley passes through all four cage posts (5/5/5/4)

The 80T HTD5 pulley pitch radius is 63.662mm. Cage posts are centered at x/y=±40mm,
radius 56.569mm, each with 6mm outside radius. Each post intersects `YawOutput80`
by 709.969mm³. This is a structural collision, not a cosmetic overbound belt-ring
artifact. The 80T output is also different from the old 60T output documentation.

Move the posts outside the actual pulley flange and belt swept envelope, or change
the reduction geometry. A starting post center at ±55mm gives radial distance
77.78mm, but requires corresponding wider upper deck, hole pattern and guards;
actual flange OD, belt width and clearances must still be checked. Re-evaluate
torsional stiffness and cost after the change. Do not notch away a load-bearing post.

### R2-M2 — pitch jack pulley occupies a bearing (4/5/5/4)

`PitchJack20` is centered at y=110mm with width 9mm, so its envelope spans
105.5–114.5mm. `PitchJackBearing_102` spans y=102–110mm. Their solid overlap is
2,261.947mm³. A pulley hub would need more space still. The inner bearing, pulley
planes and support plate must be laid out as one axial stack with positive shaft
retention. Add a direct pulley/bearing nonintersection assertion.

The other pitch jack bearing spans 146–154mm, while its support plate starts at
154mm. The bearing ends at the plate face rather than seating inside a housing.
The yaw upper jack bearing similarly ends at z=476mm where its plate begins.
These interfaces have no meaningful radial support across the bearing width;
matching hole diameters in the adjacent plate do not support a floating bearing.
Use a full-width removable cartridge or an intentional shoulder/retainer housing.

### R2-M3 — brace layout installs multiple solids and bolts in the same space (4/5/4/4)

Opposite diagonal braces share the same upper endpoint and plate plane. Each
opposed pair intersects by 1,933.764mm³. The source emits two identical upper
bolts for each opposed pair, causing 1,958.591mm³ duplicate hardware. The two
orthogonal bolt directions also cross at z=300mm, producing 144mm³ intersections.
Only one crush sleeve direction was modeled at that height; it cannot support
all the specified orthogonal tightening loads.

Stagger the two orthogonal brace heights and deliberately stack the two same-plane
links using one shared bolt and appropriate spacers, or place them on opposite
column faces. Add a crush sleeve matching each installed cross-column bolt. The
brace lower ends currently penetrate the base plate by 69.255mm³ each and their
foot brackets by 129.279mm³ each; raising/repositioning the lower pivot and ensuring
adequate edge distance is necessary. Check the full flat-link circular end, not
only the hole center. Avoid treating intersecting links as a welded assembly.

### R2-M4 — yaw shaft and motor/jackshaft cross unrelated solid structure (4/5/5/4)

- `YawKeyedShaft20` intersects `ColumnCrushSleeve_390`: 422.623mm³.
- `YawJackshaft12` crosses the unbored `YawLowerDeck`: 678.584mm³.
- The yaw motor shaft intersects `YawLowerDeck`: 190.015mm³.

Set the main shaft lower end clear of the mast sleeve or relocate the sleeve while
preserving the column-cap fastening path. Provide the real jackshaft bearing bore
and housing at its location. Mount the selected yaw motor against a deliberately
bored mounting face with register, shaft and bolt clearance; do not simply drill a
small shaft hole if the motor needs a register and 8mm offset to the existing deck.

### R2-M5 — support and fastener patterns disagree (4/5/4/4)

The yaw cage spacer centers are ±40mm, but the corresponding deck/cartridge hole
pattern is ±29mm. The posts also intersect the lower cartridges by 153.247mm³ each
and their caps by 25.541mm³ each. Define separate cartridge bolts and cage tie rods,
with real matching holes and unobstructed nuts. The yaw jack upper support holes
are x=−140/−90, y=±25mm, while its four spacer centers are x=−145/−85, y=±27mm;
these cannot take the claimed through tie bolts.

`YawHubPlateSpacer` has no four M6 holes, so each modeled hub screw crosses its
solid by 84.823mm³. Bore the common four-hole pattern through the complete stack.
`YawUpperShaftCollar` spans z=519–527mm while the flange starts at 525mm, producing
1,183.442mm³ overlap. Set an intentional bearing-inner-race shim/collar/hub stack;
moving a collar must not leave the bearing axially unsupported.

### R2-M6 — drive backplate and guards cut into structural/actuator parts (4/5/4/3)

- PitchDriveBackplate / RotatingTurretPlate: 1,098mm³.
- PitchDriveBackplate / YokeFootAngle_2: 963mm³.
- PitchBeltGuardEnvelope / PitchMotorCandidate: 6,498mm³.
- Each yaw cage post crosses the yaw guard: 157.771mm³.

The backplate currently begins below the turret and lies in the foot-angle volume.
Move its interface or provide actual matching relief and a bolted support angle;
do not pretend overlap provides attachment. Guards may be packaging envelopes, but
their present sheets cannot be cut and installed. Provide deliberate motor/body
openings or move the enclosure boundary and retain coverage of belts and pinch
points. Recheck access to motor plugs and brake fasteners after the change.

### R2-M7 — full verification covers too few interfaces (4/5/4/5)

The existing full `verify()` asserts four stub/rail shapes do not intersect the two
tubes. All eight checks pass while the collisions above remain. Shape validity and
ratio multiplication also pass. Add a categorized collision report across parts,
with explicit exclusions only for intentionally overlapping belt pitch-ring/pulley
envelopes and wire exclusion zones. Do not blanket-ignore all purchased envelopes:
a bearing inside a pulley or a motor through a guard is still an actionable issue.

Maintain explicit expected-contact pairs and nonintersection pairs for mechanical
parts and check at least endpoint/intermediate angular poses. A passed neutral
pose cannot establish the full yaw/pitch motion envelope. Bolt-hole alignment,
bearing-seat engagement and tool access need additional checks beyond booleans.

## Other observations

- (S2/L4/P3/C3) Two small catcher strut/top-clamp overlaps remain, 21.868mm³ per
  strut, after the shortened root mounting. They are now much smaller than the old
  idler clash, but distinct printed parts must not occupy the same volume. Inspect
  the round strut beginning near its foot and relieve/reposition the contact geometry.
- (S3/L4/P3/C3) Yaw belt pitch envelopes intersect two drive spacers (47.567mm³
  for stage 2; one stage-1 interference 104.415mm³). The intentionally complete
  pulley rings may overstate some arcs; test against the actual exposed tangent
  spans and actual wrap before deciding which posts to move. This is not included
  among unequivocal solid structural clashes above.
- (S2/L3/P3/C3) The shoe strip width is now 6mm on top/bottom rather than the old
  5mm. The recessed 4.2mm counterbore leaves only 0.9mm side ligaments locally.
  Verify acetal fastener preload and strip fracture under pullout and single-pad
  edge loading. Do not torque M2 screws as though these are metal bracket ears.
- (S2/L3/P3/C2) Two screws per strip and opposing access holes are useful, but the
  30mm guide section is heavily perforated. The tube-only bending model does not
  resolve local hole net-section fatigue. Document deburring and inspect guide
  hole edges after initial load cycles.
- (S3/L4/P4/C4) Belt clamp, end stops, actuator anchorage and claw tendon/spring
  reaction details still require closure. Those were already explicit design gates;
  they are not counted again as newly discovered bugs. Root owns the in-progress
  servo mount work, so this snapshot does not rate that unfinished update.

## Independent mass and geometry checks

The fresh headless build reproduces 219 solid-bearing objects and pitch/yaw ratios
8:1 and 6:1. Four timing-belt compounds each contain four solids, deliberately;
all other modeled objects in this snapshot have one solid. Root tube/stub separation
is valid. The following numbers are geometry/allowance screens, not weighed masses:

- Added stationary parts: 6.0313kg.
- Added yaw-only parts: 4.3109kg.
- Added pitch parts: 1.1238kg, including extension drive envelopes/plate.
- Added yaw-only inertia about yaw: 0.094646kg·m².

The engineering yaw allowance 4.5kg at radius 0.16m gives 0.1152kg·m², above this
0.094646 screen by about 22%. This is a reasonable provisional allowance for the
modeled yaw group, not certification: unmodeled bolts/hubs/guards and revised
collision-free geometry can consume it. Imported telescope, shoes, hardware and
claw are explicitly excluded from these CAD totals and must not be omitted from
the separate boom dynamics. Do not present 4.31kg as the complete yaw-carried mass.
The model's overlapping/doubled braces also slightly inflate stationary mass until
corrected; removal is a geometry fix rather than a meaningful speed optimization.

## Required next design pass

1. Close the yaw cage/output-pulley envelope and pitch jackshaft bearing/pulley stack.
2. Correct brace stacks, through-bolt heights, column sleeve/shaft conflict and all
   matching mounting-hole patterns.
3. Seat every bearing across its required radial support width and define the axial
   race/shaft retention paths.
4. Resolve backplate/turret/guard/strut intersections, then run full categorized
   collision checks over meaningful poses.
5. Recompute moving mass/inertia and BOM before sourcing motors or framing this as
   full CAD ready for manufacturing. Continue isolated low-cost subsystem trials.

No physical test is needed to decide whether two solid parts may occupy the same
space. Fix these desk issues first. Physical tests then determine guide friction,
creep, compliance, retention, backlash, heat and durability of an assembled mechanism.
