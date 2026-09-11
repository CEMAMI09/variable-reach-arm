# Independent adversarial review: dynamics, controls, embedded, electronics, safety — round 1

Review date: 2026-09-07. This critic did not implement the reviewed design. Scope is
the revised sizing model, its tests, firmware, host serial interface, operational
documents and electrical/budget boundary. The specified end effector is an active
three-finger claw, **not a net**. Findings describe the first-pass snapshot; later
corrections should be recorded separately rather than erasing this evidence.

## Verdict and test evidence

**The current repository is appropriate for offline analysis, logic-only protocol
experiments and passive mechanical prototypes. It is not ready for powered
autonomous catching, throwing or complete-machine purchasing.** The qualification
lock is correctly persistent and cannot be cleared through the exposed command
path. That is a useful safety property; it is not a working motor stop circuit.

I independently ran all eight host protocol tests, including the C++/Python exact
wire comparison, the available native protocol/controller executable, and all
twelve engineering tests. They passed. The native executable was supplied by the
implementation pass; this critic did not rebuild it. Passing tests did not establish
the sign of the guide-load equation: the equilibrium test repeated that error.

Checks independently supported by calculation:

- Tube mass integration and translating-body inertia give loaded I = 0.197392,
  0.330573 and 0.537335 kg m² at 0.70, 0.95 and 1.20 m mouth reach. Gravity pitch
  torque is 1.50731, 2.95049 and 4.39367 Nm at horizontal pitch. The 2.72× inertia
  change is real within the disclosed mass model.
- Euler–Lagrange equations from T = I(s)(p_dot² + cos²(p)y_dot²)/2 + m_s s_dot²/2
  confirm the inverse-dynamics signs, including **positive** I*y_dot²*sin(p)*cos(p)
  in pitch and negative centrifugal radial force. The energy-balance test is a useful
  independent conservation check.
- 36 teeth × 2 mm pitch gives 72 mm/revolution: 1.2 m/s needs 1000 rpm.
- 50 g at 4 m/s has 0.4 J relative kinetic energy. A genuine 25 mm stopping stroke
  gives 16 N average force; 32 N peak is an assumption, not a measured result.
- Current model output is 91.7394 W mechanical demand, 231.1375 W assumed bus power,
  9.6307 A at 24 V and 8.14194 J regenerative energy. An isolated 4700 µF bus rises
  from 24 V to 63.566 V if that full energy enters it. The equations and units agree.
- Current cash arithmetic is $1,387.56 complete-machine planning allowance versus
  $474.11 for the separate restrained-rig basket. The latter is not a $474 robot.

Severity, likelihood, impact and cost-of-fixing-later are each 1–5 below. Their
product orders attention but is not a formal safety risk assessment.

## Major findings requiring design/document correction

### DYN-01 — exact guide reaction uses the wrong yaw/pitch coupling sign

Location: `engineering/review_sizing.py:106`; replicated in
`tests/test_engineering_review.py:63`.

Problem: `kp = ap - wy*wy*sin(p)*cos(p)` subtracts the pitch-tangent component of
yaw centripetal acceleration. With +pitch upward, Cartesian position is
r[cos(p)cos(y), cos(p)sin(y), sin(p)]. At constant pitch and yaw speed, the horizontal
centripetal acceleration projected onto the upward pitch tangent is
**+r*wy²*sin(p)*cos(p)**. The rigid-body inverse dynamics already uses that sign.

Independent example: extension 0.5 m, pitch 45°, yaw speed 2 rad/s, zero other
rates/accelerations, no external tip load. Cartesian second differences at
±0.0001 s integrated over each moving member (10,000 slices for the inner tube)
give front/rear pitch-plane reactions **+14.64010 / −9.58396 N**. The current
function gives **+8.02500 / −4.91729 N**. It understates this front reaction by 45%.

Why it matters: friction and bearing/pad loads at a specific pose are incorrect.
The analytical `guide_bound` is still conservative because it bounds the absolute
coupling magnitude; the published envelope values do not need a pessimism increase
solely for this sign correction.

Recommendation: change the sign and replace the test's copied acceleration formula
with Cartesian differentiation/projection, exercising positive and negative pitch,
simultaneous extension and both transverse planes. Do not merely change both copied
minus signs and call the same test independent.

Severity 3; likelihood 5; impact 3; later cost 2; priority product 90.

### SAFE-01 — old operational instructions conflict with the actual safe boundary

Locations: `docs/integration.md:43` and its earlier assembly/integration steps;
`docs/bringup.md` throughout.

Problem: integration still calls the barrier optional and instructs latch operation,
IR alignment and carbon-fiber clamp handling. Bring-up tells the reader to home,
perform position steps and send manual serial setpoints although this build has no
qualified adapters or homing. The current safety document correctly prohibits this.

Why it matters: users commonly follow a bring-up checklist directly rather than
reading every new review document. A correct safety document elsewhere does not
cancel an unsafe or impossible operational checklist.

Recommendation: rewrite these entry-point procedures around passive fit checks and
logic-only firmware first. Require a physical barrier for autonomous/high-speed
work; link the exact powered-release gate before the first powered action. Remove
unsupported pin/latch instructions and obsolete material assumptions. Separate
future commissioning procedure from actions possible in this revision.

Severity 5; likelihood 3; impact 5; later cost 3; priority product 225.

### ELEC-01 — electrical demand prose is stale after the mechanical update

Location: `docs/electronics_review.md:61–82` and wiring's 8–10 A framing.

Problem: prose says 66.3 W mechanical, 192 W / 8.0 A bus, 6.07 J and 56.2 V;
current results are 91.74 W, 231.14 W / 9.63 A, 8.14 J and 63.57 V. Its 25%
current reserve is therefore 12.04 A, not 10.0 A. This does not automatically
disqualify the 14.6 A candidate PSU, but changes the usable derating margin.

Recommendation: update from the generated file; tie future verification to one
source or an explicit generated summary so a CAD mass change cannot silently leave
electrical selection prose behind. Continue calling all loss terms assumptions.
Do not select a fuse solely from this bus-current estimate.

Severity 3; likelihood 4; impact 3; later cost 3; priority product 108.

## Major unresolved implementation gates, already honestly disclosed

These are not requests to add unrelated sensors or random sophistication. They are
the minimum missing functions of the requested powered machine. Keeping motion
locked contains their immediate risk, but does not make them prototype-measurement
unknowns or completed engineering work.

### GATE-01 — high-speed actuator and transmission choices remain unqualified

Current target bounds require 2.42 Nm at 160 rpm pitch and 2.49 Nm at 120 rpm yaw
with the stated 1.5 torque margin. The 2 Nm holding-torque candidate cannot prove
either requirement, even before speed derating. Extension requires approximately
0.774 Nm available torque at 1000 rpm under the conservative bound; no exact motor
curve establishes that. The reduction shafts, hubs and brake are not fully resolved.

Before motor purchase freeze: select actual curve/current/voltage data, compare a
small useful set of ratios with reflected rotor inertia and running torque, and
either qualify the envelope or explicitly lower it. For a lower-speed extension
rig, select its exact single drive and the commanded motion interface. No need to
purchase three industrial servos merely to conduct the first useful guide test.

Severity 4; likelihood 5; impact 5; later cost 5; priority product 500.

### GATE-02 — stop, gravity retention, dump and wiring are architectures, not a circuit

The documents correctly require driver-side regenerative clamping, independent
hardware stopping, manual reset, fusing, logic voltage compatibility and pitch
restraint. The actual schematic, DC cutoff rating, clamp tolerance, driver enable
behavior, watchdog circuit and brake/load-restraint attachment remain unresolved.
`motors_disable_all()` is a stub and no independent on-target watchdog is configured.

Before powered assembly: resolve the actual driver and circuit rather than letting
a builder improvise from prose. A horizontal restrained extension rig removes the
gravity-loaded pitch subsystem; it still needs exact enable/fault wiring, an
appropriate clamp, fusing and guarding. A motor-side pitch brake alone cannot catch
the boom after a belt failure.

Severity 5; likelihood 4; impact 5; later cost 5; priority product 500.

### GATE-03 — hardware motion/controller remains an intentionally absent implementation

No real feedback, homing, timing-qualified step generation, current limits, following
error, acceleration/jerk execution or gripper control is implemented. Zero gains
are safer and more honest than fictitious tuning. They do not provide high-speed
trajectory tracking. A 1 kHz cooperative diagnostic loop is not a demonstrated
1 kHz feedback loop; driver inner-loop rate and MCU supervision rate must be explicit.

Before enabling: implement one specific adapter with timestamped measured feedback,
bounded motion execution and fault tests. Then implement extension-dependent
feedforward/gain scheduling as necessary from the model and measured plant. Avoid
unnecessary stacked integral controllers over an unidentified smart drive.

Severity 5; likelihood 5; impact 5; later cost 4; priority product 500.

## Minor issues and robustness improvements

### TEST-01 — native verification omits the actual command dispatcher

`test_native.cpp` verifies the codec, sequence comparator and safety APIs directly.
It does not compile or exercise static `handle_command()` from `main.cpp`, so it
does not directly prove that every command/reconnect/replay path retains the lock
or that invalid traffic does not refresh arrival health. The smoke executable
does not inject serial frames either.

Recommendation: make the dispatcher independently testable or use an injected
serial/time harness. Cover boot, enable, clear, home, unsupported trajectory/claw,
disable with old sequence, reset-link, duplicate/new packets and malformed stream
in actual handler order. Preserve the qualification lock; do not create a test-only
production bypass. Score severity 2, likelihood 3, impact 2, later cost 2 (24).

### CTRL-01 — controller reset retains targets and untimestamped measurements

`control_reset()` clears effort/integrator, but leaves target and measurement state.
No current command can enable the locked system, so this is not an exploitable
powered-path defect in the present revision. It must not become a stale-target
replay when a real enable transition is implemented. Document/implement explicit
target invalidation or target-to-current-measured-position handoff on every future
arm transition; measured data must carry validity and age. Score severity 3,
likelihood 2, impact 3, later cost 2 (36).

### LINK-01 — fresh receive time is not proof of fresh board state

Sequence filtering and explicit missing values are useful. A delayed run of
increasing timestamp telemetry still receives fresh host arrival times; no board
boot/session identity or command acknowledgement exists. This is already disclosed
in the protocol document and contained by the lock. Before enabled operation,
the planned session/acknowledgement/deadline contract must be implemented and tested
across buffered USB and board reset. Do not mistake a CRC for an identity check.
Score severity 3, likelihood 2, impact 3, later cost 3 (54).

### COST-01 — the budget-compatible rig is a scope reduction, with unresolved selections

The $474.11 rig is honest arithmetic but only $25.89 under the ceiling and most
lines are unquoted. Its RP2040 substitute needs a firmware port and the $45 drive
needs a verified interface. Keep the all-new basket and owned-parts credit separate.
Do not describe this as a manufacturable $300–500 complete catching robot. This
is an engineering scope/cost constraint, not solved by more software.
Score severity 2, likelihood 4, impact 3, later cost 3 (72).

## Area scores and exact prototype scope

- **Dynamics: 6/10.** Good extension-dependent rigid-body model and energy check;
  guide sign must be fixed. Missing exact mass offsets/driver curves and a qualified
  load envelope keep this below 9. Equation/test corrections are desk work; measured
  guide friction, flexibility and impact stroke require prototypes.
- **Controls: 3/10.** Useful bounded mathematical scaffold, no actual motion
  execution or measured plant. A specific adapter, reference/limits and feedforward
  implementation can improve this before hardware integration; tuning and stability
  margin require restrained testing.
- **Embedded: 5/10 for logic diagnostics; 3/10 for robot motion.** Protocol packing,
  finite checks and permanent lock are credible. Dispatcher tests and exact hardware
  adapters are desk work; timing, watchdog and interruption behavior need a board.
- **Electronics: 4/10.** Sound hazard identification, missing exact schematic/parts
  and inconsistent prose figures. Circuit/selection review is desk work; current,
  droop, regenerative waveforms, EMI and temperatures require measurements.
- **Safety and reliability: 4/10 overall, 8/10 for the current software-only
  qualification boundary.** The lock contains immediate motion risk. Contradictory
  bring-up instructions and absent physical stop/retention implementation preclude
  a high system score. No software-only review can establish stop distance.

Allowed prototype scope supported by this review: unpowered full-travel tube/guide
fit coupons, belt-clearance and stop-contact inspection, finger material/closure
fixtures using weighed soft foam objects at low energy, offline simulation and a
logic-only MCU with the motor bus physically disconnected. A horizontal guarded
single-axis powered rig is the next intended scope **after** exact drive/circuit,
firmware adapter, limit/fault and cutoff tests are complete. Free rotating arm,
autonomous catches, contact-triggered powered closure and throws are not ready.

## Round-two acceptance focus

Verify DYN-01 using Cartesian projection and report corrected numbers. Reconcile
the operational documents and current generated electrical data. Review dispatcher
tests if added. Confirm that every major gate still appears as an unresolved desk
design/implementation task rather than a falsely claimed physical-test-only unknown.
Do not inflate readiness merely because the qualification lock makes the current
incomplete firmware harmless.
