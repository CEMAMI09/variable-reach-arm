# Compact V1 print-readiness pass — 2026-09-08

## Release decision

Nine small fit-check files may be printed for unpowered dimensional testing. The entire compact robot is NOT ready to manufacture. A closed manifold mesh and successful slicing do not establish a connected, complete machine. The 44 exported CAD parts include five coupon geometries; the development quantity of 80 includes those coupons. Missing drive/wrist/restraint interfaces are desk-design work still to be completed.

## Corrections implemented

- Claw palm mounting holes intersected servo-carrier adjustment slots → fasteners could not seat independently → moved the four interface holes to X=±10, Y=0/10 mm → narrower mounting pattern needs matching wrist design → code, notes and STLs updated.
- Shoulder bearing pockets broke through the 200 mm plate top → insufficient bearing containment → raised cheek/outboard plates to 215 mm → extra material and printer-envelope constraint → regenerated valid solids. This is not a bearing-load qualification.
- Large gear lightening holes disconnected the hub → visually plausible but unusable mesh → reduced hole radii → some mass added → single-solid validation passes.
- Gear teeth lacked nominal printing backlash → binding likely → relieved tooth thickness by 0.12 mm on each gear, nominal pair clearance 0.24 mm → more backlash than ideal gears → 14 sampled mesh positions clear; actual print fit still needed.
- Motor gear retention initially required a bolt crossing the shaft → impractical motor-shaft modification → tangential split-hub clamp clear of shaft plus D-bore torque transfer → printed clamp creep remains possible → revised hubs and mesh exports. Final axial retention not qualified.
- Round saddle sockets relied on friction for pitch torque → potential slip → blind D-shaped sockets → generic shaft requires measured filing → implemented, while full stubshaft retention remains outstanding.
- Rear guide assumed 0.30 mm tape while candidate BOM names 0.13 mm → wrong guide clearance → use 34.14 mm ring OD plus two 0.13 mm tapes = 34.40 mm against 34.80 mm bore → adhesive/tape thickness needs measurement → CAD and docs synchronized.
- Front guide M3x12 adjusters were too short for the flange stack → inadequate adjustment reach → changed candidate to M3x16 → verify engagement and tip contact on real parts → documentation corrected.
- Telescope fit checks previously required long tube segments → wasted material before joint verification → added cropped male/female coupons using the exact production spigot, countersinks and nut paths → 41.9 g approximately for the pair → exported and sliced.
- Heavy bearing gauge was simplified into six joined annular cups → lower filament cost and additional 22.3/22.4 mm options → pocket cuts must follow web union → final modeled bearing clearance check caught and removed a web obstruction. Notched end identifies 21.9 mm pocket.

## Verification

FreeCAD 1.1 validates all 44 shapes as single connected solids; all closed STL meshes pass PrusaSlicer 2.9.6 manifold and slicing checks. Slicing records include SHA256 of every verified STL; packaging rejects stale records. Generic check uses 0.4 mm nozzle, 0.20 mm layer, six perimeters, five top/bottom layers and 25% gyroid. Actual printer and filament profile selection remains with the operator; no G-code is delivered.

Claw clearance: 51 sampled positions from -25 to +25 degrees, nominal carrier included, rod closure checked. Purchased hardware excluded. Gear pairs: 14 rigid pose samples, excluding material/thermal deformation. Bearing gauge: actual 22 mm OD / 8 mm ID / 7 mm bearing envelope seats without modeled interference in pockets ≥22 mm; the 21.9 mm option intentionally has interference.

## Do before bulk printing

1. Close telescope belt drive, anchors, motor/idler supports, physical stops and sensor mounts.
2. Build the wrist interface using actual servo/horn dimensions; verify carrier output-axis position and shaft height.
3. Finish complete shoulder/yaw shaft lengths, bearing spacer/cap stack, gravity restraint, motor access and cable routing.
4. Check full compact assembly poses with hardware envelopes and intended clearances. The inventory-grid FCStd is NOT an assembled robot.
5. Reconcile the named candidate purchasing BOM: previous yaw/pitch belts and spring/tendon claw no longer match this development CAD; additional long M4 bolts, countersunk M3 joint screws, M2/M2.5 servo hardware and adhesive are needed. The old two-spool allowance is insufficient: current sliced inventory is about 2.70 kg before missing design parts/rework. Three spools is a minimum inventory allowance, not a new fixed total project quote.

## Physical fit information required

Actual Prusa model/nozzle, PETG profile, 608 bearing fit, PTFE tape including adhesive thickness, and actual servo/horn measurements. These are separate from the outstanding desk-design tasks above. Do not use missing measurements as justification to call unfinished interfaces complete.

Original/fair-version CAD remains preserved. No repository commit, hardware command, firmware flashing or powered test was performed in this pass.
