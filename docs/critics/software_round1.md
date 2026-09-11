# Independent software and robotics critic — round 1

Reviewed 7 September 2026 after the first implementation pass. This critic did
not author the implementation. Scope: `host/`, `simulation/`, host regressions,
and `docs/software_review.md`. The claw is an active three-finger grabber; no net
or instantaneous grasp is credited. No motors were commanded.

**Verdict:** useful offline engineering software, not ready for autonomous
powered catching. Three additional desk issues deserve correction. Existing
hardware locks and explicit `hardware_ready=False` correctly prevent these
offline candidates from being represented as actuation permits.

## Major issues

### S1 — stereo skew can exceed the accepted depth error by several times

- Location: `host/vision/geometry.py:57–97` at review time.
- Severity: high for future interception; likelihood: high with unsynchronized
  cameras and fast lateral motion; impact: centimeters of biased targeting,
  missed grabs, and underestimated error budgets. Fix-before-integration priority.
- Independent numerical reproduction: rectified cameras, `fx=fy=600 px`,
  `baseline=.12 m`, principal point `(320,240)`, identity extrinsics. At left
  exposure time 0, the ball is `(x=.12,z=1.2) m`, moving at `+4 m/s` in camera X.
  Left pixel is `(380,240)`. At right exposure `.002 s`, the right pixel is
  `(324,240)`. The function accepts the pair at `now=.02`, reports depth
  `1.285714 m` and disparity-only uncertainty `.011480 m` below the `.02 m` gate.
  Actual left-epoch depth is `1.2 m`: **85.7 mm error**. Horizontal motion passes
  the epipolar gate. The existing test using nonzero skew only checks algebra;
  it does not simulate the moving object at its two actual exposure times.
- The field is candidly labeled disparity-only; nevertheless the acceptance
  gate does not constrain the unmodeled error and downstream `Detection` loses
  the skew/uncertainty metadata. A low ballistic residual need not expose a
  smooth systematic bias.
- Suggested fix: require synchronized exposure or a conservative motion bound;
  propagate disparity perturbation from skew through depth conditioning and
  reject when the combined bound exceeds the capture error budget. Merely
  hardcoding a smaller skew is insufficient without speed/range assumptions.
  Add the moving-object stereo regression above and an accepted synchronized pair.
- Desk-solvable: yes. Actual exposure-clock error and motion bounds then need
  measured camera validation.

### S2 — live planning can return a profile whose start time has already passed

- Location: `host/planning/intercept.py:154–172`, search loop and return.
- Severity: high if connected directly to motion; likelihood: medium, increasing
  with candidate density or host load; impact: missed deadlines or a shortened
  trajectory that no longer satisfies the proved velocity/acceleration/jerk caps.
- `now` is an input snapshot. Start is `now+command_latency`; computation time
  is neither reserved nor checked when returning. The legal 10,000-candidate
  budget is a count bound, not a real-time deadline.
- Independent local reproduction: existing hypothetical partial-extension demo
  ball and prepared pose, its `PlannerLimits(2,2,1.2,6,6,4,40,40,60)`,
  `dt=.00012`, `now=0`, zero initial rates. Search took approximately **96 ms**
  and returned `start_time=.020`, interception `.9224`. An immediate downstream
  consumer would receive a profile starting about 76 ms in the past. Exact
  elapsed time is machine-dependent; the absent deadline check is deterministic.
- Suggested fix: explicitly reserve planning time, reject an expired schedule
  at dispatch, and require sufficiently fresh measured arm state. Do not repair
  a late schedule by jumping ahead in or compressing the polynomial. A live
  clock/deadline boundary should be independently testable with a fake clock.
- Desk-solvable: yes. Real latency distribution is a later measurement.

### S3 — shared design geometry is not the default for most public APIs

- Location: default `ArmLimits()` use in planning, reach and kinematics;
  `ArmLimits.from_design_file()` is used by the simulation.
- Severity: medium now, high after a geometry revision; likelihood: medium;
  impact: CAD/simulation and an ordinary planner call can disagree silently.
- Current values agree, so there is no present 700/1200 mm mismatch. However
  editing the authoritative JSON changes CAD and default simulation while
  `plan_intercept(ball,q)` and `inverse(p)` retain dataclass literals. The test
  only verifies today's fixed values and cannot catch divergence after a change.
- Suggested fix: one configured application boundary loads and passes a single
  immutable geometry instance, with explicit defaults restricted to synthetic
  examples; alternatively make defaults use the shared loader. Test with altered
  geometry and reject incompatible simulation/engineering models explicitly.
- Desk-solvable: yes; no physical measurements required to remove duplication.

## Minor issues and improvement opportunities

1. General nonzero-boundary `QuinticSegment.sample()` clamps position outside its
   time interval but returns a nonzero endpoint velocity/acceleration. Those
   values are not derivatives of the clamped position. Severity low today because
   the executable offline planner uses rest-to-rest segments within the interval;
   likelihood high when reused for moving-boundary planning. Define outside-domain
   behavior explicitly or reject such samples. `jerk()` likewise returns endpoint
   jerk outside a held rest-to-rest segment. Add domain tests before reuse.
2. Most estimator regressions are exact ballistic data with gross single
   outliers. They do not challenge accepted smooth bias, realistic pixel noise,
   calibration uncertainty, frame-time bias or drag over the prediction horizon.
   Severity medium for readiness, likelihood high in real cameras. Add deterministic
   synthetic/replay errors and held-out prediction checks; avoid claiming the
   residual gates are confidence bounds. Existing documentation already warns
   correctly about these limitations.
3. Default `require_grasp_timing=False` means a normal planner result can still
   omit the claw model. Its `hardware_ready=False` and simulation's
   `physical_catch_validated=False` are appropriate safeguards. Keep those flags
   immutable in the future dispatch boundary; a convenience caller must not
   promote `intercept_found` into "catch succeeded." No current actuation bypass
   was found in this review.

## Independent checks and what passed

Executed `python -m unittest discover -s tests -p test_host*.py -q`: **39 passed**.
Read the implemented equations rather than relying solely on those tests.

- Spherical FK/IK and Cartesian tip Jacobian are consistent with +Z up and
  radial mouth reach. Unreachable inputs are rejected rather than clamped.
- Rest-to-rest quintic peak factors and inverse-duration bounds are correct.
  General endpoint coefficients are also algebraically consistent.
- Exact shell-root candidates fix the zero-depth normal-reach search problem;
  a feasible retracted candidate receives explicit priority over extension.
- Collision interval multiplication contains the entire straight boom for the
  monotonic synchronized motion; it can reject safe moves conservatively. It is
  not a CAD self-collision checker, as documentation correctly states.
- Claw closing-time bounds consistently account for radial gravity sign and
  conservative transverse displacement. They do not assume instantaneous fingers.
  Retraction direction is correct and unavailable at minimum reach.
- Estimation uses centered time, the latest exposure epoch and correct gravity
  correction. Timestamp ordering/gap/age gates are useful. Throw execution is
  deliberately unavailable instead of claiming the heuristic hits a target.

## Scores and prototype readiness

- **Kinematics: 8/10.** Good small-model math. Resolve shared defaults and measure
  the actual mouth frame; integrate full CAD limits to raise the score.
- **Trajectory planning: 6/10.** Rest-to-rest candidates are credible. Resolve S2
  and S3 before integration; moving-state replacement, abort trajectories and
  actuator envelopes remain documented desk work.
- **Vision/estimation: 4/10.** S1 is an additional consequential error-budget gap.
  Correct it, implement real acquisition/calibration association, then validate
  on recorded moving-ball sequences to raise the score.
- **Claw planning: 5/10.** Necessary timing checks exist, but no qualified closing
  mechanism, retention feedback or contact model. Mechanical fixture evidence
  and a matching command/state interface are required.
- **Simulation: 6/10.** Honest ideal trajectories, miss distance and coupled load
  diagnostics; no motor dynamics/contact/flex/noise validation. Raise with measured
  models and independent replay, not more nominal success examples.
- **Software testability: 7/10.** Fast reproducible regression foundation. Add S1–S3
  adversarial cases, recorded data and interface fault injection to raise it.
- **Powered autonomous software readiness: 3/10.** Not ready. Offline simulation,
  calibration tooling and isolated passive fixtures are useful now. The currently
  documented missing executor/feedback/homing/camera acquisition are real readiness
  gaps, not newly discovered implementation defects or physical-only uncertainty.

No score is a safety certification. Before powered integration, finish the known
desk interfaces and fail-closed dispatch boundary, then measure latency, tracking,
claw closure/retention, drivetrain response and loss-of-power behavior on isolated
fixtures. A successful ideal mouth crossing cannot validate an active grab.
