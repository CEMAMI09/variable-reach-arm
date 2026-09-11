# Rev B component decisions and procurement hold

This supersedes the original assertion that a $449 robot meets high-speed targets.
The original BOM actually sums to **$701 before reserve**. The new BOM is a complete
cash-purchase planning allowance, not an instruction to order parts. Run
`python -m engineering.review_sizing` for arithmetic, shipping/tax allowance and
reserve. Prices marked `estimate_unquoted` are explicitly not current vendor quotes.
Existing PC, printer, bench, hand tools, measurement tools and electricity are excluded.

## Architecture to preserve

Keep yaw + pitch + one translating stage. Preserve the 0.70–1.20m **claw mouth**
reference. Use three compliant claws with a light retention/release mechanism;
**no net**. Keep the extension motor near the shoulder and all heavy axis motors
off the inner tube. Square aluminum sections supply anti-rotation without a second
guide rail. Retain independent metal trunnions outside the boom bore; a transverse
shaft through the tube would block the moving inner tube and belt.

## Actuator decisions

Pitch and yaw: an exact STEP/DIR closed-loop stepper kit remains a cost reference,
not an approved high-speed motor. The manufacturer listed the
[1-CL57T-P20-V41 kit at $86.60](https://www.omc-stepperonline.com/tp-series-1-axis-closed-loop-stepper-cnc-kit-2-0nm-283-28oz-in-nema-23-motor-driver-1-cl57t-p20-v41)
on 2026-09-07. Its 2Nm value is **holding torque**, the motor is 5A/phase and
0.4ohm/phase, and the driver accepts24–48V. A 2Nm holding label does not satisfy
the generated running torque demands with1.5 margin. The exact manufacturer
[torque curve](https://www.omc-stepperonline.com/download/23E1K-20_Torque_Curve.pdf)
was subsequently read visually in the browser. It is explicitly a **48V,5A
pull-out** curve, not24V performance or continuous thermal torque. Rounded readings
and uncertainty allowances are recorded in `motor_curve_23e1k20.json`. The ratio
study screens pitch16:1 and yaw12:1 as promising against that48V graph; current
8:1/6:1 ratios fail. This does not authorize changing the bus to48V: driver voltage,
regenerative headroom, PSU, brake/dump and thermal duty all require reconciliation.

Candidate transmission: pitch two belt stages20:40 and20:80 =8:1, yaw20:30 and
20:80 =6:1. The large pitch pulley is127mm pitch diameter rather than255mm for
a single20:160 stage. This adds a shaft/bearings and compliance; budget includes
them. Use metal shaft clamps/hubs and small metal pulleys. A large printed pulley
may be a replaceable low-speed test part after concentricity/tooth-load proof,
not an unqualified emergency brake load path. The full assembly now includes both
staged drives, supported shafts and mounting plates. Purchased interfaces remain
provisional. `ratio_trade_study.py` compares4–20:1 requirements including motor
J*n² and a conservative reading of the48V pull-out graph. Larger ratios require
packaging and mass updates; final running/thermal qualification is still open.

Extension:36T GT2 has72mm travel/rev;1.2m/s requires1000rpm. A NEMA17 label or
0.6Nm holding rating cannot justify torque at1000rpm. The9mm belt, motor, driver,
36T pulleys, brake/fault strategy and working-tension rating require selection
against the generated **dynamic guide-friction** force, not the old7N estimate.
Choose GT2 only after tooth shear/cord load and span stretch data; HTD3/5 may improve
robustness but changes belt thickness and internal packaging. Lead screw and worm
drives are poor default choices for the requested speed/backdrivability. A geared
brushed37D motor is not a shortcut: Pololu limits its gearbox to about0.98Nm
continuous and2.45Nm instantaneous, with extrapolated stall values explicitly
unsuitable for continuous selection ([manufacturer](https://www.pololu.com/category/272/24v-37d-metal-gearmotors)).

Do not add an assumed counterbalance percentage. The rear extension motor already
contributes a signed gravitational first moment; its extra inertia is also counted.
A future spring should approximately fit the midpoint gravity curve and be measured
at min/mid/max reach and all pitch angles. It cannot cancel extension-dependent load
everywhere, and it can overbalance the short arm. High-speed servo/BLDC substitutions
remain candidates if sourced with encoder, driver and thermal data; no industrial
upgrade is hidden in the current budget.

## Power and safety procurement gates

A [Mean Well LRS-350-24](https://www.meanwell.com/Upload/PDF/LRS-350/LRS-350-SPEC.PDF)
is14.6A/350.4W, not15A/360W. It is a candidate only after drive current and wiring
are known. Its nameplate is not evidence it can absorb regenerated energy. The
motor-bus dump must remain on the driver side of the contactor; the logic/brake
sequence needs appropriate hold-up and measured power-loss behavior. A motor-side
brake does not restrain a broken belt: controlled test containment and a separate
mechanical retention strategy are still needed. Hardware E-stop must remain effective
through MCU, host or software failure. An automotive relay with no appropriate DC
interrupt rating is rejected. Stop architecture is not safety-certified by this review.

## Cost decision

The complete machine is presently above the$500 cash ceiling. Do not remove
E-stop, brake, dump, independent feedback, fusing or guards to make the sum look good.
Buy/borrow only what is needed for a restrained extension test rig and claw drop-test
first. Existing hardware, a borrowed PSU/MCU and already-owned filament may bring a
rig below$300; record those as **owned**, not zero-priced new purchases. The complete
three-axis vision machine under$500 is not defensible with the documented bill.
The cheaper metric35x1.5 outer/25x1 inner variant lowers mass but was not locally
quoted; do not substitute until stock fit, wall, material and belt corridor are checked.

### Concrete budget-compatible next build

`bom_restrained_rig.csv` is an **alternative complete purchase basket**, not extra
parts to add to the full BOM. It targets a horizontal, bench-clamped telescope and
three-claw drop-test fixture: no yaw/pitch motors, no gravity-loaded arm and no stereo
cameras. It keeps the full-stroke tube architecture, independent hardware E-stop/DC
cutoff, branch fuse, switches, downstream low-energy bus clamp and local pinch guards.
A24V60W enclosed wall adapter avoids an exposed mains build. The MCU allowance
uses the user's owned ESP32 at$0; the economy encoder/driver/motor allowance is$45.
**These are unquoted candidates; the rig needs an MCU firmware port and an exact
drive with verified enable/fault/current behavior before purchasing.** Existing
Teensy firmware does not automatically run on ESP32. Exact board identification
is pending; no pin mapping or timing qualification is inferred.

Rig purchase parts total**$360.10**; with12% shipping/tax and15% reserve the planning
cash budget is**$463.81**. This includes entire PETG/TPU spools, assumes an existing
printer/PC/rigid bench/tools, and buys no new camera. The user owns no PSU, camera
or filament; the unknown servo has not been credited as qualified. Do not claim
that low price supplies a complete catching robot. The rig measures extension
friction, maximum repeatable speed under load, guide wear, current and claw capture
behavior. Begin below150mm/s, use only low-height/low-energy foam drop tests and
do not mount the rig as a freely rotating gravity-loaded arm.

The cash total is under$500 by only$36.19, so obtain the exact component quotes
before authorizing that scope. If a suitable drive or supply pushes the rig over,
reuse the owned ESP32 after a qualified port, borrow a safe supply or begin with passive
guide/claw tests; keep the protective functions. A complete manual three-axis
budget alternative can reduce vision expense and use economy motors, but those
savings alone do not close the full machine's cost gap or validate high-speed motion.
