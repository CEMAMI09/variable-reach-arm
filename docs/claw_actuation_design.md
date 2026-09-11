# Three-finger claw actuation — current prototype

Problem → a claw envelope without springs, stops or a force path cannot demonstrate
capture. Implemented → three single-pivot rigid fingers, metal M3 pivots, integral
sector stops, smooth cross-drilled M2 tendon-eye pins, fixed guide eyes, return-spring
allowances and replaceable pads. This preserves a real grabber, not a net.
Tradeoff → three spring/preload adjustments and tendon routing require calibration.

## Motion and force path

Each finger rotates from +20 degrees open to -10 degrees closed. A 12 mm-radius
horn and fixed guide at local (-25,-4.5,52) mm give about 20.91 mm free tendon span
open and 27.08 mm closed: approximately 6.18 mm take-up opens the finger.
A hypothetical 6 mm servo drum therefore needs about 59 degrees rotation, before
elasticity and adjustment allowance. The springs close; pulling the tendons opens.
The modeled spring is a 0.5 mm wire, 4.7 mm mean-diameter, two-turn envelope with
formed legs. It is not a selected spring or a verified spring-rate calculation.

For three equal tendon tensions T, drum torque must be at least 3*T*0.006/eta Nm,
plus friction, transient demand and margin. Determine T from the chosen spring's
maximum torque divided by the instantaneous perpendicular tendon moment arm.
Do not assume a 12 mm moment arm through the entire sweep. Closure time requires
finger inertia, spring torque, contact compliance and friction measurements.

The tendon eye is a 1 mm transverse bore through the smooth 2 mm pin; edges need
rounding/polishing to prevent line abrasion. The fixed eye is an allowance that
requires a low-friction liner. Metal pivot spacers/washers isolate clamp preload
from the rotating finger. Do not clamp a printed finger between bolt head and nut.

## What is still incomplete

The modeled tendons currently terminate at the fixed guide eyes. A complete
three-line equalizer, housing retention, Bowden route and actual servo horn/drum
are NOT modeled or released. The user's servo model and shaft/mount dimensions
are unknown. A generic servo envelope must not be treated as a compatible part.
Select spring torque and tendon termination together with that servo; test release,
retention and response before using captured objects. Servo current and a separate
regulated supply must also be measured/qualified.

Print fingers and palm initially for fit in PETG, laid to keep bending loads in the
layer plane, typically 5–6 perimeters and 30–40% infill. Qualify the final material
at actual temperature/load; use tough nylon or ASA only when justified by testing.
TPU belongs on replaceable contact pads, not the entire load-bearing finger.
Use steel pivots, real springs and smooth purchased line guides/liners.

Verify free rotation at both stops, spring-leg retention, tendon rub through every
pose, captured-ball retention and power-loss behavior. A closed claw is not proof
of impact absorption or successful catching. No powered throwing release is approved.
