# Engineering review in progress — 2026-09-07

This is an ongoing repository redesign, not a completed design release or final scorecard.

## Accepted user clarification

The end effector must be a real grabber with claws/fingers and positive grasp/retention.
**No net.** The early hoop/net study is superseded. Current work investigates three
identical single-joint claws, compliant pads, metal pins, spring closing, and one small
actuator for opening/release. Active closure is an alternative to compare using measured
closing time, holding force, power-loss behavior and distal mass. Neither is qualified yet.

This overrides any earlier net/funnel recommendation. Passive impact stroke cannot be
credited from a net; use measured claw/foam contact displacement and signed radial
velocity matching. A25mm compliant contact stroke is a screening assumption, not a
measured capability. No autonomous throw or high-speed catch is approved.

## Review continuity

Independent mechanical, software and controls/safety reviews are now recorded in
`docs/critics/`. Software round2 verifies the timing/stereo/default-configuration
fixes and all45 host tests. Mechanical round2 found actual shoulder-drive and
mounting collisions; its corrective pass and full travel audit are in progress.
Do not substitute shape validity for those reviews or manufacturing approval.

## Existing changes awaiting integration

- RevB shared SI geometry and changing-inertia screening model.
- FreeCAD telescope studies at0/250/500mm stroke plus unpowered fit prints.
- Strict IK/reach; timestamp and actual quintic-limit checks; improved ideal simulation.
- Firmware v2 wide-angle protocol and explicit unqualified-hardware lock.
- Original BOM arithmetic is$701 before reserve, not its stated$449.

The complete base/yaw/pitch/telescope/claw assembly is generated separately from
the telescope study. The original32-object CAD is preserved. Telescope exports
now restore the active full document. The servo has a nominal removable cradle,
but its actual SKU and tendon mechanism remain unqualified.

Owned inventory is recorded in `engineering/owned_inventory.json`: unknown servo,
ESP32, soldering station, DMM and computers; no camera/PSU or substantial mechanical
stock. Current firmware targets Teensy; owning an ESP32 does not make it compatible.

Root coordinates and dimensions remain provisional until rear-boom swept clearance,
telescope belt anchorage/tensioning/stops, claw actuation, actuator curves and
electronics close. These are desk-design gaps, not merely physical-test unknowns.

Latest root verification:62 host/engineering tests and8 cross-language protocol
tests pass. Full neutral assembly has235 valid solid objects and zero unresolved
modeled-solid overlaps. The separate850mm raised-shoulder study clears sampled
upper-pitch poses but adds1.125kg of yaw-carried mass; it is not selected as optimal.
The default full-assembly planner now fails closed; explicit ideal-boom simulation
cannot pass the geometry dispatch gate. Desired70-degree requirements are retained.

The manufacturer23E1K-20 curve is now visually inspected:48V/5A pull-out data,
not24V or continuous thermal qualification. The reproducible ratio comparison
supports investigating pitch16:1/yaw12:1; it does not release motors for purchase.

## 8 September continuation

Current full baseline is the 850 mm raised/windowed stiffened shoulder, with 381 modeled parts. Five sampled final poses pass the broad solid-intersection screen; the unqualified workspace gate remains because sampling does not prove continuous or cable clearance. New telescope drive details and claw actuation documents distinguish implemented geometry from unresolved supplier/servo interfaces. Both full-CAD GIFs have been regenerated.

The user now accepts lower performance and more printing for a college V1 before a fair version. `docs/college_v1_plan.md` and `engineering/bom_college_v1.csv` define a separate compact concept and cost basket; this does not change the current full CAD or enable powered motion. Current costs with allowances: V1 $705.64, restrained rig $497.29, full machine $1457.12.
