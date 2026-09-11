"""Reproducible Rev B engineering screens; standard library, SI throughout.

This predicts requirements. It does not certify an actuator, printed part or machine.
Geometry comes from design_parameters.json. See calculations.md for derivations,
model limits, sources, acceptance gates and the difference between target and bench.
"""
from __future__ import annotations
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
G = 9.80665


def parameters():
    return json.loads((ROOT / 'design_parameters.json').read_text(encoding='utf-8'))


def square_section(side, wall):
    if not all(math.isfinite(x) for x in (side, wall)) or not 0 < 2*wall < side:
        raise ValueError('invalid square tube section')
    bore = side - 2*wall
    # Bredt closed thin-wall torsion constant, NOT polar bending moment.
    return side**2-bore**2, (side**4-bore**4)/12, (side-wall)**3*wall


def bodies(extension, p=None, loaded=True):
    p = p or parameters()
    g, m, mat = p['geometry'], p['mass_allowances'], p['material']
    if not math.isfinite(extension) or not 0 <= extension <= g['extension_stroke_m']:
        raise ValueError('extension outside design stroke')
    a, b = g['outer_start_m'], g['outer_end_m']
    outer_mass = square_section(g['outer_side_m'],g['outer_wall_m'])[0]*(b-a)*mat['density_kg_m3']
    il = g['inner_length_m']
    inner_mass = square_section(g['inner_side_m'],g['inner_wall_m'])[0]*il*mat['density_kg_m3']
    # name, kg, axial COM m, distributed rod length m, translates with extension.
    return [
        ('outer',outer_mass,(a+b)/2,b-a,False),
        ('inner',inner_mass,g['inner_retracted_start_m']+extension+il/2,il,True),
        ('catcher',m['catcher_and_tip_wiring_kg'],g['normal_reach_m']+extension-g['catcher_com_behind_mouth_m'],0,True),
        ('ball',m['ball_kg'] if loaded else 0,g['normal_reach_m']+extension-g['catcher_com_behind_mouth_m'],0,True),
        ('rear_guide',m['rear_carriage_kg'],g['rear_guide_retracted_center_m']+extension,0,True),
        ('front_guide',m['fixed_front_guide_kg'],g['front_guide_center_m'],0,False),
        ('minimum_stop',m['minimum_stop_kg'],-.2335,0,False),
        ('maximum_stop',m['maximum_stop_kg'],.287,0,False),
        ('front_idler',m['front_idler_kg'],.525,0,False),
        ('extension_drive',m['extension_motor_and_bracket_kg'],m['extension_motor_com_x_m'],0,False),
        ('trunnions',m['pitch_clamps_and_trunnions_kg'],0,math.sqrt(12)*m['pitch_clamps_radius_m'],False),
    ]


def inertial_terms(extension, p=None, loaded=True):
    bs = bodies(extension,p,loaded)
    return {'I':sum(m*(r*r+length*length/12) for _,m,r,length,_ in bs),
            'I_prime':sum(2*m*r for _,m,r,_,moving in bs if moving),
            'first_moment':sum(m*r for _,m,r,_,_ in bs),
            'slider_mass':sum(m for _,m,_,_,moving in bs if moving),
            'total_mass':sum(m for _,m,_,_,_ in bs)}


def dynamics(extension, pitch, rates, accelerations, p=None, loaded=True):
    """Rigid-line boom spherical-coordinate inverse dynamics, no friction.

    rates and accelerations = (yaw, pitch, extension), pitch zero horizontal.
    Boom cross-section rotary inertias and motor gyroscopic terms are omitted:
    narrow beam screen only. Rotor J is estimated; procurement requires exact J.
    """
    p = p or parameters()
    t = inertial_terms(extension,p,loaded)
    d, m, g = p['drivetrain'],p['mass_allowances'],p['geometry']
    wy,wp,vs = rates
    ay,ap,ac = accelerations
    if not all(math.isfinite(v) for v in (pitch,*rates,*accelerations)):
        raise ValueError('nonfinite state')
    cp,sp = math.cos(pitch),math.sin(pitch)
    I,Ip = t['I'],t['I_prime']
    jp = d['motor_rotor_inertia_kg_m2_assumed']*d['pitch_ratio']**2
    jy = d['motor_rotor_inertia_kg_m2_assumed']*d['yaw_ratio']**2
    turret = m['yaw_carried_motor_bracket_kg']*m['yaw_carried_motor_bracket_radius_m']**2
    radius = g['extension_belt_pitch_m']*g['extension_pulley_teeth']/(2*math.pi)
    extension_reflected_mass = 5e-6/radius**2  # assumed NEMA17 J; not published data
    return dict(pitch_nm=(I+jp)*ap+Ip*vs*wp+I*wy*wy*sp*cp+G*t['first_moment']*cp,
                yaw_nm=(I*cp*cp+turret+jy)*ay+(Ip*vs*cp*cp-2*I*sp*cp*wp)*wy,
                extension_n=(t['slider_mass']+extension_reflected_mass)*ac-Ip/2*(wp*wp+wy*wy*cp*cp)+t['slider_mass']*G*sp,
                pitch_inertia_kgm2=I+jp,yaw_inertia_kgm2=I*cp*cp+turret+jy)


def guide_load(extension, transverse_tip_n=0.0, p=None, pitch=0.0,
               rates=(0.0,0.0,0.0), accelerations=(0.0,0.0,0.0),
               tip_force_yaw_n=0.0):
    """Exact distributed inertial guide reactions in both transverse planes.

    Each body has acceleration a(r)=k*r+c; integrate its force and moment,
    including local rod moment m*l²/12. Sign = guide force needed on slider.
    Tip forces add to that demand. Contact is assumed on opposing pad faces.
    Coulomb sliding model requires measured friction/preload and excludes binding.
    """
    p = p or parameters()
    g,d = p['geometry'],p['drivetrain']
    front,rear = g['front_guide_center_m'],g['rear_guide_retracted_center_m']+extension
    span = front-rear
    if span <= 0:
        raise ValueError('guide spacing must be positive')
    wy,wp,vs = rates
    ay,ap,_ = accelerations
    cp,sp = math.cos(pitch),math.sin(pitch)
    # Yaw centripetal acceleration projects POSITIVELY onto e_pitch.
    # e_pitch=(-sin(p)cos(y),-sin(p)sin(y),cos(p)); using a negative sign
    # understates pad loads while yawing with the boom raised.
    kp, cp_acc = ap+wy*wy*sp*cp,2*vs*wp+G*cp
    ky, cy_acc = cp*ay-2*sp*wp*wy,2*vs*cp*wy
    result=[]
    for k,c,tip in [(kp,cp_acc,transverse_tip_n),(ky,cy_acc,tip_force_yaw_n)]:
        force,moment = tip,tip*(g['normal_reach_m']+extension-rear)
        for _,mass,x,length,moving in bodies(extension,p):
            if moving:
                force += mass*(k*x+c)
                moment += mass*(k*(x*x+length*length/12-rear*x)+c*(x-rear))
        rf=moment/span
        result.append((rf,force-rf))
    front_vector=(result[0][0],result[1][0])
    rear_vector=(result[0][1],result[1][1])
    front_norm,rear_norm=math.hypot(*front_vector),math.hypot(*rear_vector)
    # Square shoes react on separate orthogonal faces: Coulomb normals add
    # component-wise. Using the vector resultant would understate by up to sqrt2.
    normal=sum(abs(component) for component in (*front_vector,*rear_vector))+d['guide_preload_total_n_assumed']
    return dict(span_m=span,front_n=front_norm,rear_n=rear_norm,
                front_pitch_yaw_n=front_vector,rear_pitch_yaw_n=rear_vector,
                friction_n=d['guide_friction_coefficient_assumed']*normal+d['extension_drag_n_assumed'],
                nominal_pad_pressure_pa=max(abs(component) for component in (*front_vector,*rear_vector))/(g['guide_length_m']*g['guide_pad_width_m']))


def guide_bound(extension, envelope, transverse_tip_n=0.0, p=None):
    """Triangle-inequality bound for independently bounded motion, any pitch.

    We integrate |r| and |r-rear| exactly on sign-separated polynomial intervals,
    so rear overhangs cannot cancel bounding loads.
    """
    p = p or parameters()
    g,d=p['geometry'],p['drivetrain']
    front,rear=g['front_guide_center_m'],g['rear_guide_retracted_center_m']+extension
    span=front-rear
    w,v=envelope['angular_speed_rad_s'],envelope['extension_speed_m_s']
    kp=envelope['pitch_accel_rad_s2']+w*w/2
    ky=envelope['yaw_accel_rad_s2']+2*w*w
    cp,cy=2*v*w+G,2*v*w
    total_p=total_y=moment_p=moment_y=0.0
    for _,mass,x,length,moving in bodies(extension,p):
        if not moving:
            continue
        if length:
            lo,hi=x-length/2,x+length/2
            points=sorted({lo,hi,*[v for v in (0.0,rear) if lo<v<hi]})
            ar=abr=product=0.0
            for left,right in zip(points,points[1:]):
                mid=(left+right)/2
                sr=1 if mid>=0 else -1
                sb=1 if mid>=rear else -1
                ar += sr*(right*right-left*left)/2
                abr += sb*((right-rear)**2-(left-rear)**2)/2
                product += sr*sb*((right**3-left**3)/3-rear*(right*right-left*left)/2)
            ar,abr,product=ar/length,abr/length,product/length
        else:
            ar,abr,product=abs(x),abs(x-rear),abs(x)*abs(x-rear)
        total_p += mass*(kp*ar+cp)
        total_y += mass*(ky*ar+cy)
        moment_p += mass*(kp*product+cp*abr)
        moment_y += mass*(ky*product+cy*abr)
    # Sum orthogonal flat-face reaction magnitudes; diagonal external load can
    # produce sqrt2 times its resultant in face-normal sum.
    rf=(moment_p+moment_y+math.sqrt(2)*transverse_tip_n*abs(g['normal_reach_m']+extension-rear))/span
    rr=total_p+total_y+math.sqrt(2)*transverse_tip_n+rf
    normal=rf+rr+d['guide_preload_total_n_assumed']
    return dict(span_m=span,front_n=rf,rear_n=rr,
                friction_n=d['guide_friction_coefficient_assumed']*normal+d['extension_drag_n_assumed'],
                nominal_pad_pressure_pa=max(rf,rr)/(g['guide_length_m']*g['guide_pad_width_m']))


def beam_screen(extension, tip_force_n, torque_nm=1.0, p=None):
    """Conservative piecewise beam-only compliance screen, NOT an upper bound
    on assembled deflection. Outer to moving rear guide, inner thereafter.
    Unbonded overlapping tubes are not treated as a composite section.
    Compliance of the last115mm claw mount is unknown; its replacement by tube
    EI in this screen cannot establish actual catcher rigidity.
    """
    p=p or parameters()
    g,mat=p['geometry'],p['material']
    L=g['normal_reach_m']+extension
    joint=max(0,g['rear_guide_retracted_center_m']+extension)
    _,io,jo=square_section(g['outer_side_m'],g['outer_wall_m'])
    _,ii,ji=square_section(g['inner_side_m'],g['inner_wall_m'])
    compliance=((L**3-(L-joint)**3)/io+(L-joint)**3/ii)/(3*mat['youngs_modulus_pa'])
    stress=max(tip_force_n*L*g['outer_side_m']/2/io,tip_force_n*(L-joint)*g['inner_side_m']/2/ii)
    clearance=g['guide_total_lateral_clearance_m']
    span=g['front_guide_center_m']-(g['rear_guide_retracted_center_m']+extension)
    return dict(tip_deflection_m=tip_force_n*compliance,compliance_m_n=compliance,
                max_bending_stress_pa=stress,yield_factor=mat['yield_strength_pa']/stress if stress else None,
                twist_rad=torque_nm*(joint/jo+(L-joint)/ji)/mat['shear_modulus_pa'],
                tip_lost_motion_from_guide_clearance_m=clearance*(1+(L-g['front_guide_center_m'])/span),
                limitation='tube-only elastic screen; excludes root/bearings/pad contacts/claw compliance, belt elasticity, local crushing and stress concentrations')


def catch_energy(ball_mass, relative_speed, stroke, peak_factor=2.0):
    if min(ball_mass,stroke) <= 0 or relative_speed < 0 or peak_factor < 1:
        raise ValueError('invalid impact inputs')
    energy=0.5*ball_mass*relative_speed**2
    return dict(relative_speed_m_s=relative_speed,assumed_stroke_m=stroke,energy_j=energy,
                average_force_n=energy/stroke,assumed_peak_force_n=peak_factor*energy/stroke,
                nominal_constant_decel_time_s=2*stroke/relative_speed if relative_speed else 0,
                peak_status='assumed shape factor; physical measurement mandatory')


def radial_catch_match(ball_radial_m_s, hand_radial_m_s, commanded_retraction_m_s):
    """Positive radial = outward. Retraction is a negative hand velocity.
    This compares instantaneous relative radial speeds only, not a full controller.
    """
    if commanded_retraction_m_s > 0:
        raise ValueError('retraction velocity must be nonpositive')
    before=ball_radial_m_s-hand_radial_m_s
    after=ball_radial_m_s-commanded_retraction_m_s
    return dict(relative_radial_before_m_s=before,relative_radial_after_m_s=after,
                reduces_radial_impact=abs(after)<abs(before))


def shaft_belt_screen(output_torque_nm, external_radial_n, pitch_ratio=8.0):
    """Preliminary two-stage HTD5 20:40 then20:80, shaft reactions.
    Final trunnion layout changes require recalculation. 12mm steel shaft;
    final80T pulley radius63.66mm, unsupported length20mm. T0=100N/strand.
    If slack tension goes negative this preload is insufficient.
    """
    pitch=0.005
    radius=80*pitch/(2*math.pi)
    difference=abs(output_torque_nm)/radius
    preload=100.0
    tight,slack=preload+difference/2,preload-difference/2
    belt_radial=2*preload if slack>=0 else difference
    diameter=0.012
    bending=(belt_radial+external_radial_n/2)*0.020
    bending_stress=32*bending/(math.pi*diameter**3)
    shear=16*abs(output_torque_nm)/(math.pi*diameter**3)
    von_mises=math.sqrt(bending_stress**2+3*shear**2)
    return dict(output_pulley_pitch_diameter_m=2*radius,belt_tension_difference_n=difference,
                assumed_preload_each_strand_n=preload,tight_tension_n=tight,slack_tension_n=slack,
                preload_sufficient=slack>0,motor_pulley_direct_load_n=2*preload,
                driven_bearing_radial_n=belt_radial+external_radial_n/2,
                shaft_bending_moment_nm=bending,shaft_von_mises_pa=von_mises,
                shaft_yield_factor_assuming_250mpa=250e6/von_mises if von_mises else None,
                shaft_local_stress_factor_allowance=2.0,
                shaft_yield_factor_with_local_allowance=250e6/(2*von_mises) if von_mises else None,
                release='requires purchased belt rating, true bearing layout, steel grade, hub grip and fatigue review')


def motor_demand_curve(output_torque_nm, output_speed, ratio, efficiency, margin=1.5):
    if min(ratio,efficiency,margin) <= 0:
        raise ValueError('invalid drive factors')
    return dict(ratio=ratio,motor_rpm=abs(output_speed)*ratio*60/(2*math.pi),
                load_torque_nm=abs(output_torque_nm)/(ratio*efficiency),
                minimum_available_running_torque_nm=margin*abs(output_torque_nm)/(ratio*efficiency),
                margin_required=margin,available_running_torque_nm=None,qualified=False,
                reason='exact voltage/current/driver torque-speed curve not yet verified; holding torque is not capacity')


def claw_closure_screen():
    """Illustrative unmeasured finger mechanism. No spring/servo selected by this.
    All numbers are test parameters; low-friction fixed torque approximation.
    """
    finger_mass,length,pad_mass=0.018,0.11,0.004
    inertia=finger_mass*length**2/3+pad_mass*length**2
    travel,spring_torque,friction=0.45,0.015,0.005
    ideal_time=math.sqrt(2*inertia*travel/(spring_torque-friction))
    servo_radius,finger_horn=0.010,0.012
    # Three tendons, each opening against spring plus friction.
    servo_required=3*(spring_torque+friction)*servo_radius/finger_horn
    return dict(status='illustrative assumptions; measure every parameter',finger_inertia_kg_m2=inertia,
                finger_close_travel_rad=travel,spring_torque_each_nm=spring_torque,
                assumed_friction_torque_each_nm=friction,ideal_contactless_closure_time_s=ideal_time,
                ball_transit_60mm_at4m_s_s=0.060/4,
                servo_open_torque_nm_with_2x_margin=2*servo_required,
                warning='contact-triggered spring closure is much slower than ball transit in this example; compliant capture geometry and predictive preposition required')


def extension_hardstop_screen(effective_mass, speed, pulley_radius, stroke=0.003):
    """Current 5mm smooth steel pins; conservatively one pin takes first contact.
    Three millimetres is the modeled TPU axial pad thickness, not proven usable
    energy-absorbing stroke. A 2x mean pulse is illustrative, not a peak guarantee.
    """
    energy=0.5*effective_mass*speed**2
    force=2*energy/stroke+0.6/pulley_radius
    diameter=0.005
    overhang=0.004
    bending=32*force*overhang/(math.pi*diameter**3)
    shear=force/(math.pi*diameter**2/4)
    vm=math.sqrt(bending*bending+3*shear*shear)
    return dict(kinetic_energy_j=energy,assumed_usable_pad_stroke_m=stroke,
                average_force_n=energy/stroke,illustrative_design_force_n=force,
                single_pin_von_mises_pa=vm,pin_yield_factor_assumed250mpa=250e6/vm,
                maximum_unsupported_pin_length_m=overhang,
                status='Not released: actual steel grade, usable pad stroke, impact pulse, collar slip, printed lug strength and tube bearing require qualification; no normal hard-stop deceleration')


def envelope_row(extension,envelope,p):
    t=inertial_terms(extension,p)
    d,g=p['drivetrain'],p['geometry']
    w,v=envelope['angular_speed_rad_s'],envelope['extension_speed_m_s']
    ap,ay,ae=envelope['pitch_accel_rad_s2'],envelope['yaw_accel_rad_s2'],envelope['extension_accel_m_s2']
    jp=d['motor_rotor_inertia_kg_m2_assumed']*d['pitch_ratio']**2
    jy=d['motor_rotor_inertia_kg_m2_assumed']*d['yaw_ratio']**2
    turret=p['mass_allowances']['yaw_carried_motor_bracket_kg']*p['mass_allowances']['yaw_carried_motor_bracket_radius_m']**2
    pitch=(t['I']+jp)*ap+abs(t['I_prime'])*v*w+t['I']*w*w/2+G*abs(t['first_moment'])+d['pitch_friction_nm_assumed']
    yaw=(t['I']+turret+jy)*ay+abs(t['I_prime'])*v*w+t['I']*w*w+d['yaw_friction_nm_assumed']
    guide=guide_bound(extension,envelope,p=p)
    radius=g['extension_belt_pitch_m']*g['extension_pulley_teeth']/(2*math.pi)
    axial=(t['slider_mass']+5e-6/radius**2)*ae+abs(t['I_prime'])*w*w+t['slider_mass']*G
    extension_force=axial+guide['friction_n']
    return dict(peak_pitch_bound_nm=pitch,peak_yaw_bound_nm=yaw,
                I_dot_pitch_coupling_bound_nm=abs(t['I_prime'])*v*w,
                extension_force_bound_n=extension_force,guide_motion_bound=guide,
                pitch_motor=motor_demand_curve(pitch,w,d['pitch_ratio'],d['belt_efficiency']),
                yaw_motor=motor_demand_curve(yaw,w,d['yaw_ratio'],d['belt_efficiency']),
                extension_motor=motor_demand_curve(extension_force*radius,v/radius,1,d['belt_efficiency']))


def bom_totals(path=None):
    path=path or ROOT/'bom.csv'
    with path.open(newline='',encoding='utf-8-sig') as handle:
        rows=list(csv.DictReader(handle))
    errors=[]
    groups={}
    for row in rows:
        subtotal=int(row['qty'])*float(row['unit_price_usd'])
        if not math.isclose(subtotal,float(row['ext_price_usd']),abs_tol=0.005):
            errors.append(row['item'])
        groups[row['stage']]=groups.get(row['stage'],0)+subtotal
    subtotal=sum(groups.values())
    # This is an allowance, not a jurisdiction tax calculation or shipping quote.
    shipping_tax_allowance=round(0.12*subtotal,2)
    reserve=round(0.15*(subtotal+shipping_tax_allowance),2)
    return dict(purchase_subtotal_usd=round(subtotal,2),groups_usd={k:round(v,2) for k,v in groups.items()},
                shipping_tax_allowance_usd=round(shipping_tax_allowance,2),reserve_usd=round(reserve,2),
                cash_budget_usd=round(subtotal+shipping_tax_allowance+reserve,2),line_math_errors=errors,
                within_500_usd=subtotal+shipping_tax_allowance+reserve<=500)


def run_all():
    p=parameters()
    g,d,target=p['geometry'],p['drivetrain'],p['performance_targets']
    rows=[]
    for s in (0,g['extension_stroke_m']/2,g['extension_stroke_m']):
        t=inertial_terms(s,p)
        routine=envelope_row(s,target,p)
        bench=envelope_row(s,p['bench_envelope'],p)
        impact=catch_energy(p['mass_allowances']['ball_kg'],target['ball_incoming_speed_m_s'],target['passive_catcher_stroke_m'])
        force=impact['assumed_peak_force_n']
        structure=beam_screen(s,t['total_mass']*G+force,p=p)
        clear=beam_screen(s,0,p=p)
        L=g['normal_reach_m']+s
        rows.append(dict(extension_m=s,reach_m=L,**t,gravity_pitch_nm=G*t['first_moment'],
                         tube_masses_kg={name:mass for name,mass,*_ in bodies(s,p) if name in ('outer','inner')},
                         target_motion=routine,commissioning_motion=bench,
                         claw_unmatched_impact=impact,transverse_impact_additional_pitch_nm=L*force,
                         guide_motion_plus_transverse_impact_bound=guide_bound(s,target,force,p),
                         structure_screen=structure,guide_lost_motion_m=clear['tip_lost_motion_from_guide_clearance_m'],
                         shaft_belt_motion_screen=shaft_belt_screen(routine['peak_pitch_bound_nm'],t['total_mass']*G),
                         shaft_belt_unmatched_impact_screen=shaft_belt_screen(routine['peak_pitch_bound_nm']+L*force,t['total_mass']*G+force),
                         beam_only_first_mode_screen_hz=1/(2*math.pi)*math.sqrt(1/(structure['compliance_m_n']*t['total_mass']))))
    last=rows[-1]
    w,v=target['angular_speed_rad_s'],target['extension_speed_m_s']
    e=last['target_motion']
    mech=e['peak_pitch_bound_nm']*w+e['peak_yaw_bound_nm']*w+e['extension_force_bound_n']*v
    # Explicit loss allowance; motor copper follows selected vendor's rated5A/phase .4ohm:
    # two phases fully energised would bound20W/motor; chopper waveform matters.
    copper_two_major=2*(2*5**2*0.4)
    ext_and_drivers=35.0
    logic=15.0
    bus_w=mech/0.65+copper_two_major+ext_and_drivers+logic
    kinetic=last['I']*w*w+0.5*last['slider_mass']*v*v
    rotor=0.5*d['motor_rotor_inertia_kg_m2_assumed']*((w*d['pitch_ratio'])**2+(w*d['yaw_ratio'])**2)
    radius=g['extension_belt_pitch_m']*g['extension_pulley_teeth']/(2*math.pi)
    rotor += 0.5*5e-6*(v/radius)**2
    turret=0.5*p['mass_allowances']['yaw_carried_motor_bracket_kg']*p['mass_allowances']['yaw_carried_motor_bracket_radius_m']**2*w*w
    # Bound full pitch descent + radial retraction: absolute moving/fixed mass heights.
    gravity_drop=G*abs(last['first_moment'])*(math.sin(g['pitch_max_rad'])-math.sin(g['pitch_min_rad']))
    regen=kinetic+rotor+turret+gravity_drop
    cap=0.0047
    ext_stop_energy=0.5*(last['slider_mass']+5e-6/radius**2)*v*v
    return dict(status='UNQUALIFIED: not released for powered catching or procurement freeze',
                configurations=rows,
                dynamic_bound_note='Triangle bounds allow simultaneous independent axis extrema. Some combinations cannot occur at physical endpoints. No measured duty cycle or performance claim.',
                power_screen=dict(mechanical_bound_w=mech,loss_assumption_bus_w=bus_w,bus_current_24v_a=bus_w/24,
                                  conversion_efficiency_assumed=0.65,major_motor_copper_bound_w=copper_two_major,
                                  additional_extension_driver_loss_assumed_w=ext_and_drivers,logic_w=logic,
                                  combined_kinetic_energy_j=kinetic+rotor+turret,
                                  regeneration_energy_bound_j=regen,bus_24v_plus_regen_into_4700uf_v=math.sqrt(24**2+2*regen/cap),
                                  required_cap_f_for_24_to_28v=2*regen/(28**2-24**2),
                                  dump_example_ohms=10,dump_example_peak_w_at_28v=28**2/10,
                                  dump_status='example only; regulator, energy/pulse resistor rating and contactor topology are a release gate'),
                extension_stop_screen=extension_hardstop_screen(last['slider_mass']+5e-6/radius**2,v,radius),
                claw_closure_screen=claw_closure_screen(),
                catch_comparison=[catch_energy(.05,speed,.025) for speed in (1,2,4)],
                inward_ball_retract=radial_catch_match(-4,0,-1.2),outward_ball_retract=radial_catch_match(4,0,-1.2),
                budget=bom_totals(),restrained_rig_budget=bom_totals(ROOT/'bom_restrained_rig.csv'),original_bom_actual_subtotal_usd=701.0,
                release_gates=['Exact loaded torque-speed/temperature curves at bus voltage, driver current and reduction; minimum1.5 margin',
                  'Profile RMS torque/current and continuous horizontal hold temperature; characterize spring before any balance credit',
                  'Complete pitch/yaw reductions, shaft/hub retention, brake, bearing loads, belts and drive ratings',
                  'Measured claw/foam stopping stroke, peak force and approach cone; no unmatched4m/s transverse catches',
                  'DC E-stop/brake/dump power circuitry and measured power-loss behaviour',
                  'Physical tube corner radii/straightness, pad creep/friction and full-travel belt-clamp clearance',
                  'Catcher mass, mount stiffness, distal wiring, controller saturation and captured-ball retention'])


def main():
    result=run_all()
    for name in ('review_results.json','sizing_results.json'):
        (ROOT/name).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    for row in result['configurations']:
        print(f"L={row['reach_m']:.2f}m I={row['I']:.4f}kgm2 gravity={row['gravity_pitch_nm']:.2f}Nm "
              f"pitch_bound={row['target_motion']['peak_pitch_bound_nm']:.2f}Nm "
              f"extension_bound={row['target_motion']['extension_force_bound_n']:.1f}N")
    print(json.dumps(result['power_screen'],indent=2))
    print(json.dumps(result['budget'],indent=2))
    print('Restrained rig cash budget:',result['restrained_rig_budget']['cash_budget_usd'])


if __name__ == '__main__':
    main()
