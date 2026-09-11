"""Export checked millimetre STL development set; only fit batch is releaseable.
Run with FreeCAD Python. Does not change active GUI documents or legacy CAD.
"""
import sys,json
from pathlib import Path
import FreeCAD as App
import MeshPart
sys.path.insert(0,str(Path(__file__).resolve().parent))
import v1_core_parts as core
import v1_telescope_parts as telescope
import v1_claw_parts as claw

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'cad'/'college_v1'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    doc=App.newDocument('V1_Print_Development')
    report=[];index=0
    sources=[('frame_drive',core.parts()),('telescope',telescope.parts()),('claw',claw.parts())]
    for group,parts in sources:
        for name,spec in parts.items():
            sh=spec['shape'].copy();sh.translate(App.Vector(0,0,-sh.BoundBox.ZMin))
            assert sh.isValid() and len(sh.Solids)==1,(name,'solid validation failed')
            bb=sh.BoundBox
            assert bb.XLength<=250 and bb.YLength<=220 and bb.ZLength<=270,(name,'does not fit assumedCOREOne')
            mesh=MeshPart.meshFromShape(Shape=sh,LinearDeflection=.06,AngularDeflection=.12,Relative=False)
            assert mesh.isSolid(),(name,'mesh not closed')
            path=OUT/'development_stl'/group/(name+'.stl');path.parent.mkdir(parents=True,exist_ok=True);mesh.write(str(path))
            fit=('Fit_Coupon' in name or 'FitCoupon' in name or name in ['Telescope_Front_Guide_Pad','Telescope_Rear_Guide_Ring','V1_Claw_Servo_Carrier','V1_Claw_Crank_Adapter'])
            row={k:v for k,v in spec.items() if k!='shape'}
            row.update(name=name,group=group,file=str(path.relative_to(OUT)),dimensions_mm=[bb.XLength,bb.YLength,bb.ZLength],volume_mm3=sh.Volume,mesh_facets=mesh.CountFacets,closed_mesh=True,valid_single_solid=True,release='fit_check_only' if fit else 'development_hold')
            report.append(row)
            obj=doc.addObject('PartDesign::Feature',name);obj.Shape=sh;obj.Label=name+' x'+str(spec['qty'])
            obj.Placement.Base=App.Vector((index%6)*270,(index//6)*240,0);index+=1
    doc.recompute();doc.saveAs(str(OUT/'V1_Print_Development.FCStd'))
    result=dict(status='Development set. Valid geometry is not completed assembly validation.',units='mm',assumed_bed_mm=[250,220,270],parts=report,unique_parts=len(report),piece_count=sum(r['qty'] for r in report),all_geometry_checks_passed=True,full_build_ready=False)
    (OUT/'print_manifest.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='parts'}))

if __name__=='__main__':main()
