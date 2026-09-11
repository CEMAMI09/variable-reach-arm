# Telescope drive detail — current prototype

Problem → belt ends, motor support and end stops lacked a credible load path.
Why it matters → an attractive telescope could slip, jam or eject its inner tube.
Implemented → rear plug and bolted belt clamp, supported front idler, common-bolt
motor bracket, split stop collars, smooth steel pins and keyed replaceable TPU pads.
Tradeoff → additional hardware and moving mass; these are qualification prototypes.

## Geometry and assembly

The current single sliding tube travels 500 mm. Nominal guide spacing is 690 mm
retracted and 190 mm extended; tube overlap is 740 and 240 mm respectively.
The rear plug is 32 mm long and nominally 22.025 mm square inside the 22.225 mm
bore. Measure actual corner radii, straightness and extrusion size before printing.
Two recessed M3 bolts retain it; its relief channels clear the guide fasteners.
A 26 x 24 x 2.2 mm metal clamp cap and four M2 screws trap the two open-belt ends.
The clamp model compresses the belt from 1.38 to 1.20 mm locally. This is an
allowance, not a qualified tooth profile or verified gripping preload.

The extension motor faceplate shares two M4 bolts and metal compression spacers
with the rear stop collar. At the front, a split outer-tube collar supports a
bridged idler bracket. Two purchased 625 bearings (5 x 16 x 5 mm), a ground 5 mm
shaft, inner-race spacers, metal caps and shaft collars support the metal pulley.
The collar can be manually shifted approximately +/-2 mm before clamping to set
belt tension; clearance over that adjustment and actual preload remain to be tested.
Do not tension by bending the bearing support. Install cap nuts before the pulley.

Install guide nuts and rear plug first, thread and clamp the belt ends, fit the
inner tube, assemble the idler bearings and pulley, set both stops, then tension
with the front collar. Check full travel by hand before attaching motor power.
Mark collar locations to detect slip. Caps and belt-clamp screws must remain
accessible without separating the entire arm from its base.

## Stops and independent load screen

Four 5 mm steel pins project into the outer-tube corner corridors at z=12 mm,
above the side guide pads. Pins are retained by steel caps; no threads are cut
into the thin tube wall. The nominal soft-contact/hard-contact positions are
-2/-5 mm and 501.5/504.5 mm. Normal commanded travel remains 0–500 mm.
The maximum hard-stop position still leaves 185.5 mm guide spacing.

`engineering.review_sizing.extension_hardstop_screen` uses current effective
slider mass including reflected extension motor inertia. It checks one pin taking
first contact, 4 mm unsupported length, a 3 mm assumed stopping stroke and an
illustrative twice-mean impact force plus motor force. It assumes only 250 MPa
steel yield. The 3 mm pad thickness is NOT evidence of 3 mm usable stopping stroke.
A real pulse can exceed this screen. Printed lug bending, collar axial slip,
tube bearing, TPU compression and pin grade must be proven separately.

The CAD mass screen estimates 55 g for the rear guide/anchor group and 135 g for
the front idler assembly; dynamics allow 65 g and 150 g respectively. Stop collars
are fixed to the outer tube; their allowances are 90 g each. These are density
estimates, not weighed parts. Do not silently omit this hardware from inertia.

## Remaining release gates

Select actual belt/pulley SKUs and verify tooth engagement, tension, clamp pullout,
fatigue and repeatable tension adjustment. Qualify collar grip and single-pin stops
on a restrained horizontal rig. Measure extension force/current throughout travel,
including tolerance extremes. Confirm supplier bearing fits and all screw grip
lengths. Complete guards and flexible wiring. Full-speed hard-stop tests require
containment and a measured energy/force limit; start with hand and low-energy tests.
