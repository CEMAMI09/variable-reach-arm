# Subsystem testing — development, not powered release

The current firmware refuses powered operation. Do not bypass that lock. Complete
qualified driver, feedback, homing, independent stop, brake and power interfaces
before any restrained powered test. See bringup.md and safety.md.

## Records

Record CAD/config/firmware revision, actual parts, payload, reach, supply voltage,
ambient temperature and instrument calibration. Save raw capture-time samples
under data/experiments/. Report sample count, RMS, maximum and 95th percentile;
separate measured results from targets and include measurement uncertainty.

## Unpowered mechanics

1. Measure tube dimensions, corner radii and straightness; print the guide coupon
   first. Verify screw access and retention before installing long tubes.
2. With motor/belt disconnected, measure breakaway and running force in both
   directions at 0/125/250/375/500mm stroke, unloaded and with proposed tip load.
   Run20 slow traversals. Jamming, pad migration, screw contact or tube damage
   fails. Compare measured friction with sizing assumptions.
3. Load the tip in both bending directions at three reaches. Subtract fixture
   compliance; report force/displacement slope and residual displacement. Compare
   against the model and positioning error budget. The old25mm allowance is not
   a stiffness qualification. Measure torsional compliance and reversing backlash.
4. Check bolt witness marks, access, assembly order and cables over full travel.
   Verify stop contact before guide/belt disengagement. CAD checks alone do not
   qualify tolerances, stopping capacity or fatigue.

## Logic/electronics without motor energy

Run documented host, engineering and production-dispatch tests. On the selected
MCU, measure loop jitter under worst communications load. Inject stale/malformed
commands, replay, invalid encoders, unexpected limits and watchdog timeout; verify
latched faults and deliberate rearming. Test independent energy removal using a
dummy load. A telemetry flag or motors_disable_all stub is not electrical proof.

## Future restrained powered tests

After release gates close, start with independent current/speed/travel limits,
no projectile, and no person in the swept volume. Prove homing direction first.

- Extension: log position, velocity and current for20 repeated moves. Report
  endpoint/midpoint repeatability. Document filtering when deriving acceleration.
- Pitch/yaw separately at three reaches: RMS/peak error, overshoot, repeatability,
  settling within a stated band, and slip/lost-step checks. Compare variable-inertia
  predictions to measurements before scheduling gains or increasing speed.
- Thermal/power: monitor temperatures through representative duty until stable.
  Measure simultaneous acceleration current and braking bus voltage with suitable
  instruments; a DMM cannot capture short regenerative peaks. Compare actual
  ratings with margin, not assumed efficiency alone.
- Vibration: measure dominant frequency and decay versus extension after a small
  move/impulse; use the results to constrain trajectory bandwidth.

## Vision and planner

Validate fixed surveyed points, then independently measured moving trajectories.
Report position/prediction error by horizon, depth, speed, lighting and occlusion.
Measure capture, transport, detection, planning and command latency separately,
including tail latency and stereo clock uncertainty. Replay tracks through reach,
partial-extension, unreachable, stale-data, late-dispatch, saturation and collision
cases before connecting an executor. Never compress a late trajectory to catch up.

## Claw and eventual contained catches

Test the claw alone with a soft known-mass ball behind containment. Measure closure
and release time, retention, bounce-out, pad force/displacement, wear and power-loss
behavior. Compare compliance, velocity matching and bounded radial retreat only
after each is independently qualified. Acceleration is not force without a model.

Later report all attempts and rejected opportunities, binned by incoming speed,
distance and extension, with sample counts. Report both attempted-catch success
and overall opportunity success. Increase energy only after a repeatable lower
stage. Throwing requires separate release-timing and containment validation.
