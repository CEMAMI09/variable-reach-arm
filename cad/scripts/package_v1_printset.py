"""Package validated V1 fit meshes separately from unfinished build geometry."""
import json,shutil,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'cad/college_v1'
def main(destination):
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    m=json.loads((SOURCE/'print_manifest.json').read_text())
    checks=json.loads((SOURCE/'slicer_checks.json').read_text())
    byname={r['name']:r for r in checks['parts']}
    assert checks['all_manifold_and_sliced'] and len(byname)==m['unique_parts']
    fits=[];listing=['# File inventory','', 'Dimensions are millimetres, X × Y × Z in the exported orientation. Quantities below describe the development inventory including coupons; they are NOT an instruction to print the full build. Print one of each of the nine first-batch files initially.','']
    packaged=[]
    for row in m['parts']:
        name=row['name'];fit=row['release']=='fit_check_only'
        group='01_PRINT_FIRST_FIT_CHECKS' if fit else '02_HOLD_NOT_READY_FOR_BUILD/'+row['group']
        target=destination/group/(name+'.stl');target.parent.mkdir(parents=True,exist_ok=True)
        source=SOURCE/row['file'];shutil.copy2(source,target)
        digest=hashlib.sha256(target.read_bytes()).hexdigest()
        assert digest==byname[name]['stl_sha256'],(name,'slicer verification is stale')
        d=' × '.join(f'{x:.3f}'.rstrip('0').rstrip('.') for x in row['dimensions_mm'])
        if fit:fits.append(row)
        listing += [f'## {name}',f'- File: [{name}.stl]({group}/{name}.stl)',f'- Size: {d} mm; development quantity: {row["qty"]}; initial fit quantity: {1 if fit else 0}.',f'- Status: {"Print for unpowered fit checking" if fit else "HOLD — full assembly not qualified"}.',f'- Material/orientation: {row["material"]}. {row["orientation"]}',f'- Hardware: {row["hardware"] or "See assembly instructions"}.',f'- Notes: {row["note"]}','']
        packaged.append({**row,'file':str(target.relative_to(destination)).replace('\\','/'),'sha256':digest,'initial_print_qty':1 if fit else 0,'slicer_mass_g_each':byname[name]['estimated_mass_g']})
    fitmass=sum(byname[r['name']]['estimated_mass_g'] for r in fits)
    readme=f'''# Variable Reach Arm — compact V1 print package

**Print the nine files in `01_PRINT_FIRST_FIT_CHECKS`, one copy each. The complete robot is NOT ready for bulk printing.**

These are real millimetre STL meshes. All {m['unique_parts']} files passed FreeCAD valid-single-solid and closed-mesh checks and PrusaSlicer 2.9.6 manifold/toolpath checks. The complete development inventory is {m['piece_count']} pieces including five test coupons. This validation establishes sliceable geometry, not fit, strength or completed assembly.

## What is in the folders

- `01_PRINT_FIRST_FIT_CHECKS`: nine files for bearing, telescope, joint and servo fitting. One of each is approximately **{fitmass:.1f} g of PETG** with the verification settings, before your printer's purge and any extra brim.
- `02_HOLD_NOT_READY_FOR_BUILD`: the other 35 design files. Included for review and completeness of the CURRENT export, not for bulk printing. Several required robot parts are still missing; this is not a complete build kit.
- `FILE_INVENTORY.md`: every file, size, intended quantity, material and hardware notes.
- `Telescope_Assembly.md` and `Claw_Assembly.md`: dimensional and assembly instructions with unresolved interfaces stated.
- `verification`: machine-readable geometry/slicing and sampled-clearance results.

## Import into PrusaSlicer

1. Select the actual printer model at work and its actual nozzle. Use its PETG filament profile; the verification temperatures are not a universal filament recommendation.
2. Import individual STL files from the first folder. Keep scale **100%**, units **mm**, and the supplied orientation. Auto-arrange may move/rotate around Z, but do not lay the tube/joint coupons sideways.
3. Start with 0.20 mm layers, 6 perimeters, 5 top/bottom layers and 25% gyroid. The small pads will naturally be solid. Supports off for the first batch. Use a small brim on upright joint coupons if needed and check the footprint remains on the bed.
4. Slice and inspect every layer for missing walls, unsupported islands, first-layer contact and collisions with the print boundary. Print objects by layer, not sequential complete-object mode unless you check extruder clearances yourself.
5. Export G-code only after selecting the actual machine and filament. No machine-specific G-code is supplied here.

The full set was checked against a 250 × 220 × 270 mm CORE One envelope. Your message "a prusa one" has not definitively identified the model. First-batch parts fit inside 167 × 42 × 50 mm individually. The bearing gauge is 167 mm long: on a MINI, verify skirt/brim clearance or rotate/disable the skirt as appropriate. Full-set pieces up to 240 mm are unsuitable for a MINI without redesign. On other Prusas, check plate orientation and footprint; do not shrink structural parts to fit.

## What to check with the first batch

- **608 bearing gauge:** six pockets from the notched end, diameters 21.9 / 22.0 / 22.1 / 22.2 / 22.3 / 22.4 mm. Test an actual 608 bearing (8 × 22 × 7 mm). Choose a pocket that seats with moderate hand pressure without cracking and without perceptible rocking. The production pockets currently use 22.3 mm; record which size works before printing shoulder/base parts. Do not hammer bearings into coupons.
- **Outer/inner tube coupons:** outer 42 mm square with 34.8 mm bore; inner 30 mm square with 23.6 mm bore. Check squareness and smooth surfaces. Free clearance between bare tubes is intentional; guides take up the gap.
- **Rear guide ring:** 34.14 mm outside, 30.3 mm inside. Fit on the inner coupon; measured 0.13 mm PTFE tape on each outside face gives 34.40 mm, nominally 0.40 mm total clearance in the outer bore. Keep seams flush. Do not glue it until the sliding fit is established.
- **Front pad:** 16 × 18 × 1.6 mm; print ONE initially. Check thickness and smooth PTFE contact face. The complete development telescope requires four after fit validation.
- **Male/female joint coupons:** test both actual nut insertion paths, two M3 nuts and M3 × 12 DIN965/ISO7046 countersunk screws. Verify the spigot fits and both screw heads remain flush with the 30 mm tube surface. The 0.2 mm per-face adhesive gap is intentional. Dry-fit first; then test an expendable bonded pair before relying on the joint.
- **Servo carrier/horn adapter:** designed around an MG90S candidate, not a universal servo mount. Check actual body, flange, output-axis position, shaft height and horn screw pattern. Do not force your unknown existing servo into it. Adapter uses a bought horn and two M2 fasteners, not a printed spline. Record the measurements before printing the claw palm and fingers.

## Why the rest remains on hold

These are unresolved design tasks, not merely prototype unknowns:

- Complete telescope motor/idler mounts, belt attachment, drive alignment, limit-switch mounts and robust travel stops.
- Complete wrist-to-telescope attachment and servo support/height stack using measured hardware.
- Finish complete frame/shaft/bearing axial retention, pitch gravity restraint, wire routing and fastener/tool access.
- Assemble and check the entire compact robot through the complete intended motion range, with purchased hardware envelopes.
- Reconcile final fastener lengths, shaft cuts, drive changes and filament quantity into the purchasing BOM.

Do not print the hold folder expecting it to assemble into a complete functioning arm. The earlier full-size fair-version CAD remains preserved; this package is a separate compact, slow, mostly printed prototype.

## Filament and budget correction

The CURRENT development inventory slices to approximately **{checks['estimated_set_mass_g']/1000:.2f} kg**, including quantities and test coupons. The previous two-spool BOM allowance is insufficient. Three 1 kg spools are the current minimum material allowance, with little allowance for missing parts or failed prints. At the existing unquoted $20/spool assumption this is at least $60 of filament instead of $40. Do not interpret that as a newly finalized total robot price: the purchasing list also needs the drive and fastener reconciliation above. Print this approximately {fitmass:.0f} g fit batch first, not 2.7 kg of development geometry.

## Checks performed, and their limits

- 44 valid connected CAD solids and 44 closed manifold STL files, all successfully sliced with a generic 0.4 mm nozzle/0.2 mm PETG verification configuration.
- Claw printed parts including nominal carrier: 51 sampled crank positions, -25 to +25 degrees, with no material overlap and numerical linkage closure. Purchased servo, horn, screws/nuts and continuous swept clearance remain unverified.
- Gear pairs: 14 sampled poses of the 20/80 and 20/160 tooth pairs, no material overlap. Actual printed backlash, wear, holding torque and loaded capacity remain unverified.
- These fit prints are for unpowered dimensional checking. They do not release autonomous catching or throwing.
'''
    (destination/'README_PRINT_FIRST.md').write_text(readme,encoding='utf-8')
    (destination/'FILE_INVENTORY.md').write_text('\n'.join(listing),encoding='utf-8')
    (destination/'02_HOLD_NOT_READY_FOR_BUILD'/'DO_NOT_BULK_PRINT.md').write_text('Full build remains incomplete. See ../README_PRINT_FIRST.md for the exact missing design interfaces. These valid meshes are development exports, not a manufacturing release.\n')
    for old,new in [('v1_claw_assembly.md','Claw_Assembly.md'),('v1_telescope_assembly.md','Telescope_Assembly.md')]:shutil.copy2(ROOT/'docs'/old,destination/new)
    v=destination/'verification';v.mkdir(exist_ok=True)
    for f in ['slicer_checks.json','claw_clearance_checks.json','gear_mesh_checks.json','bearing_coupon_checks.json']:shutil.copy2(SOURCE/f,v/f)
    (destination/'print_manifest.json').write_text(json.dumps({**m,'parts':packaged,'first_batch_unique_files':len(fits),'first_batch_mass_g':fitmass},indent=2)+'\n')
    assert len(list(destination.rglob('*.stl')))==44
    print(destination)
    print('Packaged 44 STL files; 9 first-batch fit files; all SHA256 recorded.')
if __name__=='__main__':main(sys.argv[1])

