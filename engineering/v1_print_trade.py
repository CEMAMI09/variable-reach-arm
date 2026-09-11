"""Ideal straight tube comparison only; printed joints/creep/telescope guides excluded."""
import json
from pathlib import Path

def section(b,t):
    if not 0 < 2*t < b: raise ValueError('invalid wall')
    return (b**4-(b-2*t)**4)/12, b*b-(b-2*t)**2

def run():
    rows=[]
    for b in (.0254,.0381):
        ia,aa=section(b,.0015875)
        ip,ap=section(b,.003)
        ratio=69e9*ia/(2.31111e9*ip)
        rows.append(dict(side_m=b,al_wall_m=.0015875,petg_wall_m=.003,
            al_mass_per_m_kg=aa*2700,petg_mass_per_m_kg=ap*1300,
            petg_to_al_tip_deflection_same_span=ratio,
            petg_to_al_deflection_half_span=ratio/8))
    return dict(source='https://polymaker.com/wp-content/uploads/lana-downloads/TDS_Polymaker_PETG_V2.0_2025-11-17.pdf',
        modulus_basis='PETG XY nominal2.31111GPa supplier coupon, favorable estimate not design allowable; Al69GPa assumed',
        rows=rows,limitations='Single ideal uniform cantilever with same tip force. Excludes joints, anisotropy, creep, guide lash and segmented printing. Not a complete telescope deflection calculation.',
        concept=dict(normal_reach_m=.35,maximum_reach_m=.55,stroke_m=.20,
            nominal_shoulder_height_m=.35,payload_kg=.02,
            proposed_initial_angular_speed_rad_s=.15,proposed_initial_extension_speed_m_s=.05,
            status='Design targets only; no powered operating envelope approved. Separate compact CAD and sizing required.'))

if __name__=='__main__':
    result=run()
    Path(__file__).with_name('v1_print_trade_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
