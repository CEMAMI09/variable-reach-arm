# Calibration contract

Firmware has no qualified driver/encoder/homing implementation. Do not follow the
historical instruction to drive toward a named pin. Qualify the restrained homing
procedure and independent stop first; see bringup.md.

Use the documented base frame: +Z up, zero yaw along +X, zero pitch horizontal.
Measure pitch-axis origin and actual claw entry plane. Extension zero is a measured
soft reference, not hard-stop contact. Store SI offsets, signs, uncertainty, actual
hardware identity and config revision together.

With motor energy isolated, manually verify encoder sign and scale over known
motion. A motor encoder cannot detect all transmission slip or establish tip
accuracy. Later measure repeated low-speed switch approaches only on a qualified
restrained rig. Record switch and soft-limit positions separately with stopping
clearance before the physical stop.

No camera is owned or qualified. Calibrate chosen cameras at their actual resolution,
focus and crop, including distortion, stereo pose and rectification. Validate on
held-out surveyed3D points across the volume. Store serial numbers and image size
with calibration. Measure the camera-to-base transform and document its direction.
Test detection under lighting changes, occlusion and blur; reject ambiguous pairs.

Use exposure capture timestamps, not host arrival timestamps. Independently measure
frame skew, timestamp uncertainty and capture-to-command latency. Nominal FPS is
not latency. Nonzero stereo timing uncertainty requires an explicit speed bound;
see planning_deadlines.md. Calibration and association errors need separate bounds
beyond the implemented timing/pixel gate.

Measure actual capture volume, claw angle, closure/release delay and pad compliance
on the isolated fixture. CAD mouth position is not a measured grasp region. Repeat
checks after changes to tubes, guides, belts, cameras or claws; retain old files.
