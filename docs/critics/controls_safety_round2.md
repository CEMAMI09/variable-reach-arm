# Independent adversarial review: dynamics, controls, embedded, electronics, safety — round 2

Review date: 2026-09-07. This is a separate review of corrections made after
`controls_safety_round1.md`. The critic did not edit the implementation. Full CAD
is undergoing its own review and is not scored here.

## Verdict

**The specific equation, procedural-documentation and embedded-reset defects from
round 1 are corrected. No new major defect was found in those revised sections.**
The production receive/dispatch path now has meaningful direct tests. This improves
confidence in the current permanently disabled diagnostic firmware.

The complete powered robot still has unresolved engineering implementation work:
exact actuator/transmission selection, actual stop/dump/retention circuitry and
real motor/feedback/homing/motion adapters. Those gates were already disclosed and
remain. Correcting these reviewed defects does not establish high-speed readiness
or mean the remaining uncertainties are mostly physical-test-only.

## Independent verification performed

- Ran all **13 engineering tests**: pass, including energy balance, Cartesian guide
  reactions, guide-load bounds, inertia integration and BOM arithmetic.
- Ran all **8 Python firmware/host tests**, including the exact C++/Python wire
  comparison: pass, no skipped cross-language check.
- Ran the updated native executable: **production dispatcher, protocol,
  qualification lock and controller tests passed**. Source inspection confirms
  `main.cpp` and the native tests use the same `CommandReceiver`; no test-only
  arm/qualification bypass was added. The executable's modification time follows
  the dispatcher source update. This critic did not independently rebuild Teensy;
  the root agent reports its successful 2.82 s target rebuild and no flashing.
- Independently tested **300 random combined-motion states**, with extension in
  0–0.5 m, pitch/yaw spanning positive and negative angles, simultaneous signed
  yaw/pitch/extension velocity and acceleration, and signed external tip loads in
  both transverse planes. Differentiated world Cartesian positions at ±0.0001 s,
  projected acceleration plus gravity onto the instantaneous pitch/yaw tangents,
  and used two-point spatial Gaussian integration for each uniform rod. The
  maximum discrepancy between independent front/rear reactions and `guide_load`
  was **5.62 × 10^-7 N**. This calculation does not reuse the implementation's
  spherical acceleration formula.
- Read the rewritten bring-up, integration and print-guide procedures, electrical
  figures, reset semantics and actual production dispatcher tests.

No test connected a motor bus, flashed a board or moved hardware.

## Round-one findings disposition

### DYN-01 — closed

The pitch-plane yaw coupling is now positive in `guide_load`, matching the
Cartesian projection and inverse dynamics. The prior copied-expression regression
was replaced by a world-position finite-difference test of both transverse planes.
The raised-boom regression also explicitly checks that steady yaw increases the
upward guide reaction. The independent 300-state test provides additional sign and
coupling coverage, including below-horizontal pitch.

At 0.5 m extension, 45° pitch and 2 rad/s yaw, correct front/rear reactions remain
approximately **+14.6401 / −9.5840 N**. The triangle envelope did not require an
increase because it already bounded the coupling magnitude. This finding is fixed
by an equation correction and independent evidence, not by loosening a tolerance.

### SAFE-01 — closed for the inspected operational documents

Bring-up now explicitly limits work to passive mechanical checks, offline analysis
and logic-only diagnostics. It states that homing/motor adapters are absent and the
qualification bit must not be removed to follow old jog instructions. Integration
requires containment for autonomous/high-speed work and distinguishes future
release conditions from actions available now. The print guide uses square
aluminum stock and an actual three-finger claw, excludes net substitution, and calls
the meshes fit prototypes. It correctly refuses to equate a 4 mm TPU pad with a
measured 25 mm stopping stroke.

This addresses the contradictory entry-point instructions. It does not verify the
physical guard, print strength or CAD assembly, which are outside this round's scope.

### ELEC-01 — closed

Electrical prose now matches the current generated screen: 91.74 W mechanical,
231.14 W assumed bus power, 9.63 A at 24 V, 12.04 A arithmetic allowance at 25%
reserve, 8.14 J regeneration and approximately 63.6 V isolated capacitor rise.
Losses remain clearly assumed. The 10 A wire-resistance example remains explicitly
an illustrative calculation, not the whole-system design current or an ampacity
approval. The 14.6 A PSU still needs actual load/ambient/derating verification.

### TEST-01 — closed for the current locked receive/dispatch path

`CommandReceiver` receives bytes in the same path used by the application loop.
Tests now cover valid NOP arrival, duplicate/backward/half-range sequence rejection,
CRC/semantic errors, enable/clear, unsupported home/trajectory/claw commands,
out-of-range and discarded disarmed setpoints, old-sequence disable, reset-link,
sequence rollover, frame truncation/dropped-byte recovery and reboot.

Read-only safety snapshots show invalid/replayed packets do not refresh host
arrival time. Every dispatch helper invocation asserts that the production
qualification fault and disabled motion remain. No fake safety implementation is
substituted. These tests do not claim to exercise enabled watchdog/limit behavior;
there is intentionally no enabled state reachable in the current production code.

### CTRL-01 — reset/stale-target defect closed; feedback age remains an explicit gate

Controller reset now clears targets and integrators, invalidates target and
measurement state, makes measurements NaN and zeros output. Telemetry publishes
missing target sentinels when a target is invalid. A new measurement alone cannot
replay a pre-reset target; that behavior is directly tested. Invalid targets also
reset the scaffold instead of quietly retaining an old command.

Actual sample timestamps and a measured-pose handoff at a future arm transition
remain absent. The header and procedures acknowledge this. They must be implemented
with the real feedback adapter; the validity booleans alone are not sample-age checks.

## Remaining issues and disposition

No additional corrective defect is raised in this round. The following previous
gates retain their priority; they have not disappeared because diagnostic tests pass.
Severity/likelihood/performance impact/cost-of-fixing-later are each on a 1–5 scale.

- **GATE-01, exact powered actuators/transmissions:** 4/5/5/5. The 2 Nm
  holding-torque references do not establish the required running torque at the
  proposed reductions; extension torque at 1000 rpm remains unqualified. Exact
  curves, ratio choice, load path and operating envelope are desk selection tasks.
  Thermal, backlash and loaded speed then need measurement. Complete-machine motor
  purchases should not be frozen from the current reference basket.
- **GATE-02, physical stop/dump/retention and wiring:** 5/4/5/5. Exact schematic,
  DC cutoff, independent enable/watchdog, clamp tolerance/pulse rating and pitch
  retention implementation remain required before their relevant powered scope.
  A horizontal restrained rig avoids the rotating gravity-loaded pitch subsystem,
  but does not remove its own cutoff/fusing/guarding requirements.
- **GATE-03, actual motion execution:** 5/5/5/4. No real motor/feedback/homing or
  deterministic motion adapter is implemented. The permanent lock correctly
  contains this. Implement and qualify one selected axis before all-axis integration.
- **LINK-01, enabled link freshness contract:** 3/2/3/3. Increasing board timestamps
  received from an old USB queue can still look newly arrived. Session/boot identity,
  acknowledgements and execution deadlines remain a future enabled-protocol gate,
  accurately stated in the protocol document. It is not a current lock bypass.
- **COST-01, budget and exact rig choices:** 2/4/3/3. The separate $474.11 rig
  basket is close to the $500 ceiling, mainly unquoted, and requires exact drive
  selection plus an RP2040 firmware port if that MCU is purchased. It is not the
  complete three-axis robot. Keep scope, current quotes and owned parts explicit.

These are finite, specific next engineering tasks. Repeating abstract safety
checklists or adding unneeded sensors would not close them.

## Updated scores and prototype readiness

- **Dynamics: 7/10**, up from 6. The rigid-body equations and guide reactions now
  withstand independent checks. Below 9 because exact component mass/offsets,
  running actuator envelopes and flexible/catch behavior remain unresolved. Exact
  selections/model updates can improve this before prototyping; friction, stiffness,
  impact stroke and damping need physical evidence.
- **Controls: 3/10 for powered robot control**, unchanged. Reset behavior is better,
  but there is still no implemented physical trajectory executor or tuned plant.
  Driver interface, feedback age, homing and limit execution are desk work before
  safe restrained tuning. No score increase is earned simply by remaining disabled.
- **Embedded: 8/10 for the current logic-diagnostic boundary; 3/10 for powered robot
  firmware.** The production dispatcher is now directly tested and stale targets
  are invalidated. Diagnostics need on-board timing/fault evidence to reach 9;
  motion firmware still needs the actual adapters and execution state machine.
- **Electronics: 4/10**, unchanged. Numerical consistency improved. Exact circuit,
  parts and interfaces remain the larger task; waveforms, EMI and heating follow
  physical build and measurement.
- **Safety and reliability: 4/10 overall; 8/10 for the software-only qualification
  boundary.** Conflicting instructions are corrected and disabled behavior has
  better evidence. Actual stop circuits, load retention and measured stop response
  determine system readiness. A circuit review can precede a prototype; physical
  fault injection is still indispensable.

Supported now: passive fit/travel/retention fixtures, contained low-energy
three-claw material tests, offline simulations and logic-only firmware diagnostics
with motor power physically disconnected. Supported next after the exact relevant
gates: a guarded horizontal single-axis extension rig, initially below proposed
bench caps. Not ready: freely rotating gravity-loaded arm, autonomous catching,
contact-triggered powered claw closure or throwing.

The repaired sections do not justify another identical desk critique cycle absent
new design changes. Engineering effort should now close the named selections and
interfaces, and then measure the restrained mechanism. The overall user-requested
manufacturing-ready/high-speed design has not yet met its terminal acceptance
criteria; this report does not silently lower them.
