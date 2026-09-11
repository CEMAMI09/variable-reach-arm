# Compact V1 two-finger claw: print and fit instructions

This is a real two-finger rigid grabber with one servo crank and two pinned rods. No net, springs or tendons. It is designed for restrained slow handling of a soft object up to 20 g. These are print-ready shapes, with the servo carrier and horn adapter explicitly **fit-test parts** until the actual servo is measured. It is not released for catching thrown objects.

## Print settings and inventory

All shapes are millimetres, flat on XY at Z=0. Use PETG, 0.20 mm layers, five perimeters, five top/bottom layers and 30% gyroid. A 0.4 mm nozzle is assumed. No supports are needed in the exported orientation. Inspect slicer preview and print a hole coupon first.

- Palm: one, 70 x 54 x 5 mm. Four M3 mounting holes at X=+/-10, Y=0 and 10 mm. Finger pivots at X=+/-22, Y=0 mm.
- Left finger and right finger: one each, 6 mm thick. Rear linkage pin 12 mm behind pivot; tip centre 44 mm ahead and 8 mm inboard. Two 2.2 mm holes in each finger retain bought foam pads with thread/ties. Do not buy a TPU spool just for these pads.
- Pushrod: two, 23.4094 mm hole-centre distance, 3 mm thick, 7 mm width.
- Crank adapter: one, 12 mm output pin radius, 3 mm thick. It bolts to a purchased servo horn; no printed spline.
- Servo carrier: one, 44 x 34 x 3 mm. Body window 24 x 14 mm. M2.5 flange slots cover 27-33 mm screw-centre spacing.
- Spacers: five 1 mm, one 2 mm, one 6 mm. Measured metal washers can replace them.

Every individual part fits even a Prusa MINI-sized bed. The exact Prusa model and material shrinkage still need checking. Ream printed 3.4 mm pivot holes only enough for the actual M3 smooth shank to rotate freely. Do not allow visible pivot wobble.

## Actual servo and horn fit gate

TowerPro lists the MG90S body as 22.8 x 12.2 x 28.5 mm and also lists width 12.4 mm in its configuration table. The carrier allows both nominal widths. Primary source checked 2026-09-08: https://towerpro.com.tw/product/mg90s-3/

That page does not establish a universal horn-hole pattern or a shaft-to-flange height for the user's unidentified servo and market variants. Print the carrier and adapter first. Dry-fit the actual hardware before printing the rest of the claw.

Use the original servo horn and its output screw. Bolt the printed adapter to that horn through **two M2 screws and nuts**, using its two 2.2 mm wide radial slots at Y=+/-2.5 and X=5.5-7.5 mm relative to shaft centre. A suitable disc/cross horn may require two drilled holes. Check there is enough horn material around both holes. If the supplied horn cannot accept this pattern, measure and revise the adapter or buy a compatible disc horn. Do not use only centre-screw friction to transmit torque.

Carrier centre is nominal X=-10, Y=-22 mm below the palm. Carrier M3 holes are at local X=+/-17, Y=+/-13. The palm slots allow +/-5 mm X adjustment. Set the actual servo output axis at **X=-12, Y=-20 mm**. The actual shaft Y position must be checked; if the body's available adjustment cannot achieve it, revise the carrier rather than forcing assembly.

The modeled crank occupies Z=10-13 mm above the palm bottom. Measure the real horn/shaft height. Use equal measured carrier spacers if necessary; if the modeled height cannot be reached with rigid support, revise the mount. The arm nose must clear the servo below the rear palm and must not fill the carrier aperture.

## Mechanical assembly

Use metal M3 bolts, washers and locknuts. A smooth shank should run through each moving hole. Do not tighten a nut against a moving printed link. Select screw lengths after measuring the full stack, with about two threads beyond the nut; keep protruding ends away from foam and fingers.

1. Mount palm through the four 20 x 10 mm pattern holes (rows at Y=0 and 10).
2. At each finger pivot, install a 1 mm spacer above the 5 mm palm, then the 6 mm finger. Finger bottom/top are Z=6/12 mm. Add washer and locknut and confirm free motion. M3 x 20 is a candidate pivot screw length, subject to actual washer/nut dimensions.
3. Electrically centre the servo before installing its horn, initially with rods disconnected. The modeled neutral shaft centre is (-12,-20); crank common pin is (0,-20); finger rear pins are (-22,-12) and (22,-12).
4. Left rear finger pin: 2 mm spacer above finger, then rod at Z=14-17 mm, washer and locknut. Right rear pin: 6 mm spacer, then rod at Z=18-21 mm, washer and locknut. M3 x 16 left and M3 x 20 right are candidate lengths; verify the actual stacks.
5. Common crank pin: crank top Z=13, 1 mm spacer, left rod, 1 mm spacer, right rod, washer and locknut. Both rods must rotate independently. An M3 x 16 or longer screw may be needed; measure before ordering packs.
6. With power disconnected, sweep every pose by hand and check screw heads, nuts and the underside of the fingers against the palm. Install foam pads and set the powered grip endpoint before any stall or hard jam.

CAD angles are not servo pulse widths. Do not send a generic 0-180 degree command. Begin with a narrow pulse sweep around a measured neutral and expand only after proving clearance. Limit the modeled crank to +/-25 degrees.

## Kinematics and checks

The common pin follows C=(-12+12*cos(a), -20+12*sin(a)). Each finger rear pin is P=(s*22+12*sin(t), -12*cos(t)), with side s=-1 or +1. The code solves the actual pinned-link equation distance(P,C)=sqrt(22^2+8^2), rather than moving disconnected links visually.

At crank -25 degrees, finger angles are +7.283 and -20.750 degrees. At neutral both are zero. At +25 degrees they are -11.148 and +0.483 degrees. Motion is asymmetric; it is a simple foam-object grabber, not a precision parallel gripper. Usable opening depends on pad thickness and object shape.

All nine unique printed shapes are valid single solids. Assembled printed-part overlap and rod closure checks are executed headlessly. They exclude purchased servo, horn and fasteners and do not prove continuous clearance, strength or durability. No universal powered-ready claim should be made until the servo fit gate passes.

## Acceptance before demonstrating

First fit the carrier and horn. Confirm the servo cannot shift under a gentle hand load. Hand-sweep the complete linkage with actual bolts, nuts, pads and the arm attached. All pins must rotate freely with no visible wobble. Route and restrain the servo wire outside the moving links.

Then use a current-limited supply for slow empty cycles, followed by a soft object of at most 20 g. Record voltage, current, heat and loosening. Stall torque is not continuous gripping torque. Keep hands outside pinch points. Likely failure modes are PETG creep, hole ovalization, horn-adapter loosening and pad detachment. Stop at a crack, loose interface, overheating or stalled servo.

This subsystem is specific to the compact printed V1. It does not release or replace the full-size fair-version claw without a separate design decision.
