# Integration and release checklist — Rev B

**Not released for powered autonomous operation.** Full CAD, simulation and a
compiled Teensy target do not close these interfaces. Follow docs/bringup.md for
work possible now and docs/safety.md for physical stop requirements.

## Mechanical

- Anchored base, braced stock support, separated yaw bearings and coaxial opposed
  pitch bearings. External trunnions need positive torque retention; no shaft
  crosses the sliding tube bore.
- Measured square aluminum stock, retained fixed/moving wear pads, adjustable
  clearance, accessible belt anchorage/tensioner, both stops and return-belt guard.
- Three compliant claws with smooth steel pivots, spacers/retainers, spring/tendon
  paths, actuator mount, travel stops and replaceable pads. No net or fictitious latch.
- Full yaw/pitch/extension/claw clearance including rear overhang, real pulley
  flanges, screw heads, connector bodies, cable bend radii and tool access.
- Independent pitch drop restraint: a motor brake does not catch a boom after
  downstream belt, hub or structural failure.

## Electronics and software

- Exact wiring/pin map, current/voltage ratings, rated DC stop/manual reset,
  independent watchdog/enable, driver-side bus clamp, branch fuses and grounding.
  Test total-power-loss and USB-reset behavior. GPIO is 3.3 V.
- Real measured feedback, bounded homing, current/following-error limits,
  deterministic trajectory execution and measured loop/communication timing.
- v2 CRC/sequence framing, stale-data handling and qualified session/deadline
  behavior. Current unsupported commands reject and motion remains locked.
- Camera exposure timestamps, rectification/extrinsics, bounded stereo skew,
  valid 3D association and recorded calibration revision.

## Acceptance order

Unpowered fit → logic-only faults → qualified restrained drive → single-axis
feedback/homing → bounded profiles → simultaneous axes → camera replay/fixture
tracking → low-energy contained grasp → interception → throwing.

Do not skip a stage because another works in simulation. Record failed runs and
measured criteria. A physical containment barrier is required during high-speed/
autonomous work; people remain outside the reach and projectile volume.
Communication, encoder, current, limit or planner faults require the qualified
safe stop; autonomous motion must not continue.

Demonstrate a retracted catch when feasible, partial extension only when needed,
and rejection beyond feasible workspace/time. Record mouth alignment, positive
finger retention and a completed safe catch as distinct outcomes.
