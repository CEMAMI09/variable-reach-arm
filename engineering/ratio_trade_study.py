"""Running-torque requirements versus reduction; no invented available curve."""
import copy
import json
from pathlib import Path
from engineering.review_sizing import parameters, envelope_row


def graph_lower_screen(rpm, curve):
    """Conservative local graph reading, not a guaranteed torque rating.

    Use the minimum adjacent readings across the requested speed uncertainty
    interval, less reading allowance. No extrapolation or voltage scaling.
    """
    points=curve['points_rpm_nm']
    lo=rpm-curve['rpm_reading_allowance'];hi=rpm+curve['rpm_reading_allowance']
    if lo<points[0][0] or hi>points[-1][0]:return None
    values=[]
    for (a,ta),(b,tb) in zip(points,points[1:]):
        if a<=hi and lo<=b:values.extend((ta,tb))
    return max(0,min(values)-curve['torque_reading_allowance_nm'])


def run():
    baseline=parameters()
    curve=json.loads(Path(__file__).with_name('motor_curve_23e1k20.json').read_text())
    results=[]
    for axis in ('pitch','yaw'):
        for ratio in (4,6,8,10,12,16,20):
            p=copy.deepcopy(baseline)
            p['drivetrain'][axis+'_ratio']=ratio
            row=envelope_row(p['geometry']['extension_stroke_m'],p['performance_targets'],p)
            demand=row[axis+'_motor']
            lower=graph_lower_screen(demand['motor_rpm'],curve)
            results.append(dict(axis=axis,ratio=ratio,motor_rpm=demand['motor_rpm'],
                required_running_torque_nm=demand['minimum_available_running_torque_nm'],
                reflected_rotor_inertia_kgm2=p['drivetrain']['motor_rotor_inertia_kg_m2_assumed']*ratio**2,
                pullout_graph_lower_screen_nm_at_48v=lower,
                passes_48v_graph_screen=lower is not None and lower>=demand['minimum_available_running_torque_nm'],
                qualified=False))
    return dict(status='48V pull-out graph screen only; no24V or continuous-duty qualification',
                curve_source=curve,
                omitted='Additional jackshaft/pulley spin inertia, exact belt loss, ratio-dependent packaging and cost',
                results=results)


if __name__=='__main__':
    result=run()
    Path(__file__).with_name('ratio_trade_results.json').write_text(json.dumps(result,indent=2)+'\n')
    for r in result['results']:
        print(f"{r['axis']:5} {r['ratio']:2}:1  {r['motor_rpm']:5.0f}rpm  requires {r['required_running_torque_nm']:.3f}Nm with margin")
