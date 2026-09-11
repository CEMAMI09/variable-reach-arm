# Current full CAD animations

Both GIFs are regenerated from `build_review_robot.py`, including the base, yaw supports, telescope, attached trunnions and three single-joint claws. The raised 850 mm shoulder with stiffened yoke is the current clearance-prototype baseline; physical qualification is pending.

- `arm_motion.gif`: prescribed yaw, pitch, full extension/retraction and claw opening/closing.
- `arm_motion_catch_fast.gif`: coordinated interception posture, closure and short retraction sequence. The old filename remains for link compatibility. There is no simulated ball capture or claim of actual motor speed.

The on-image caption is mandatory: these are kinematic demonstrations, not measured performance or proof of catch success. Playback is 12 fps; timing is illustrative. Mechanical interfaces and actuator qualification remain subject to the current engineering review.

To reproduce, run `animate_arm.animate_and_export(mode="demo")` and `animate_arm.animate_and_export(mode="catch_fast")` in FreeCAD with `cad/scripts` on its module path. Then run `python cad/scripts/make_gif.py`, and run it again with `--frames cad/animations/frames_catch_fast --out cad/animations/arm_motion_catch_fast.gif`. Pillow is required for GIF assembly. Frames are listed explicitly in `metadata.json`, so stale PNGs from earlier renders cannot silently enter a new GIF. The animation creates and closes its own temporary CAD document, and restores the previously active full assembly without saving over it.
