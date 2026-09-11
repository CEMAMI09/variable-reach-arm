# Full Rev B CAD — revised assembly status

The current connected full-robot prototype uses an 850 mm shoulder, windowed
3 mm cheeks and stock-angle stiffeners. It preserves yaw +/-70 degrees and pitch
-15 to +70 degrees. Raising the shoulder corrects the earlier 650 mm geometry's
sampled high-pitch collision. Five final poses at retracted, intermediate and full
extension have 381 valid modeled parts and no unresolved part intersections above
the collision screen threshold. These samples are not continuous swept clearance.

The raised yaw structure adds about 0.866 kg relative to the old baseline after
windowing; total added yaw CAD group mass is 5.221 kg. Telescope rear anchor,
stop collars/pins/pads, motor bracket and supported front idler are now modeled.
Claw springs, stops and short working tendon segments are modeled; actual servo
termination/equalizer and complete cable routing remain unfinished. See the new
`telescope_drive_design.md` and `claw_actuation_design.md` for precise limitations.
The older findings below record design history; unresolved 650 mm collisions refer
to that superseded geometry. This model remains NOT manufacturing released.

## Problems corrected after independent round 2

- **Yaw pulley/cage collision → blocked rotation → moved cage posts to x=±40,
  y=±65mm with matching deck holes and a 130×150mm upper deck → slightly larger
  stationary deck.** Posts now clear both the 80T pitch disk and stage-2 tangent;
  merely moving posts to x/y=±52mm cleared the disk but still hit the tangent.
- **Floating/intersecting jack bearings → unsupported shafts and impossible stack
  → full 8mm radial carriers, 3mm removable caps and common M4 patterns.** Pitch
  bearing starts are y=91 and 146mm; their pulleys remain centered at y=110/132mm.
  Yaw bearing starts are z=390 and 468mm. Opposite stock plates use 22mm shoulder
  apertures. Supplier fits, shims, inner-race collars and rated hubs remain gates.
- **Duplicate brace links/bolts and orthogonal bolt crossings → impossible assembly
  → stacked link planes 28/31mm, one shared screw per pair, upper heights 250/360mm,
  matching crush sleeves and 24mm lower pivots.** The unequal brace heights avoid
  broad-link crossings, including the intermediate positive-X/positive-Y members.
- **Yaw shaft/deck/sleeve collisions → blocked rotation → removed the 390mm cross
  sleeve, provided actual deck apertures, and mounted the yaw motor face at z=398mm
  against the deck underside with register and mounting bores.** Main-shaft shoulder
  and column-to-deck fastening details still require an exact hardware drawing.
- **Collar/hub overlap and unbored hub spacer → impossible stack → 4mm inner-race
  spacer at z=513–517mm, collar at 517–525mm, and common M6 holes through the hub
  spacer and turret.** Actual inner/outer-race axial shims remain unqualified.
- **Backplate/turret and motor/guard intersections → cut-in geometry → relieved the
  backplate below the turret/foot interface and moved the outer guard plane to
  y=250mm.** Complete guard sidewalls, brackets and brake/motor access remain open.
- **M4 saddle bolt too close to L-shoe upright → trapped nut/washer → widened the
  shoe foot and moved the rail/flange/stub interface outward by 5mm.** Bolt axis to
  upright distance is now 7mm, admitting nominal M4 hardware and a small socket;
  validate the actual socket and washer series. Matching turret/yoke foot holes
  were also added. Bolted clamp slip and thin tube crushing still require proof.
- **Narrow verification missed most failures → false confidence → added a broad
  bounding-box/boolean collision report.** Only exact own-belt/own-pulley pitch
  representation pairs are ignored. Cable routing-envelope contacts are reported
  separately; other purchased envelopes are not blanket-exempted.

Ratios remain pitch 20:40 × 20:80 = 8:1 and yaw 20:30 × 20:80 = 6:1. Supplier belt
lengths must match the intended centers with real tension adjustment. A pitch-path
ring is not a printable pulley or proof of supplier tooth engagement.

## What the independent headless checks show

The revised neutral assembly at extension 250mm, yaw 0°, pitch 20° produced zero
unresolved solid collisions after the parallel claw-mount corrections. At the
pre-final rail-access revision, added mass screens were stationary 6.5557kg,
yaw-only 4.3563kg, pitch-added 1.1238kg; yaw-only inertia was 0.099994kg·m². The
latest `_checks.json` and mass CSV generated from source supersede these snapshot
figures. Telescope, shoes and claw are separately imported and excluded from these
added-part totals; 4.3563kg is not the complete mass carried by yaw.

Sampled poses at pitch −15°, yaw ±70°, extension 0/500mm were clear. At extension
0mm, pitch 35° and 40° with yaw −70°, 0°, +70° were clear in modeled solids. At
45° pitch all three yaw samples collided with the rotating turret (about
296.6mm³); yaw 0° also collided with the upper jack support (~869.4mm³) and guard.
Thus onset is between the sampled 40° and 45° cases, not at 70° alone. This is not
a continuous collision-free range certificate or a new software operating limit.

At pitch 70°, the rear outer tube, retracted inner tube, extension pulley and
extension motor enter the yaw stack. At yaw 0°, extension motor/lower deck overlap
was about 11,291mm³; at yaw 70°, extension motor/yaw motor overlap was about
31,238mm³. Outer tube/hub and outer tube/turret interference persist with yaw, so
moving one guard or motor cannot solve the whole sweep. Extended stroke removes
some retracted-inner contacts but does not remove the fixed rear boom/motor conflict.

## Remaining desk-design decision: clearance over the required pitch range

The rear extension motor is about 275mm behind pitch. At 70°, its axial center
alone descends 275 sin(70°) ≈258mm; the rear 250mm outer tube descends ≈235mm.
Cross-section/motor-body depth adds further clearance demand. Retaining the current
650mm shoulder above the yaw stack therefore needs an architectural change.

1. **Lower the entire yaw stack and use a taller shoulder yoke.** Approximately
   150–170mm more vertical separation is a useful first packaging study, not a
   solved clearance value. Shortening the 50×50×2mm column by 150mm saves about
   0.156kg, while simply extending both 160×3mm yoke cheeks by 150mm adds about
   0.389kg before cutouts/gussets. Plain taller plates are not adequate by default:
   a cantilever height increasing from roughly106 to256mm raises a comparable
   bending compliance by about(256/106)^3 ≈14.1. Use triangulated/boxed stock load
   paths and repeat bearing alignment, stiffness and full sweep checks.
2. **Raise the shoulder with the yaw stack fixed.** Similar 150–170mm relative
   separation would put the pivot near800–820mm. It preserves boom inertia about
   pitch but adds yoke mass and height, changes the world pivot height, and raises
   base overturning moment. Tall thin printed cheeks are not an acceptable shortcut.
3. **Move pitch forward of yaw.** A small shift that clears the 70° endpoint can
   still collide at intermediate pitch. Study the whole sweep; offsets of order
   0.3–0.4m may be needed around this broad stack. Such an offset substantially
   increases yaw inertia: for pitch-moving mass M, first moment S and shift d,
   ΔI_yaw ≈M d²+2dS at horizontal pitch. At d=0.35m the M d² term alone is about
   0.29kg·m² for M≈2.4kg, before the positive first-moment term. This conflicts with
   low inertia, enlarges footprint and requires new noncoincident-axis kinematics.
4. **Shorten the rear telescope.** The rear overhang comes from the combination
   of 500mm stroke, 240mm minimum overlap and 700mm mouth reach. Cutting its tail
   loses either overlap, stroke or retracted reach unless the guide architecture
   changes. More stages add distal guides, compliance and routing complexity.
   Recalculate all lengths and inertia before treating this as a cheap cut-and-drill fix.

These are quantified options, not approved replacement designs. Keep the complete
hardware qualification lock in place. Do not quietly cap pitch to40° and call the
original 70° objective complete. A restricted unpowered fit fixture is a separate
test scope and must be described as such.

### Implemented clearance comparison

The builder now accepts `pivot_height_mm=850, stiffened_yoke=True` for a separate
raised-shoulder study. It preserves the lower turret interface at541mm, extends
the metal cheeks to the new bearing height and adds bolted stock-angle edge
flanges. Rear angle legs are trimmed to15mm to clear the pitch-drive backplate;
front legs remain30mm. These are connected solids with M5 clearance bores, not
floating reinforcement graphics. Required world geometry remains650mm in the
shared baseline until the architecture comparison is resolved.

Root independently checked extension0mm at (yaw,pitch)=(0,20),(0,70),(-70,-15),
(70,70): no unresolved modeled-solid intersections. A preceding plain-yoke height
study also cleared pitch−15/20/40/55/70 at yaw0. These are sampled checks, not a
continuous clearance certificate. Cable contacts remain separately unresolved.

The stiffened variant's yaw-added mass is5.480kg versus4.355kg baseline: **+1.125kg**.
It preserves distal/pitch mass but increases yaw load, total mass and base height.
This is a concrete fallback for clearance, not an accepted optimum. Evaluate
lower yaw-stack placement and lighter boxed/triangulated yokes before adopting it.
Bolted-joint compliance, bearing alignment, overturning load, full sweep and BOM
still require analysis. The variant is saved separately as
`VariableReachArm_RaisedShoulder_Study.FCStd`; the normal full assembly stays active.

## Manufacturing and verification gates still open

- Resolve the rear sweep architecture before releasing the complete frame or
  freezing expensive motor/reduction procurement.
- Freeze supplier-specific motor, brake, shaft, bearing, pulley/hub and belt data;
  add actual flanges, collars, keys, shoulder faces and wiring connectors.
- Close extension belt anchorage, motor bracket support, both end-stop force paths,
  guide adjustment and claw spring/tendon/release geometry.
- Complete mounting bolts/nuts, wrench/socket access, assembly order, cable loop
  routing and complete guards. A matched hole pattern is only part of an assembly.
- Recalculate moving mass/inertia, stiffness, bearing reactions, motor torque-speed
  demands and BOM from the final architecture. Verify unpowered fits, then isolated
  restrained low-energy subsystem tests under the existing hardware safety gates.

The new neutral CAD is substantially more connected and inspectable. The upper-pitch
collision remains a major unresolved desk-design flaw, so full manufacturing and
autonomous-motion readiness remain false.
