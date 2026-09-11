# Second software pass: deadlines and stereo timing

**Problem → consequence → correction → tradeoff → implemented evidence.**

1. A dense candidate search could consume 96 ms and return a start only 20 ms after
   the original caller timestamp. Compressing or skipping that trajectory invalidates
   its derivative limits. Planning now reserves an explicit 20 ms computation budget
   before command latency, checks elapsed monotonic time during live search, and
   rejects an overrun. Offline replay is deterministic. The separate
   dispatch_schedule_valid boundary rejects a late start, changed/nonstationary
   measured pose, stale feedback or expired observation. It is a necessary scheduling
   check, never a hardware permission. A real executor, session/acknowledgement and
   fault integration remain unimplemented. Tradeoff: expensive searches can reject
   a geometrically feasible catch; they cannot borrow unbudgeted motion time.
2. A 2 ms stereo skew at 4 m/s admitted 85.7 mm depth error under a 20 mm gate.
   Nonzero pair timing error now requires an explicit physical speed bound. The
   exact depth interval includes disparity error and speed times exposure skew plus
   relative timestamp uncertainty. For normalized observed right coordinate uR,
   d Z = fx (baseline - deltaX + uR deltaZ); Cauchy–Schwarz bounds the unknown
   displacement. Reject if this interval exceeds depth/error limits. The bound
   excludes calibration/association errors and is not a covariance or measurement
   of actual speed. A caller must supply a defensible speed and timestamp bound;
   unknown motion with nonzero skew fails closed. Tradeoff: fewer accepted pairs
   from unsynchronized cameras, which otherwise create false precise detections.
3. Public FK/IK/reach/throw/planning defaults now load the shared JSON. Explicit
   ArmLimits objects still support fixtures, but edits to shared geometry propagate
   to normal callers. The parameter file is not silently replaced by stale constants.

Regression tests include the critic's moving-ball image pair, small bounded skew,
timestamp uncertainty, a deterministic over-budget clock, late/stale/moved dispatch,
and a changed shared geometry file. The firmware remains permanently unqualified;
these corrections do not enable physical motion or certify grasp success.

## Full-assembly collision gate

The desired 70-degree pitch and ±70-degree yaw requirements remain in shared
geometry. Full CAD has known interference at high pitch. Clear isolated poses
at 35 or 40 degrees do not prove a continuous safe workspace, so no reduced
operating range is inferred from those samples.

`plan_intercept` and `motion_clear` now default to `collision_model="full_assembly"`
and fail closed. No continuous, revision-bound full-assembly collision validator
exists; changing a JSON status string cannot enable one. Explicit
`collision_model="ideal_boom"` retains the earlier straight-boom, external-box and
floor analysis for offline simulation and mathematical tests. Such results carry
`self_collision_verified=False`; simulation reports its simplified collision model.

`schedule_timing_valid` isolates the mathematical deadline/fresh-state checks.
`dispatch_schedule_valid` additionally rejects every ideal-only or unverified
geometry candidate. Both remain necessary checks rather than hardware enable
permissions. This preserves useful requirements analysis while preventing an
ordinary planner call from treating the incomplete CAD workspace as feasible.
Before enabling full-assembly planning, implement and independently validate
continuous trajectory collision checking for the actual CAD revision, including
cables, guards, tolerances and the intended permitted-contact exclusions.
