# Value-focused fabrication decisions — Rev B

The objective is low total cost for useful catching performance, not maximum printed
mass. Print the complex shapes, replaceable interfaces and fixtures. Buy inexpensive
standard parts wherever stiffness, heat, wear or safe load retention dominates.
The complete machine remains a design study; the current fit STL manifest is not a
release of every part described below.

## BOM changes implemented in this pass

Problem → the bill omitted M2 guide hardware and a separate servo supply and called
the rigid claws TPU. Why it matters → missing purchased packs and a noisy/overloaded
logic rail invalidate both the cash budget and electronics integration. Implemented
→ both current BOMs now include the 24 M2x8 screws, 24 nuts and 24 thin washers within
a larger hardware allowance, a separate $8 unquoted servo-regulator allowance, rigid
fingers in structural filament, and TPU for pads. Reduction-kit descriptions exclude
the six separately counted 6001 bearings and use the common filament line for any
qualified printed large pulley. Tradeoff → honest cash totals rise $16.74 including
allowances; nothing about these entries qualifies a part for ordering.

Full machine: $1,131.30 parts, $135.76 shipping/tax allowance, $190.06 redesign
reserve, **$1,457.12 planning cash**. Alternative restrained telescope/claw rig:
$386.10 parts, $46.33 shipping/tax allowance, $64.86 reserve, **$497.29 cash**.
Shipping/tax is rounded to cents, then reserve is rounded on that subtotal.
These are alternative
baskets, not additive. Most prices remain explicitly unquoted. The existing PC,
printer, rigid bench and ordinary tools are excluded; confirm printer/bench access.
No camera, PSU or filament is counted as owned. The ESP32 is $0 purchase cost but
needs a qualified firmware port. The unknown owned servo receives no speculative
credit. Miscellaneous EE parts are credited only when identified and suitable.

The raised-shoulder CAD alternative is not selected or included. Exact motors,
ratios, bus voltage, brake, guard dimensions and camera synchronization can change
this budget materially. In particular the currently cited 48 V motor curve does
not qualify the candidate 24 V power system. The $480.55 rig is not a three-axis
catching robot and has only $19.45 of headroom under $500.

## Where printing gives good value

The detailed process and hardware requirements are in `cad/drawings/print_guide.md`.
Default to one PETG spool for cold housings, claw fit parts and jigs, plus TPU only
for compliant parts. Avoid purchasing PETG, ASA, nylon and CF nylon simultaneously.
Use ASA or qualified nylon only when measured temperature, creep or impact results
justify their printing difficulty and cost. Manufacturer printability/material
properties support this starting choice; they do not establish structural allowables
for our geometry ([Prusa material guide](https://help.prusa3d.com/category/material-guide_220)).

Print claw fingers, palm, servo cradle/straps, sensor brackets, guards against finger
access, wire clips, bearing caps, drill templates and fit coupons. Conditional
hybrids include tube clamps, bearing carriers and large reduction pulley webs with
metal hubs. These avoid custom machining and exploit geometry that flat stock cannot
easily provide. Use bought acetal shoes for the actual small sliding contact surfaces;
generic filament friction/wear is not qualified by appearance. Engineered printed
bearing polymers can work, but require specific material/testing rather than generic
PETG substitution ([igus bearing materials](https://www.igus.com/3d-printing/3d-printed-bearings)).

Use drilled aluminum stock for long tubes, hot motor/tension plates, thin stiff
cheeks/rails and critical stop load paths. Use real steel shafts/pins, bearings,
belts, metal motor pinions, springs and brake parts. Their standard mass-produced
versions provide better value than spending iteration time trying to reproduce
precision or fatigue properties in FDM. A large printed base/column consumes a spool
and print time while creating compliant joints; triangulated stock is the better
starting architecture. Containment uses suitable polycarbonate/frame, not an
untested thin printed cover.

## Concrete value choices and savings boundaries

1. **Preserve aluminum tubes; defer carbon fiber and premium motors.** The current
   model already spends far more than $500. A $50 upgrade for 5% improvement is not
   accepted by default. It must remove a measured limiting failure, save other parts,
   or materially improve repeatable catch success. There is no measured performance
   basis to purchase carbon fiber now. Aluminum offcuts also provide test coupons.
2. **Reuse the ESP32 and possibly the servo.** The board already saves $35 versus the
   earlier full-machine MCU allowance ($8 versus the old rig MCU allowance). Servo
   credit cannot equal the whole $20/$16 claw-hardware line because springs, tendons
   and pins remain required. Identify its model and bench-test travel/current first.
3. **Print large pulley webs only after tooth/runout qualification.** Bought metal
   hubs and small pinions remain. There is no booked cash saving yet because current
   transmission kit prices are allowances, and a smooth CAD envelope is not a
   printable timing tooth profile. Obtain like-for-like metal and hybrid quotes.
4. **Use stock drops and common hole sizes.** The $70 frame allowance assumes basic
   cutting/drilling, no outsourced machining. Quote the final cut list locally;
   do not replace a needed metal load path with plastic merely to avoid one drill
   operation. Printed hole-position jigs are a useful low-cost aid, followed by
   measured coaxiality/alignment checks.
5. **Test a low-cost foam contact insert before buying an entire TPU spool solely
   for one palm.** A mechanically trapped foam pad could reduce the full $24 (rig
   $22) spool cash requirement, minus foam and retention cost. This is a conditional
   experiment, not a booked saving: bounce, durability and capture retention need
   comparison and CAD retention details must be updated. Rigid fingers remain.
6. **Stage purchases, reuse the same telescope.** The restrained rig avoids buying
   angular motors and cameras before friction/claw viability is measured. This lowers
   immediate spend, not final full-machine cost. Do not buy all rig parts and then
   rebuy duplicated full-machine parts; credit actual reusable purchases line by line.
7. **Prefer targeted stiffness fixes over blanket infill or material upgrades.**
   Reorient a part, shorten a lever, increase bearing separation or add a rib before
   choosing expensive filament. Preserve mass at the tip. Weigh complete assemblies;
   sliced plastic cost is not complete hardware mass or full-spool cash cost.

Never count removal of brake, independent cutoff, fuses, required feedback or guards
as a value improvement. Instead reduce the qualified operating envelope or build a
restrained subsystem until the complete safety function is affordable. No shopping
list currently demonstrates the full requested high-speed capability below $500.
