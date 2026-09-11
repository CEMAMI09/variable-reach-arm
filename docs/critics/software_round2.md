# Independent software and robotics critic — round 2

Reviewed 7 September 2026. This isolated critic did not implement the fixes.
Scope: the S1–S3 corrections and quintic-domain issue from round 1, with
adversarial mathematical and deadline checks. No hardware was actuated.

**Verdict:** the three identified desk defects are resolved within the documented
offline model. No new major defect was found in this bounded re-review. This is
not autonomous catching readiness: the missing executor, measured actuator
envelopes, camera acquisition and calibrated claw/contact model remain real
integration work.

## Findings and independent evidence

### S1: corrected under the explicitly stated error-bound contract

Independently projected a point at two different physical exposure times into
rectified pinhole cameras, including motion in all three camera directions.
The camera identity gives `disparity * Z = fx * (baseline - dx + u_right * dz)`.
Applying the displacement norm bound to `(-1, 0, u_right)` and then bounding the
disparity denominator gives the implemented interval. This accounts for axial
motion as well as the original adversarial lateral motion.

A seeded 100,000-case independent synthetic experiment varied X/Y/Z, arbitrary
3D direction, speed from 0–8 m/s, signed physical exposure offsets up to 2 ms,
relative timestamp errors up to 0.1 ms, and independent pixel perturbations
whose disparity difference remained within the supplied 0.5 px bound. Of
93,994 accepted measurements, **zero** exceeded the returned depth bound. The
maximum actual-depth-error / returned-bound ratio was **0.986094**. The test
deliberately relaxed acceptance thresholds to exercise poorly conditioned cases;
this is not a prediction of practical camera acceptance rates. Independent
projection, rather than reuse of the implementation formula, supplied truth.

The contract still requires an actual bound on speed throughout the exposure
interval and on both individual horizontal-coordinate errors and their disparity
difference. Nominal detector standard deviation is not such a bound. Calibration,
rolling shutter, absolute timestamp bias and transverse world-position error are
not certified by this scalar depth bound. These exclusions are documented;
they must remain explicit in acquisition and estimator integration.

### S2: budget and dispatch checks close the identified schedule gap

The profile now reserves planning time before communication latency, checks
monotonic elapsed time during and after the search, and independently verifies
fresh stationary feedback and arrival before the unchanged start time.

Additional direct probes rejected clock rollback, NaN, infinity and a 20.001 ms
elapsed interval against the 20 ms budget. Arrival exactly at the deadline
passed; arrival 1 ns late failed. A deliberately stale caller `now` snapshot
can still produce an offline candidate when the search itself is quick, but the
mandatory dispatch check rejects it using current time. Consequently, this helper
must be called by the eventual executor at dispatch; planning alone is not a
timing permit. No executor currently exists and no powered authorization was
inferred. Exact measured-pose equality is conservative but will be impractical
with noisy encoders; replacing it requires a justified uncertainty envelope,
not casually relaxing the comparison.

### S3 and trajectory-domain issue: resolved

Public geometry defaults now load the shared design file. The changed-geometry
regression exercises actual API behavior, including planning, instead of checking
only today's constants. General moving-boundary quintics reject out-of-domain
samples; held rest-to-rest segments now return zero derivatives outside their
interval. Endpoint jerk steps remain intentional and documented.

Executed all `test_host*.py` regressions: **45 passed**. This count covers the
current host suite, not firmware, CAD or physical tests.

## Remaining issues, severity and readiness

- **High severity / high likelihood upon powered integration / large impact:**
  there is still no complete qualified trajectory executor, moving-state abort
  planner or measured coupled actuator envelope. These are already acknowledged
  desk/integration gates. Keep the present hardware locks; implement and fault-test
  the interfaces before connecting motion. They are not solved by this review.
- **Medium severity / high likelihood in real imagery / centimeter-scale impact:**
  systematic calibration/time bias, realistic detector errors and rolling shutter
  need acquisition contracts and independent moving-object replay. Some work can
  be done before hardware; performance bounds require the actual cameras.
- **Low severity / medium likelihood / integration friction:** repeated default
  file loads are safe for offline use but an eventual application should load one
  immutable configuration snapshot and pass it through a planning transaction.
  Otherwise a concurrent file edit could mix versions across separate calls.
  Do not put filesystem reads inside a deterministic embedded loop.

## Updated scores

- Kinematics **8/10**: defaults fixed; full-assembly envelope and measured frames
  still require integration and validation.
- Trajectory planning **7/10**: identified deadline defect fixed; moving-state
  execution, aborts and actuator feasibility remain unfinished desk work.
- Vision/estimation **5/10**: explicit conservative pair-motion depth bound;
  real acquisition and calibrated error characterization remain absent.
- Claw planning **5/10**: timing model is useful; no measured closure/retention
  mechanism or qualified contact state interface.
- Simulation **6/10**: useful offline checks, without measured motor/contact/flex
  behavior or replay validation.
- Software testability **8/10**: adversarial regressions and deterministic clocks
  improve confidence; recorded data and executor fault injection would raise it.
- Powered autonomous software readiness **3/10**: not ready. Offline modeling and
  passive measurement fixtures are appropriate; autonomous motion remains gated.

No new reason was found to redesign the corrected small-model mathematics before
those integration tasks. Resolving S1–S3 does not close the entire robot's design
review or establish physical catch success.
