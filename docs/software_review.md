# Robotics software engineering review — 7 September 2026

The original host stack could label missed balls as feasible catches. The revised
stack is suitable for offline regression, calibration development and isolated
subsystem experiments. It is **not released for autonomous powered catching**.
The end effector is an **actively closing three-finger claw; no net is assumed**.
Passing the planner now means a bounded geometric motion candidate, not a proven
grasp, a motor torque qualification or permission to enable hardware.

## Preserved architecture

Preserved the yaw–pitch–extension architecture, SI spherical kinematics, future
ballistic candidate search, synchronized smooth profiles, host/MCU separation,
simple color segmentation and CSV telemetry. These are useful, understandable
starting points. No extra axes, reinforcement learning or speculative sensors
were introduced. The original serial implementation is reviewed separately in
the embedded work; this report does not imply a working hardware motion adapter.

## Significant findings and implemented changes

1. **Unreachable IK became a different target.** Problem: `inverse` silently
   clamped angles and reach. Why it matters: the planner's subsequent limit check
   could pass after the original ball point had already been lost. Solution:
   unreachable and nonfinite targets return `None`; explicit `clamp_joints` remains
   only for manual UI/visualization. Tradeoff: fewer nominal successes, truthful
   reachability. Implemented in `host/kinematics/arm_kinematics.py`, with random FK/IK
   round trips and near, far, behind-arm, angular-limit and NaN regressions.

2. **The workspace was incorrectly treated as a filled sphere.** Problem:
   targets below 700 mm radius were projected outward and called catchable.
   Why it matters: a straight three-axis arm cannot move its mouth to arbitrary
   points inside its minimum-radius shell. Solution: strict shell reach policy;
   only an explicitly measured inward capture pocket may absorb a small radial
   offset. Tradeoff: targets inside the shell need a future actual shell crossing
   or are unreachable. Implemented in `host/planning/reach.py`. The reference is
   pivot to claw mouth, `L=.700+s`; encoder extension is `s`, not `L`.
   A feasible normal-shell catch is preferred before weighted timing cost, so
   the arm extends only when its retracted candidate is infeasible. An explicit
   `prefer_retracted=False` override permits a different timing priority.

3. **The default 30 mm extension margin moved the claw past the ball.** Problem:
   adding radius is not a free safety margin. Solution: default margin zero;
   positive margin must fit an explicitly supplied, measured capture depth.
   Tradeoff: uncertainty is an aperture/error-budget problem and cannot be hidden
   by stretching the target vector. Implemented in reach selection; the planner
   uses exact mouth crossings and never assumes a pocket depth from CAD appearance.

4. **Timing credited the oldest observation as available actuation time.**
   Problem: the estimator previously returned its first timestamp and planning
   started there. Why it matters: processing and transfer latency consumed real
   flight time but were ignored. Solution: fit the state at the latest exposure,
   subtract current observation age and command latency, reject old/future states.
   Tradeoff: live callers must provide exposure-clock mapping, current monotonic
   time, measured rates and measured command latency. Implemented in estimator
   and planner; `now=None` is reserved for synthetic offline data.

5. **Feasibility used a trapezoid while execution used a quintic.** Problem:
   the shorter trapezoid bound did not constrain quintic peak velocity,
   acceleration or jerk. Solution: analytic normalized quintic coefficients and
   exact rest-to-rest derivative peaks. For displacement `d`, duration `T`:
   `v_peak=1.875|d|/T`, `a_peak=(10√3/3)|d|/T²`, `j_peak=60|d|/T³`.
   The required duration is the maximum of the three inverse bounds for all axes.
   Tradeoff: this is the fastest allowed member of this quintic family, not the
   globally fastest trajectory. Jerk is finite but has endpoint steps; snap is
   not bounded. Implemented without a NumPy solve at each sample. Tests compare
   analytic peaks to 10,001 samples in both directions and reject faster profiles.

6. **Moving-state replanning could pretend the robot was stationary.** Solution:
   the current planner explicitly rejects nonzero/invalid initial rates. Live
   calls cannot omit rates. Tradeoff: this version supports a single synchronized
   move from a verified resting state; it cannot safely update a moving catch
   trajectory. Implemented fail-closed behavior. A future implementation must
   preserve measured position, velocity and acceleration, prove polynomial extrema
   and stopping feasibility, and transact replacement trajectories atomically on
   the MCU. Streaming arbitrary host position steps is not a substitute.

7. **Normal-reach catches depended on search-grid coincidence.** Problem: a
   zero-thickness shell crossing almost never occurs at a regular 20 ms sample.
   Solution: solve the ballistic radius quartic by derivative-root isolation and
   bracketed bisection, including tangencies and multiple crossings inside one
   search interval. Tradeoff: numeric root tolerance remains bounded and explicit.
   Implemented in `shell_crossing_times`, with between-grid and tangent regressions.

8. **No claw closing-time or entry-direction feasibility existed.** Problem:
   position coincidence does not mean active fingers can close before the ball
   escapes or strikes the back of the claw. Solution: reject wrong-side approach;
   `ClawTiming` requires measured closure time, trigger latency, usable ball-center
   depth and lateral clearance. The ballistic inward path and conservative lateral
   displacement must fit those bounds during closing. Tradeoff: conservative
   contact-triggered closure rejects many fast balls; pre-triggering and moving
   interception need separate verification. Implemented in `host/planning/grasp.py`.
   `require_grasp_timing=True` rejects missing measurements. No existing actuator
   is assumed to achieve the hypothetical fast-claw parameters used in tests.

9. **Collision checking considered only the target, not the moving boom.**
   Solution: conservative interval bounds for the whole straight boom, including
   its rear overhang, between progress intervals of the synchronized trajectory.
   Ground and caller-supplied external keep-out boxes are checked continuously by
   enclosure rather than only at sample points. Tradeoff: enclosing boxes can
   reject safe motions. Implemented in `host/planning/collision.py`; thin obstacles
   between endpoints and rear obstacles have regressions. Real CAD self-collision,
   moving fingers, cables, flex and operator exclusion remain release gates.

10. **The advertised Kalman filter did not estimate velocity or covariance.**
    Solution: remove the misleading position blend; preserve a clear compatibility
    error and use rolling ballistic least squares with timestamp, span, gap, RMS
    residual and peak residual gates. Tradeoff: no confidence covariance, drag
    model or robust identity association is claimed. Implemented a standard-library
    estimator and tracker; invalid detections/order faults/dropouts invalidate the
    current estimate. A small residual is not evidence against calibration bias.

11. **Pixels were not connected to calibrated world coordinates.** Solution:
    add a rectified stereo geometry boundary with explicit camera/world convention,
    verified rotation matrix, calibration ID, exposure skew/age, epipolar agreement,
    positive disparity, depth range and depth-conditioning gates. Tradeoff:
    acquisition, undistortion/rectification and clock synchronization still require
    actual camera calibration. Implemented in `host/vision/geometry.py`; no monocular
    depth is fabricated. Detector candidates also need size/circularity gates so
    the largest orange rectangle does not automatically win.

12. **Throw speed mixed rad/s and m/s, and release pose used an unsampled endpoint.**
    Solution: add the Cartesian tip Jacobian; root review disabled executable
    throwing and corrected the offline swing preview to use the sampled pose/rates.
    Tradeoff: throwing remains unavailable until inverse-ballistic release,
    finger opening timing, motion limits, contact and post-release stopping are
    implemented and qualified. `plan_throw_toward` deliberately raises an error.

13. **Simulation repeated the planner's assertion without checking a trajectory.**
    Solution: execute the same analytic profile, verify derivative peaks, inspect
    intermediate workspace states and compute actual mouth-to-prediction miss.
    Connect sampled states to `engineering.review_sizing.dynamics`, recomputing
    translated-body inertia, gravity and simultaneous-motion coupling throughout
    extension. Tradeoff: sampled load peaks are diagnostic, not upper bounds or
    certified motor capacity. Geometry mismatch between host and engineering raises
    an error. `physical_catch_validated` and `hardware_ready` remain false.

14. **Telemetry could overwrite a previous experiment silently.** Solution:
    exclusive-create logs by default, explicit opt-in overwrite, context-managed
    closure and rejection of misspelled fields. Add exposure, arrival, planning,
    capture and closure timestamps, calibration identity and residual/error fields.
    Tradeoff: callers must choose a fresh experiment filename and valid schema.
    Existing legacy position fields remain for compatibility; record their units
    in run metadata and prefer SI values for new host integrations.

## Active impact absorption: what is physically possible

World relative velocity is `v_ball-J(q)q_dot`. Project it onto the arm's radial
unit vector. For an inward ball, retraction is a negative radial hand velocity
and can reduce the radial component. It does not cancel tangential impact.
`assess_retraction` implements this decomposition and reports available stroke
and a bounded *steady-state diagnostic* velocity, never a motor command.

For a stationary mouth and an inward 4 m/s ball, future steady retraction at
1.2 m/s reduces the radial relative speed to 2.8 m/s. At `L_min`, available
retraction is zero. Provisional bench extension speed is only 0.15 m/s, so its
best eventual radial reduction is small. Actuator acceleration/jerk and trigger
delay further limit benefit during a short impact. Retraction does not replace
foam compliance, suitable TPU pads, retained-ball geometry or force testing.
An outward-moving ball is a different case; blindly retracting can increase
relative speed. The diagnostics reject that assumption.

Closing time is also a fundamental constraint: at 2 m/s, 130 ms of trigger plus
closure delay implies about 260 mm of inward ball-center travel before including
gravity. An 80 mm usable claw depth cannot absorb that delay without an already
tested impact/slowing/retention mechanism. The demo rejects this case. The test
fixture must measure actual force, slowing and closure; CAD finger length is not
equivalent to usable stopping distance or successful grip.

## Configuration and interface contract

- SI throughout host math: metres, seconds, radians, rad/s and m/s. `JointState.L`
  denotes reach in position states, but extension velocity/acceleration in rate
  states; `tip_velocity` maps those rates into Cartesian m/s. The serial boundary
  owns explicit degrees/mm conversion and firmware checks.
- World: +X forward, +Y left, +Z up. Pitch zero horizontal. Geometry loader reads
  `engineering/design_parameters.json`. Provisional 90 mm swept-radius and 350 mm
  rear-envelope allowances still require confirmation against final CAD and wiring.
- Exposure times, estimator epoch, `now`, profile start and interception all share
  one host monotonic clock. MCU clock mapping/acknowledged execution are a separate
  communication requirement. Wall clock and receipt time are not exposure time.
- The benchmark planner caps are 0.35 rad/s angular, 0.15 m/s extension,
  0.70 rad/s² angular, 0.50 m/s² extension; jerk caps 4 rad/s³ and 3 m/s³.
  These are proposed commissioning ceilings after independent safety checks,
  not proven motor capabilities. Start slower. No fixed cap certifies `I(L)`
  dynamics; the coupled model reports demand and still lacks verified motor curves.
- `require_grasp_timing=False` returns geometry candidates for offline study.
  `True` requires measured claw geometry and timing. Neither path enables motors.
- `ClawTiming` clearances are ball-center clearances **after** ball radius,
  calibration/prediction errors, flex and timing uncertainty have been deducted.
  Grasp feasibility currently assumes the arm holds at contact; dynamic matching
  and moving-state replanning are deliberately not represented as implemented.
- OpenCV and NumPy are optional image-test dependencies. Core planning, fitting
  and simulation use the standard library. Tested image dependencies are pinned
  in `host/requirements-vision.txt`; serial dependencies are maintained separately.

## Validation evidence

`python -m unittest discover -s tests -p "test_host*.py" -v` passed **39 tests**
on the local QA Python environment, including two synthetic OpenCV image tests.
Core regressions include wrong reach/angles, nonfinite inputs, between-grid shell
crossings, exact derivative peaks, initial-rate enforcement, old/future timestamps,
slow active closure, wrong entry direction, thin/rear collisions, estimator order
and dropout faults, stereo conditioning/synchronization, log preservation, physical
catch non-assertion, and inertia change during executed extension.

`python -m simulation.run_demo` distinguishes an ideal normal-shell crossing,
an original optimistic throw rejected at bench caps, a hypothetical partial-
extension trajectory, and rejection due to slow active-claw closure. Positive
geometry results are not reported as successful physical catches.

## Before physical autonomous motion: desk work still required

1. Implement a deterministic hardware trajectory executor and measured feedback
   adapter with verified homing, fault latching, command freshness and atomic
   trajectory replacement. The host cannot infer feedback or safely arm stubs.
2. Complete moving-boundary replanning and a bounded stop/abort trajectory if
   replanning during motion is required. Add polynomial-extrema checks, actuator
   saturation, torque-speed/thermal envelopes and collision checks for those paths.
3. Freeze claw actuator/linkage and demonstrate with a fixture that its swept
   fingers do not strike the ball out, pinch wires, overdrive stops or falsely
   report retention. A mouth crossing alone cannot satisfy the user's active-grab
   requirement. Add contact/closed-state integration only after those interfaces exist.
4. Implement actual camera acquisition, exposure timestamp mapping, rectification,
   calibration-file loading and target association. A single uncalibrated camera
   cannot supply arbitrary 3D ball positions. Validate full CAD self-clearance and
   an enforced physical exclusion volume; external boxes do not encode humans.
5. Add experiment metadata and replay datasets with deliberate failures. Preserve
   raw exposure times and image frame IDs so end-to-end latency can be audited.

## Unknowns needing physical data

Measure loaded torque-speed/temperature curves; encoder tracking and latency;
guide friction/stick-slip versus extension and bending load; backlash, flex and
vibration; claw mass and dynamic stiffness; finger closure latency distribution,
grasp force/retention and actual impact stopping distance; camera exposure delay,
rolling-shutter bias, frame drops and stereo skew; calibration/prediction errors
at actual catch horizons; and loss-of-power stopping behavior. Simulation cannot
determine these from the current repository.

## Subsystem experiment acceptance records

Record at least 30 repeatable runs per condition before claiming repeatability;
report sample count, conditions, RMS, peak and percentile errors, not one best run.

- **Tracking fixture:** surveyed 3D points, ball-sized target, measured frame times.
  Hold out future frames at 50, 100, 200 and 400 ms; report prediction RMS/95th/peak
  versus speed/range, drop rate, exposure-to-estimate latency and calibration ID.
- **Claw fixture:** disconnected from arm, lightweight foam balls, contained test
  area. Measure trigger-to-first-motion and trigger-to-retention across supply,
  temperature and ball sizes, plus bounce-out and stalled-claw behavior. Report
  usable ball-center depth/clearance, closing-time 95th/maximum and peak force.
- **Axis fixture:** independent safety qualification first. Log measured positions,
  rates, current, commanded profile and communication fault injections. Repeat
  retracted/mid/extended states, quantify RMS tracking, settling time, repeatability,
  speed/acceleration, deflection and vibration. Do not infer force from motor current
  until drivetrain friction and torque constant have been measured.
- **Integrated catches:** only after release gates. Stratify success rates by range,
  incoming velocity, extension, approach angle and prediction horizon. Report
  denominators and confidence intervals; retain failed and unreachable trials.
  Distinguish mouth alignment, finger retention and completed safe catch.

## Candid software assessment after this pass

- Kinematics **8/10**: strict SI shell model and Jacobian verified; real capture
  frame calibration and full CAD self-collision still need integration. Desk and
  calibration work can raise the score before autonomous trials.
- Trajectory planning **6/10**: exact stationary-boundary derivative feasibility and
  timing fixed; moving-state replacement, torque envelopes and stop planning remain.
  These are desk implementation plus motor-data tasks, not small tuning details.
- Vision/estimation **5/10**: tested geometry/fit gates, but no real acquisition,
  calibrated stereo sequence, association or measured latency. Calibration fixture
  data and full data-path implementation are required to raise the score.
- Simulation **6/10**: executable ideal profiles, quantified misses and coupled
  load diagnostics; no contact, flex, motor dynamics, measurement noise replay or
  hardware-in-the-loop validation. Add measured effects only when data justify them.
- Active-grasp planning **5/10**: closure delays and physical approach are explicit;
  linkage/actuator and retention are not qualified. Fixture evidence, closed-state
  interface and moving-catch timing must raise this score.
- Software testability **8/10**: 39 reproducible regressions, deterministic offline
  paths and safe rejects; real recorded datasets and hardware fault injection remain.
- Software readiness for powered autonomous catching **3/10**: useful offline
  foundations, deliberately incomplete actuation/perception integration. Isolated
  fixtures and simulation are ready to develop; autonomous catching is not.
