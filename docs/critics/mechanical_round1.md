# Independent mechanical / CAD / manufacturing critic — round 1

Review date: 2026-09-07. Scope: current Rev B telescope/claw source, exported studies,
engineering parameters/results/BOM, and original build/print guidance. This review
did not design or edit those main files. User requirement: genuine finger/claw
grabber with positive retention; no net. No live FreeCAD instance was touched.

## Verdict

Not ready to manufacture the complete robot or buy the three actuator systems.
The four explicitly unpowered fit parts can support dimensional experiments, subject
to the clamp/collision corrections below. The current CAD is an incomplete mechanism
study, and its own NOT RELEASED labels correctly acknowledge many omissions. A label
does not make those omissions disappear, but they are distinguished below from actual
calculation/geometry errors. Restrained hand-actuated tube and gripper experiments
are a useful next scope; high-speed powered extension, catch and throw are not approved.

Scores at this snapshot: mechanical design 4/10; CAD/manufacturing completeness 3/10;
3D-print design 5/10; cost efficiency against the requested complete $500 machine 3/10.
Scores describe the integrated design, not the usefulness of its investigation tools.

Severity S, likelihood L, performance impact P and cost of fixing later C use 1–5,
with 5 worst. Priority product is S×L×P×C. Likelihood here is likelihood of failure
if the present study were fabricated/operated as a completed design, not measured
failure frequency.

## Major findings

### M1 — actual collision in the fully retracted telescope (5,5,5,4; 500)

`build_review_telescope.py` puts the top catcher collar at x=538–560mm when s=0.
The front idler pitch-envelope center is x=545mm, and the belt lower run extends
to x=545mm. Independent FreeCAD 1.1.3 booleans give these positive intersections:

- BeltInsideEnvelope / CatcherClamp_top: 86.94mm³.
- IdlerPulleyPitchEnvelope / CatcherClamp_top: 179.24444mm³.

These occur for all four checked claw angles (-10, 0, 10, 20 degrees). Therefore
the nominal zero-stroke CAD cannot exist physically even before adding real idler
flanges and bearings. Current `verify` tests the clamp only against inner/outer
tubes, so its valid result misses the issue. Change the nose/clamp/idler layout,
then sweep every moving mount against the actual purchased drive envelopes. A
clearance cut is acceptable only if the remaining top clamp and load path are sized.
Do not merely hide the overlapping part or redefine zero travel after building.

### M2 — flat-guide friction uses the wrong normal-force combination (4,5,4,4; 320)

`guide_load` and `guide_bound` use hypot(pitch_reaction,yaw_reaction) for friction.
These square tubes have orthogonal flat shoe faces, not one bearing face normal to
the resultant. Separate face normals add: N=|Rp_front|+|Ry_front|+|Rp_rear|+
|Ry_rear|+preload. The current expression can understate the reaction contribution
by up to sqrt(2) in simultaneous pitch/yaw loading. Replace it and independently
check both single-plane and equal-plane cases. Account for the small drive-line
eccentricity if needed; at max stroke 2×0.15×0.0143/0.19≈0.023, so that alone does
not justify claiming this telescope self-locks, but it should not be ignored in a
final friction margin.

Pressure area is also inconsistent: JSON assumes one 30×9mm patch, whereas CAD
has two 30×5mm strips on each top/bottom face and one 30×18mm side pad. Use each
actual loaded face area and unequal load-sharing sensitivity. One narrow strip
may take essentially the full reaction under skew, doubling nominal face pressure.

### M3 — split collar bottoms out before establishing grip (4,5,4,3; 240)

`split_collar` has a bore 0.4mm larger than the tube and two mating surfaces both at
z=0. There is no designed split gap or compression liner. Tightening four M4 bolts
first mates the flange faces; positive grip would rely on unspecified bending of
the printed flange. Add controlled mating-face relief or a specified conformable
liner with a measurable remaining clamp gap and metal compression-limit strategy.
Prove axial pullout and rotational slip without crushing the 1.59mm tube wall.
Do not substitute high screw torque for an intentional clamp geometry.

### M4 — central extension mechanism and support load paths remain unclosed (5,5,5,5; 625)

Declared gate, not a falsely claimed release: the rear carriage/pad fasteners, belt
end clamp, tensioning adjustment, front pulley bearings/bracket, motor bracket,
mechanical end stops, root trunnion attachment and pitch/yaw frames/reductions are
not detailed. Current trunnions float outside the tube; current pads float in the
annulus. An open belt line with no anchorage is not a bidirectional extension drive.
The 4.76mm annular gap must contain the actual belt tooth/back thickness and clamp
through the full travel, not just a 1.38mm belt envelope.

Close the restrained extension-rig mechanism first: removable rear cartridge with
positive axial retention, belt clamp that is inspectable before insertion, adjustable
front wear carriers, purchased pulley data, both stop contact paths, and a numbered
assembly sequence. Add full assembly collision checks and fastener access envelopes.
Do not release the rotational assembly until the trunnion-to-tube torque path, hub
grip, brake and independent drop restraint have drawings and load checks.

### M5 — claw is not yet an actuated grabber (4,5,5,4; 400)

Declared gate: there are three real separate links and steel pin envelopes, but no
spring seats/reaction legs, physical open/closed stops, tendon routing/equalizer,
servo mounting or demonstrated release stroke. A servo envelope provides none of
these. A rigid equal tendon splitter may prevent one finger accommodating an off-center
ball unless slack/compliance is intentional. Route each tendon with a controlled
moment arm across travel; specify spring preload, force, overtravel, pinch points
and the power-loss retention/release behavior.

The current illustrative closure time is 104ms versus 15ms for a ball crossing
60mm at 4m/s. This is honestly disclosed and is a fundamental architecture constraint,
not something software timestamps alone fix. Test prepositioned claws and compliant
contact retention before pursuing faster actuation. A net is not proposed. The
4mm TPU palm cannot be credited with 25mm stopping stroke without force–displacement
testing and a model of its backing, support ears and replaceable foam.

### M6 — declared inertia/actuator/impact envelope does not support requested speed (5,4,5,5; 500)

The variable-inertia equations correctly include translated full-length tube mass and
I-dot coupling. The snapshot shows max-reach pitch demand 10.25Nm and yaw 7.94Nm
before impact; 1.5 torque margin requires 2.14/2.21Nm motor running torque at
160/120rpm. These exceed the candidate 2Nm holding labels, and extension requires
about 0.565Nm including margin at 1000rpm before the friction correction. The
model appropriately refuses approval. This remains a desk-design procurement gate:
obtain actual curves and select speed-dependent operating limits or a different
motor/ratio. It is not merely an unknown needing an entire robot prototype.

The unmatched 32N transverse catch adds 38.4Nm at 1.2m; the illustrative 12mm shaft
screen reports local-allowance yield factor ~0.47 for combined load. Do not approve
this event by calling foam safe. Bound the permitted relative velocity and approach
direction, qualify claw compliance, and size the complete transmission against the
accepted event. Physical impact tests should begin with an isolated restrained claw.

### M7 — distal mass allowance has no assembly budget (3,4,4,4; 192)

Independent CAD volumes: three claws 33.204cm³, palm 22.835cm³, palm pad 11.929cm³,
two collars 17.794cm³, two struts 5.478cm³: total 91.24cm³. Typical solid-density
conversion near 1.2–1.3g/cm³ gives about 113g before servo, steel pins, four M4
bolts/nuts, other screws, springs, tendons, foam and wiring. This is an envelope
screen, not a claim that a sparse print weighs its solid volume. The 130g allowance
is tight and must be supported by slicer plus purchased-hardware mass accounting.
The printed parts are mostly thin sections, so infill savings are smaller than
for thick blocks. Weigh the complete distal assembly and update COM and inertia.
Remove flange/annulus material by load-path-aware ribs if needed, not all-solid
infill or a heavier servo. Separate ball seating COM from nominal mouth plane.

### M8 — contradictory fabrication guidance is still active (4,4,4,4; 256)

Original `cad/drawings/print_guide.md` still describes the older CF round-tube build,
allows printed hinge pins, says the STLs form a real prototype fabrication cut-list,
and treats shields as optional; `requirements.md` still permits cradle/net wording.
This conflicts with current square tubes, steel pivots, no-net user requirement,
containment and NOT RELEASED states. Supersede the old cut-list prominently and
quarantine old outputs as legacy examples. A user must not accidentally order the
old tube sizes or believe the new review approved the old full-robot STLs.

### M9 — budget has no feasible complete-machine architecture (3,5,5,5; 375)

The new BOM correctly totals $1,077.30 before shipping/tax/reserve and $1,387.56
with disclosed allowances, nearly 2.8 times the $500 maximum. This is honest
accounting, not cost optimization completion. The basic extension-rig group alone
is $336.10 before safety, claw and allowances. The overrun cannot be closed by
printing shafts or deleting brake/containment. Determine owned parts and obtain
exact alternate motor/driver quotes; compare borrowed electronics and a manually
operated tube/claw phase. Keep each scope's costs explicit. No claim of a complete
safe high-speed $300–500 machine is defensible at this snapshot.

## Minor findings and improvements

- (S2,L4,P3,C2) Claw clevis gap is 12mm while the finger is 8mm thick, leaving 4mm
  axial space. Specify two 2mm thrust spacers or the intended alternative, actual
  M3 shoulder length, washer/nut stack and clearance; do not clamp rotating plastic
  tightly with the retaining nut. The 3.3mm printed pivot bore needs coupon/reaming
  validation against 3mm metal pin wear and backlash.
- (S2,L3,P3,C3) Two round 7mm printed catcher struts and annular palm leave mount
  compliance outside the tube-only deflection model. Check asymmetric contact and
  torsion, fillet strut-foot transitions, and give a reproducible lateral-load test.
- (S2,L4,P2,C2) Guide fit coupon has ideal square external corners. Real extrusion
  bore radii/straightness may reject it before face-clearance conclusions are useful.
  Relieve corners based on measured stock and document which coupon dimension tests
  face fit versus corner fit.
- (S2,L3,P2,C2) Nominal square-pad top/bottom preload needs adjustment and lock
  features. Overconstrained tightening is a credible jam source even when all
  nominal CAD shapes do not intersect; record pull force at many strokes and orientations.
- (S2,L4,P3,C3) Use a retained removable cover over the external return belt and
  avoid routing distal wiring through the same top corridor without a bend-radius
  and full-stroke harness trial. The harness belongs in the moving mass budget.
- (S2,L3,P2,C2) `verify` should assert one solid per manufactured component, not
  merely nonempty `Solids`. Independent spot checks currently found one solid in
  every one of the 33 objects, but the invariant should survive future edits.

## Independent checks and limitations

FreeCADCmd 1.1.3 built source at four claw angles, checked one solid per object,
and computed boolean intersections for claws/palm/pad/servo and drive versus
catcher mounts. No tested claw–palm/pad/servo collision was found. This does not
cover undefined springs/tendons/hardware or the complete yaw/pitch workspace.
Tube overlap independently follows 520-(−220+s)=740−s mm at the relevant interval,
giving 240mm at max stroke; guide spacing 490−(−200+s)=690−s mm gives 190mm.
These are credible improvements over unsupported guide placement, but retention
is still needed. No finite-element or supplier-material certification is claimed.

## Revision priorities and prototype boundary

1. Correct full-retraction belt/idler collision, collar clamping gap, square-guide
   friction/pressure model and contradictory fabrication status.
2. Finish an inspectable extension drive, pad cartridge and hard-stop load path.
3. Complete the claw spring/tendon/stop/servo mechanism and hardware stack.
4. Select motors only from torque-speed/current/thermal data at actual bus voltage;
   reconcile moving masses and price a buildable scope.
5. Perform unpowered dimensional/pull-force tests, restrained claw drop/retention
   tests, then restrained low-energy powered extension after hardware safety review.

Desk-solvable items are mechanism closure, drawings, dimensions, conflicts, motor
data, cost and mathematical errors. Physical unknowns are actual guide friction,
wear, extrusion straightness, print strength/creep, assembly stiffness, mass,
claw stopping stroke/rebound, motor heating and harness life. The current major
unknowns are not predominantly physical-test unknowns; several major design
decisions still require desk work before buying the complete machine.
