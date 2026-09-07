# Print & Buy Cut-List — Variable-Reach Arm

Regenerate STLs anytime (FreeCAD):

```bash
/Applications/FreeCAD.app/Contents/MacOS/FreeCAD -c '
import sys; sys.path.insert(0,"cad/scripts"); import export_printables as EP; EP.main()'
```

Source: `cad/scripts/export_printables.py` → outputs `cad/stl/*.stl` + `cad/stl/MANIFEST.csv`.

---

## 1. Print cut-list (all files in `cad/stl/`)

| File | Qty | Material | Walls | Infill | Notes |
|------|-----|----------|-------|--------|-------|
| `PitchCheek_L.stl` | 1 | **PETG** | 4 | 40% gyroid | 6001 pocket, NEMA23 holes, M4 inserts |
| `PitchCheek_R.stl` | 1 | **PETG** | 4 | 40% | Same as L |
| `NEMA23_MountPlate.stl` | 2 | **PETG** | 4 | 40% | Yaw + spare / pitch assist |
| `NEMA17_MountPlate.stl` | 1 | **PETG** | 4 | 40% | Extension motor |
| `YawHubClamp.stl` | 1 | **PETG** | 4 | 45% | **Measure yaw tube OD; ream ID if needed** |
| `Guide_1.stl` | 1 | **Nylon or PETG** | 4 | 50% | Bore vertical; UHMW tape ID |
| `Guide_2.stl` | 1 | **Nylon or PETG** | 4 | 50% | Same |
| `ExtensionStop_Min.stl` | 1 | **PETG** | 5 | 60% | Retract bumper |
| `ExtensionStop_Max.stl` | 1 | **PETG** | 5 | 60% | Extend bumper |
| `CableGuide.stl` | **3** | **PETG** | 3 | 30% | Print 3 copies |
| `CatcherHub.stl` | 1 | **PETG** | 4 | 40% | Clamp on CF inner tip |
| `CatcherAdapter.stl` | 1 | **PETG** | 3 | 30% | Behind hub |
| `CatcherFunnel.stl` | 1 | **TPU 95A** | 3 | 15% | Soft entrance |
| `CatcherCradle.stl` | 1 | **TPU 95A** | 3 | 20% | Soft backstop |
| `CatcherRib.stl` | **3** | **PETG** | 3 | 30% | Print 3 |
| `CatcherFinger.stl` | **3** | **PETG** | 4 | 40% | Articulated claw, open pose |
| `CatcherTipPad.stl` | **3** | **TPU 95A** | 3 | 20% | Slip/glue on distal tips |
| `HingePin.stl` | **6** | **PETG** (or buy Ø6 steel dowel) | 3 | 100% | 2 pins × 3 claws |
| `ElectronicsEnclosure.stl` | 1 | **PETG** | 3 | 25% | Hollow + insert posts |
| `ElectronicsEnclosure_Lid.stl` | 1 | **PETG** | 3 | 20% | Vent slots |
| `BaseFootSpacer.stl` | 4 | **PETG** | 3 | 30% | Optional under feet |

**Total unique STLs:** 21 · **Approx part count:** ~40 pieces

Do **not** print: base plate, CF tubes, shafts, bearings, pulleys, motors (buy).

---

## 2. Slice settings (recommended)

### PETG (structural)
| Setting | Value |
|---------|-------|
| Nozzle / bed | 240°C / 80°C |
| Layer | 0.20 mm |
| Nozzle | 0.4 mm |
| Walls / top / bottom | 4 / 5 / 5 |
| Infill | 40% gyroid (60% on stops) |
| Speed | 40–55 mm/s |
| Cooling | 30–50% |
| Supports | As needed (cheeks usually flat; hub flange-down) |

### TPU 95A (funnel / cradle / tip pads)
| Setting | Value |
|---------|-------|
| Nozzle / bed | 225°C / 45°C |
| Layer | 0.20 mm |
| Walls | 3 |
| Infill | 15–20% |
| Speed | 20–30 mm/s |
| Retraction | Minimal (direct drive preferred) |
| Cooling | 0–20% |

### Orientation cheat-sheet
- **Cheeks / motor plates / lid:** flat on largest face  
- **Guides:** **bore vertical** (Z)  
- **Hub:** flange up or down; clamp slot vertical OK  
- **Funnel:** open axis vertical  
- **Fingers:** flat on link face  
- **Pins:** standing (Z = length) or buy metal dowels  

### Post-print
1. Heat-set **M3** and **M4** brass inserts (soldering iron or dedicated tip).  
2. Line guide IDs with **UHMW tape**; target ~0.2 mm clearance on measured inner-tube OD.  
3. Ream `YawHubClamp` / `CatcherHub` bores to fit **your** stock tubes.  
4. Assemble each claw: 2× `HingePin` + `CatcherTipPad`; check open/close by hand.  
5. Epoxy hub to CF inner tip **after** dry-fit; do not crush CF with overtight clamps.

---

## 3. Buy list (cannot print — required to work)

Use `engineering/bom.csv` as the shopping list. Minimum to move and catch foam:

| Category | Items |
|----------|--------|
| Structure | Al base 300×300×6; CF outer Ø40×750; CF inner Ø32×750; yaw tube/shaft stock |
| Joints | Ø12×120 pitch shaft; 4× 6001-2RS; thrust washers; 4× Ø12 shaft collars |
| Actuation | 2× NEMA23 closed-loop; 1× NEMA17 closed-loop; HTD5 yaw 6:1 + pitch 8:1 kits; GT2 extend belt/pulley; pitch gas/torsion spring; 9g servo |
| Control | Teensy 4.1; 24V≥15A PSU; 5V buck; e-stop + relay; limit switches ×2; IR break-beam |
| Consumables | M3/M4/M5 fasteners; M3/M4 heat-set inserts; UHMW tape; epoxy; Loctite 243; wire; foam balls |
| Optional later | USB camera(s); acrylic shield; string pot |

**Filament to buy:** 1 kg PETG + 1 kg TPU 95A (partial use).

---

## 4. Readiness / honesty check

| Item | Status |
|------|--------|
| Feature-rich STLs (bores, NEMA holes, inserts, hub, enclosure cavity) | **Yes — regenerated** |
| Fit to *your* exact motor brand / tube OD without sanding | **First-article adjust expected** |
| Drop-in belt center distances / full exploded assembly drawing | **Not production-released** |
| Firmware flash-and-catch | **Skeleton only** — see `docs/bringup.md` |
| Can print + buy + dry-fit structure now | **Yes** |
| Can expect first-power mid-air catch without bring-up | **No** |

**Bottom line:** STLs are now a real print cut-list suitable for prototype fabrication. Treat hole patterns and tube IDs as **nominal** — measure motors/tubes, adjust bores, then assemble per `docs/bringup.md` milestones.

### Critical dimensions (nominal)
- Guide ID ≈ inner OD + 0.6 mm before tape  
- 6001 pocket ≈ Ø28.3 × 8.2 deep; shaft through ≈ Ø12.5  
- NEMA23 hole square pitch **47.14 mm**; NEMA17 **31.0 mm**  
- Catcher hub bore ≈ inner OD + 0.25 mm; clamp with 2× M4  
- Finger hinge pins **Ø6**  

### Fastener summary
| Size | Approx qty | Use |
|------|------------|-----|
| M3×8–16 | 50 | Guides, enclosure, fingers, ribs |
| M4×12–20 | 30 | Cheeks, clamps, NEMA23 |
| M5×16 | 8 | Base / column |
| M6 | 4 | Leveling feet |
| Brass inserts M3/M4 | 30+ | All printed screw bosses |
