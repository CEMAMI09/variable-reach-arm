# Calibration

## Axis homing

1. E-stop ready; software speed at minimum.
2. Extension: drive slowly toward `PIN_EXT_HOME` until switch; set encoder zero; record max switch position.
3. Pitch: move to known mechanical square / digital level; set soft zero (horizontal = 0°).
4. Yaw: align boom to base +X scribe mark; set zero.
5. Save offsets in `data/calibration/joint_zeros.json`.

## Camera (Phase 2)

1. Intrinsics via OpenCV chessboard → `data/calibration/cam0_intrinsics.yaml`.
2. Extrinsics: measure camera pose relative to base frame; store `T_cam_base`.
3. Color thresholds for foam ball under site lighting → `hsv_thresholds.json`.
4. Measure end-to-end latency (LED blink or falling ball) — do not assume fixed FPS.

## Stereo (Phase 3)

Stereo calibrate pair; verify triangulation error on known points < 15 mm in work volume.
