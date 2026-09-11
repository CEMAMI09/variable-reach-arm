# College V1 and fair-version budget — 8 September 2026

**Superseded V1 cost/classification:** use `college_v1_named_bom.md` and the current
`engineering/bom_college_v1.csv`. The new named print-first basket is $368.47 parts,
$446.55 with assumed shipping/tax, or $513.53 including optional repair reserve.
The $705.64 V1 allowance and metal-only cap/pulley guidance below are historical.

## Answer

A compact, slow, mostly printed robot with powered yaw, pitch, telescope and a real
three-finger claw has a current planning basket of **$547.86 in parts; $705.64
including $65.74 shipping/tax allowance and $92.04 redesign reserve**. Treat roughly
$650–800 as an initial planning range, not a quote or guaranteed ceiling. Exact
CAD, actuator selection and supplier prices can move it outside that range.
This is a new compact concept, not the current full-size CAD converted to plastic.

The current higher-performance full-machine/fair-direction basket is **$1,131.30
parts; $1,457.12 with allowances**. It includes $100 for stereo cameras/accessories,
but its actuator and voltage choices still need revision. It is not an approved
shopping list or a final guaranteed cost to achieve high-speed catching.

The restrained horizontal telescope/claw rig remains **$497.29 with allowances**.
It demonstrates extension, sensing and claw tests, but has no powered yaw/pitch.
These are three alternative initial baskets, not three costs to add together.

## What V1 would demonstrate

Proposed compact geometry: approximately 350–550 mm reach, 200 mm telescope stroke
and a 350 mm shoulder height. Initial design targets are slow motion, a lightweight
foam ball no more than 20 g, coordinated movement, homing, repeatable extension,
and commanded gripping/release. These are proposed limits to qualify, not approved
powered operating settings. No camera is included: vision tracking, autonomous
interception and throwing are later capabilities, not claims for this V1 budget.
Adding the present stereo allowance adds $100 parts, approximately $129 with the
same allowances. A single camera could support a constrained-plane experiment;
it does not replace general 3D stereo without a different measurement method.

## Print versus buy

Print the compact shoulder/yoke as a ribbed box structure, motor brackets, bearing
carriers, large pulley webs with metal hubs, palm, rigid fingers, guards, cable
supports and fit fixtures. Use through-bolts and metal compression sleeves where
preload would creep through plastic. Printed bearing seats need retention and
replaceable fit inserts. These are redesign tasks, not permission to print the
existing 3 mm aluminum cheek geometry unchanged.

Printed inner/outer boom shells are reasonable to investigate for the SHORT V1.
Use longitudinal load paths, real low-friction wear strips, replaceable joints
and mechanical retention. A short tube that fits the printer as one part is much
better than several thin butt-jointed sections. Printer bed size is still unknown.
Keep aluminum tubes as the preferred fallback if straightness, binding or joints
consume more time and filament than the tube stock saves.

Keep steel shafts, screws, nuts, pins, bearings, springs, bearing caps, belt clamp
caps and small drive pulleys. Keep a rigid anchored base; plywood is acceptable
for a low-energy compact prototype. Use bought foam/rubber pads instead of buying
a whole TPU spool solely for a few pads. This V1 budget buys two PETG spools and
allows rework; it does not assume free filament. Nylon and carbon-filled filament
are not default upgrades. Printed failure modes include creep, layer separation,
hole ovalization, belt hub slip and guide roughness.

## Why printing alone is not a $1,000 saving

The full-size aluminum tube pair is only $48.10 of the current parts basket.
Two printed 3 mm-wall shells of the same outside sizes have an ideal bending
stiffness about 18–19 times lower using a favorable 2.31 GPa PETG XY coupon modulus.
That comparison excludes joints, creep, layer-direction effects and guide play.
They weigh only about 13–14% less per metre in this ideal solid-wall calculation.
A shorter span improves deflection strongly, which is why a compact V1 deserves
its own architecture rather than the original long arm in plastic.

Reproduce with `python -m engineering.v1_print_trade`. PETG source:
https://polymaker.com/wp-content/uploads/lana-downloads/TDS_Polymaker_PETG_V2.0_2025-11-17.pdf
Coupon values are not a printed structural design allowable.

The major V1 savings come from reduced reach, smaller motors/drives, simpler
support structure and postponed high-speed perception. Purchased low-cost NEMA17
motors are a price reference only; $9.62 each was observed on 8 September 2026:
https://www.omc-stepperonline.com/nema-17-bipolar-59ncm-84oz-in-2a-42x48mm-4-wires-w-1m-cable-connector-17hs19-2004s1
Their 0.59 Nm holding rating is not running torque. The driver allowance is $20 per
axis; the cheaper DM320T has only about 1.56 A RMS and cannot be credited with full
2 A motor torque. Output feedback, independent power interruption, regeneration
protection and pitch power-loss restraint remain budgeted.

## Avoid spending twice

ESP32/host tooling, calibration procedures, claw test results, measurement scripts,
fasteners and some power/interface hardware may transfer to the fair version.
Do not assume compact motors, printed booms, brake, belts or a 120 W supply will
transfer to the larger robot. The future fair budget is a full basket; actual
incremental upgrade cost requires subtracting only compatible reused components.
Borrowing school printer access, camera equipment or suitable hardware can lower
cash cost, but no unconfirmed loans are counted. Printer purchase, bench, ordinary
tools and host computer are excluded. Unknown owned servo is not credited yet.

## Work completed on the full design in this pass

Both repository GIFs were regenerated from the complete 381-part CAD. The model
now includes raised/windowed shoulder supports, rear telescope belt anchor and
stop hardware, a connected extension motor bracket, supported front idler and
claw spring/stop/tendon allowances. Five sampled full-robot poses had no unresolved
solid intersections above 0.5 mm3, and animation placements agreed with a separately
built pose for all 381 parts. This is sampled evidence, not continuous collision
validation. All 62 host/engineering tests pass after mass updates.

At 0.70/0.95/1.20 m reach the updated pitch inertia is approximately
0.2555/0.3877/0.5967 kg m2; target-motion pitch torque bounds are
5.66/9.04/13.05 Nm. Current motor/reduction choices do not qualify those targets.
The smooth 5 mm stop-pin screen was updated to match the actual CAD and assumes
single-pin first contact; pad stroke and impact pulse still require measurement.

## What still requires design, and what requires hardware

Desk work: compact V1 CAD and sizing; final fair drive ratio/voltage selection;
complete claw equalizer/servo horn; complete cable/guard/brake envelopes and swept
collision checks; supplier-specific fits and assembly drawings; ESP32 port.
The actual servo and ESP32 model are still needed for their final interfaces.

Prototype work: printed joint/guide fit, tube straightness, collar and belt-clamp
slip, stopping stroke/force, spring preload, servo current/closure time, motor
running torque/temperature and repeatability. None can be established from a GIF.

Next priorities are: choose the compact dimensional baseline; complete its
motor/reduction and pitch-restraint sizing; build its print-oriented CAD; qualify
telescope and claw on a restrained rig; then integrate yaw/pitch and measured
motion before adding autonomous ball interception.
