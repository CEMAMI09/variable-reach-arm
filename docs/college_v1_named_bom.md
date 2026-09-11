> **Print-CAD revision notice (2026-09-08):** This is the earlier candidate basket, not a purchase release matching the new development STLs. The current set slices to about 2.70 kg, exceeding its two-spool allowance. Printed spur gears and the two-link claw also require drive/fastener reconciliation. See the new print package README before ordering or bulk printing.

# College V1: named parts and maximum practical printing

This supersedes the earlier $705.64 allowance basket. That figure was not a
demonstrated minimum: it combined $547.86 of broadly estimated parts with $157.78
of shipping/tax and contingency. Its blanket metal-only recommendations for
bearing caps, belt clamps and small pulleys were too restrictive for this slow V1.

## Current cost

The revised 59-line candidate basket is **$368.47 in parts**. Allowing $45 shipping
and an illustrative 8% tax on parts plus shipping gives **$446.55 before repair
reserve**. An optional 15% repair/redesign reserve adds $66.98, giving **$513.53**.
Shipping is not a checkout quote and the tax rate is not a jurisdiction-specific
calculation. Seven lines totaling $109.52 have observed supplier prices; the
remaining named standard components/pack prices are explicitly estimates.

Parts divide into $40 filament, $57.52 motors/drivers/servo, $106 mechanical
hardware, $107.35 power/protection components, $45.60 control/sensing/wire, and
$12 assembly consumables/balls. No separate purchased shoulders, boom tubes,
pulley bodies, bearing caps, belt-clamp caps or large guard panels are charged.

The work Prusa has no printer-purchase charge. The exact model and usable bed size
are not confirmed. Two complete PETG spools remain in the cash list; slicing has
not established consumed mass. Work-supplied filament would remove $40 parts if
confirmed. Existing ESP32 and host PC are credited, but no unknown EE parts or
unidentified servo are silently credited. Access to ordinary hand tools, shaft
cutting and dimensional measurement is assumed; those tools are not in this parts
total. No camera, autonomous catching or throwing capability is included.

## Searchable items

`engineering/bom_college_v1.csv` now uses manufacturer part names or fully
specified commodity search names, rather than lines such as 'motion hardware'.
Quantity means purchase quantity: a ten-pack is counted as one pack, not as one
bearing. Pack contents and any unresolved fit are described in the specification.

Examples with observed prices on 8 September 2026:

- Three STEPPERONLINE **17HS19-2004S1** motors, $9.62 each:
  https://www.omc-stepperonline.com/nema-17-bipolar-59ncm-84oz-in-2a-42x48mm-4-wires-w-1m-cable-connector-17hs19-2004s1
- Three BIGTREETECH **TMC2209 V1.3**, SKU **1040000053**, $7.89 each:
  https://biqu.equipment/products/btt-tmc2209-stepper-driver
  The search excerpt showed an older $6.94; the opened current product page showed
  $7.89, which is the value used. No bulk or unearned coupon discount is assumed.
- MEAN WELL **GST60A12-P1J**, $19.40:
  https://www.bravoelectro.com/gst60a12-p1j.html
  The grounded C13 cord and appropriately rated barrel connector are separate.
- TowerPro **MG90S positional servo**, $4.99 listing:
  https://dfh.fm/products/mg90s-servo
  This is a candidate, not identification of the user's existing servo.
- Adafruit **6357 AS5600** sensors, $5.95 each:
  https://www.adafruit.com/product/6357
- Adafruit **2717 TCA9548A** multiplexer, $6.95:
  https://www.adafruit.com/product/2717
- Adafruit **819 roller microswitches**, $1.95 each:
  https://www.adafruit.com/product/819

Standard search names include **608-2RS 8x22x7 mm**, **625-2RS 5x16x5 mm**,
**400-2GT-6 timing belt**, **8 mm h6 ground shaft**, and metric fastener sizes.
These define commodity families; an estimated price does not imply that every
seller's material, pack contents or rating is interchangeable. The workbook keeps
the source/price-status column beside these entries.

## What becomes printed

The print list includes the base, yaw housing/turret, boxed shoulder/yoke,
inner/outer telescope shells, joint sleeves, rear plug, guide shoes, motor mounts,
all drive/idler pulley bodies, bearing caps, belt clamps/caps, collars/spacers,
hard-stop bodies, padded pitch catch cradle, friction-disk body, claw palm/fingers,
servo cradle/equalizer, sensor brackets, cable guides and guards.

The printed pulley design must use adequate tooth size and a split-clamp or D-flat
hub with mechanical axial retention. A metal grub screw in an unsupported printed
thread is not sufficient. Printed belt clamps use long toothed engagement and
steel through-bolts/locknuts. Printed bearing caps use broad annular ribs and
washers. Each is a fit/load-test candidate, not an automatic upgrade from metal.
The attached print manifest gives material/orientation/perimeter guidance and
explicitly labels its IDs as planned parts, not available released STL files.

Purchase actual bearings, smooth shafts, fasteners, small springs, reinforced
belts, line, friction/foam/PTFE facing, electronics and the small resistor heat
spreader. Printing these last items generally creates a large functional loss for
a small saving, or is not possible with an ordinary FDM printer. The goal is a
low-cost working demonstrator, not maximizing the printed percentage on paper.

## Changes enabling the lower estimate

The $60 external-driver allowance becomes $23.67 of named driver modules. Purchased
pulley/hub kits become $16 of belts plus printed bodies. The unnamed $35 brake
allowance becomes a candidate printed friction mechanism with purchased spring,
liner and preload bolt, backed by a padded catch cradle. The large supply becomes
a 12 V 60 W external adapter appropriate to investigating much slower, current-
limited operation. Guards and base structure move into the filament budget.

These are architecture changes, not equal-performance substitutions. The compact
scope remains roughly 350–550 mm reach, 200 mm stroke and light foam objects.
Loaded motor torque at the selected current/12 V, reduction ratio, printed tooth
life, telescope straightness, sensor mechanics and temperatures need engineering
qualification. The motor's 2 A/0.59 Nm holding rating is not credited at 1 A RMS.

The candidate friction restraint must hold worst-case gravity torque at maximum
extension and still leave enough motor torque to move against friction. Printed
worm gears are not assumed self-locking. A spring assortment is explicitly a
trial purchase; its exact rate has not been selected. If this approach fails,
the design and cost must be revised, not silently operated without restraint.

The new discrete relay/watchdog/overvoltage components are named circuit
candidates. Their schematic, threshold/hysteresis, startup state, motor cutoff,
inrush/DC contact rating, regeneration pulse rating and fault tests are unfinished.
The 12 V topology does not modify or energize the existing 24 V full-robot design.
Powering the ESP32 from host USB saves an extra regulator but requires correct
grounding and no 5 V backfeed. A listed relay does not make a certified safety system.

## Status

The BOM is now useful for looking up named candidates and challenging individual
prices. It is **not ready for ordering a complete compatible kit**: belt lengths,
spring/preload selection, screw grip lengths, compact CAD and the power/control
circuit still need closure. Existing full-size CAD/GIFs are preserved; they do not
depict this new printed compact robot. The higher-performance fair BOM remains
a separate unqualified proposal and has not been relabeled as this V1.
