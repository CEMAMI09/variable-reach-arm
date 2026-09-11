# Bring-up — current revision and future gates

**Only unpowered mechanical checks, offline simulation and logic-only firmware
diagnostics are supported now.** Homing and real motor control are absent.
FLT_UNQUALIFIED cannot be cleared by the host. Do not remove it to try old jog
instructions. No hardware was flashed during this review.

## Work possible now

1. Print Rev B fit coupons. Measure tube dimensions, wall, corner radii and
   straightness. Record part and material revisions.
2. With motor power physically disconnected and the mechanism restrained, check
   hand travel, guide friction, accessible hardware and belt/claw clearances.
   Complete undeveloped interfaces before treating the CAD study as a mechanism.
   Minimum overlap is 240 mm; minimum guide spacing is 190 mm.
3. Verify smooth steel claw pivot grip, thrust spacers and retention. Start an
   isolated contained claw fixture with hand insertion and low-energy soft-ball
   tests. Measure mass, closure, stopping travel and retention; no net.
4. Run engineering, host and protocol regressions and python -m simulation.run_demo.
   Board diagnostics require inspected wiring and a physically disconnected motor
   bus. Verify missing-feedback sentinels, CRC/sequence handling, rejected commands
   and the persistent lock using docs/embedded_protocol.md.

## Gate before powered single-axis trials

These are required future tasks, not implemented instructions:

- Select the exact motor/driver and loaded torque curve, voltage/current settings
  and command/feedback interface. Implement timestamped feedback, bounded homing,
  following-error detection and deterministic bounded motion.
- Complete rated DC cutoff/manual reset, independent watchdog/enable, fuses,
  regenerative clamp and guarded travel. Verify the power circuit separately.
- Complete belt/pad retention, both hard-stop load paths and harness strain relief.
  Restrain the first telescope horizontally; omit gravity-loaded pitch motion.
- Prove startup, command loss, feedback/limit faults and reset cannot enable motion.
  Test independent stopping first on an unloaded drive, then at low energy in the
  restrained rig; record stop distance, residual force and voltage/current waves.
  motors_disable_all() is a stub, not proof of a physical cutoff.

Begin below proposed bench caps with reduced current and bounded profiles only
after these gates. Caps are future experiment ceilings, not authorization to power
this revision. Expand after measured acceptance and fault injection.

## Later integration

Finish base anchorage, yaw/pitch bearings/hubs and independent pitch drop restraint
before adding rotation. Test axes separately then together. Calibrate joint/camera
frames, total latency and prediction error; qualify claw closure/retention.
A physical containment barrier and empty active workspace are required for
high-speed or autonomous trials. Throwing follows deliberate release qualification.
See docs/testing.md and docs/safety.md.
