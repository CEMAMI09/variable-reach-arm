import copy
import math
import random
import unittest

from engineering import review_sizing as e


class EngineeringReviewTests(unittest.TestCase):
    def test_distributed_inertia_against_independent_mass_quadrature(self):
        for extension in (0,0.25,0.5):
            numeric=0.0
            for _,mass,com,length,_ in e.bodies(extension):
                n=2000 if length else 1
                numeric += sum(mass/n*(com+length*((i+.5)/n-.5))**2 for i in range(n))
            self.assertAlmostEqual(numeric,e.inertial_terms(extension)['I'],places=7)

    def test_translating_fixed_length_member_derivative(self):
        h=1e-6
        at=e.inertial_terms(.25)
        derivative=(e.inertial_terms(.25+h)['I']-e.inertial_terms(.25-h)['I'])/(2*h)
        self.assertAlmostEqual(derivative,at['I_prime'],places=8)
        self.assertAlmostEqual((e.inertial_terms(.3)['I_prime']-e.inertial_terms(.2)['I_prime'])/.1,
                               2*at['slider_mass'],places=8)

    def test_inverse_dynamics_energy_balance(self):
        p=e.parameters()
        q=(.2,.3,.25)
        dq=(.4,-.3,.2)
        ddq=(-.8,.6,-.1)
        d=p['drivetrain']
        radius=p['geometry']['extension_belt_pitch_m']*p['geometry']['extension_pulley_teeth']/(2*math.pi)
        turret=p['mass_allowances']['yaw_carried_motor_bracket_kg']*p['mass_allowances']['yaw_carried_motor_bracket_radius_m']**2
        def energy(dt):
            pos=[q[i]+dq[i]*dt+.5*ddq[i]*dt*dt for i in range(3)]
            vel=[dq[i]+ddq[i]*dt for i in range(3)]
            t=e.inertial_terms(pos[2],p)
            kinetic=.5*t['I']*(vel[1]**2+math.cos(pos[1])**2*vel[0]**2)
            kinetic += .5*turret*vel[0]**2+.5*(t['slider_mass']+5e-6/radius**2)*vel[2]**2
            kinetic += .5*d['motor_rotor_inertia_kg_m2_assumed']*((d['pitch_ratio']*vel[1])**2+(d['yaw_ratio']*vel[0])**2)
            return kinetic+e.G*t['first_moment']*math.sin(pos[1])
        step=1e-6
        power_by_energy=(energy(step)-energy(-step))/(2*step)
        demands=e.dynamics(q[2],q[1],dq,ddq,p)
        power_by_forces=demands['yaw_nm']*dq[0]+demands['pitch_nm']*dq[1]+demands['extension_n']*dq[2]
        self.assertAlmostEqual(power_by_energy,power_by_forces,places=7)

    def test_guide_reactions_from_cartesian_acceleration_and_projection(self):
        p=e.parameters()
        s,pitch=.4,.3
        rates,accels=(1.1,-.9,.6),(.7,-1.2,2)
        rear=p['geometry']['rear_guide_retracted_center_m']+s
        span=p['geometry']['front_guide_center_m']-rear
        L=p['geometry']['normal_reach_m']+s
        tip=3.0
        yaw=.3
        basis_pitch=(-math.sin(pitch)*math.cos(yaw),-math.sin(pitch)*math.sin(yaw),math.cos(pitch))
        basis_yaw=(-math.sin(yaw),math.cos(yaw),0.0)
        forces=[0.0,0.0]
        moments=[0.0,0.0]
        h=1e-4
        for _,mass,x,length,moving in e.bodies(s,p):
            if not moving:
                continue
            n=4000 if length else 1
            for j in range(n):
                r=x+length*((j+.5)/n-.5)
                # Differentiate world Cartesian position; do not reuse the
                # spherical acceleration expression from the sizing code.
                def position(dt):
                    radius=r+rates[2]*dt+.5*accels[2]*dt*dt
                    y=yaw+rates[0]*dt+.5*accels[0]*dt*dt
                    a=pitch+rates[1]*dt+.5*accels[1]*dt*dt
                    return (radius*math.cos(a)*math.cos(y),radius*math.cos(a)*math.sin(y),radius*math.sin(a))
                before,at,after=position(-h),position(0),position(h)
                world_acc=[(after[k]-2*at[k]+before[k])/(h*h) for k in range(3)]
                world_acc[2] += e.G
                for axis,basis in enumerate((basis_pitch,basis_yaw)):
                    f=mass/n*sum(world_acc[k]*basis[k] for k in range(3))
                    forces[axis] += f
                    moments[axis] += f*(r-rear)
        forces[0] += tip
        moments[0] += tip*(L-rear)
        guide=e.guide_load(s,tip,p,pitch,rates,accels)
        for axis in (0,1):
            rf,rr=guide['front_pitch_yaw_n'][axis],guide['rear_pitch_yaw_n'][axis]
            self.assertAlmostEqual(rf+rr,forces[axis],places=6)
            self.assertAlmostEqual(rf*span,moments[axis],places=6)

    def test_raised_boom_yaw_increases_upward_guide_reaction(self):
        spinning=e.guide_load(.5,pitch=math.pi/4,rates=(2,0,0))
        stationary=e.guide_load(.5,pitch=math.pi/4)
        self.assertGreater(spinning['front_pitch_yaw_n'][0],stationary['front_pitch_yaw_n'][0])
        self.assertAlmostEqual(spinning['front_pitch_yaw_n'][0],14.640144,places=4)

    def test_analytic_guide_bound_contains_random_dynamic_samples(self):
        p=e.parameters()
        limit=p['performance_targets']
        rng=random.Random(137)
        w,v=limit['angular_speed_rad_s'],limit['extension_speed_m_s']
        for s in (0,.25,.5):
            bound=e.guide_bound(s,limit,5,p)
            for _ in range(100):
                angle=rng.uniform(-math.pi/2,math.pi/2)
                rates=(rng.uniform(-w,w),rng.uniform(-w,w),rng.uniform(-v,v))
                accels=(rng.uniform(-limit['yaw_accel_rad_s2'],limit['yaw_accel_rad_s2']),
                        rng.uniform(-limit['pitch_accel_rad_s2'],limit['pitch_accel_rad_s2']),0)
                sample=e.guide_load(s,5,p,angle,rates,accels)
                self.assertLessEqual(sample['friction_n'],bound['friction_n']+1e-9)

    def test_square_pad_friction_adds_orthogonal_face_normals(self):
        p=e.parameters()
        guide=e.guide_load(.5,3,p,pitch=.2,rates=(1,1,.7),accelerations=(3,4,0),tip_force_yaw_n=5)
        face_load=sum(abs(x) for x in (*guide['front_pitch_yaw_n'],*guide['rear_pitch_yaw_n']))
        d=p['drivetrain']
        expected=d['guide_friction_coefficient_assumed']*(face_load+d['guide_preload_total_n_assumed'])+d['extension_drag_n_assumed']
        self.assertAlmostEqual(guide['friction_n'],expected)
        self.assertGreater(face_load,guide['front_n']+guide['rear_n'])

    def test_segmented_beam_reduces_to_known_uniform_cantilever(self):
        p=copy.deepcopy(e.parameters())
        g=p['geometry']
        g['inner_side_m']=g['outer_side_m']
        g['inner_wall_m']=g['outer_wall_m']
        force=7
        length=1.2
        second=e.square_section(g['outer_side_m'],g['outer_wall_m'])[1]
        expected=force*length**3/(3*p['material']['youngs_modulus_pa']*second)
        self.assertAlmostEqual(e.beam_screen(.5,force,p=p)['tip_deflection_m'],expected,places=12)

    def test_radial_retraction_has_direction(self):
        self.assertTrue(e.radial_catch_match(-4,0,-1.2)['reduces_radial_impact'])
        self.assertFalse(e.radial_catch_match(4,0,-1.2)['reduces_radial_impact'])

    def test_impact_energy_and_velocity_squared_scaling(self):
        self.assertAlmostEqual(e.catch_energy(.05,4,.025)['average_force_n'],16)
        self.assertAlmostEqual(e.catch_energy(.05,4,.025)['energy_j']/e.catch_energy(.05,1,.025)['energy_j'],16)

    def test_bom_exact_arithmetic_and_total_not_fabricated(self):
        totals=e.bom_totals()
        self.assertEqual(totals['line_math_errors'],[])
        self.assertAlmostEqual(totals['purchase_subtotal_usd'],sum(totals['groups_usd'].values()),places=2)
        self.assertGreater(totals['cash_budget_usd'],totals['purchase_subtotal_usd'])

    def test_unverified_motor_never_approved(self):
        result=e.motor_demand_curve(10.0,2.0,8,.9)
        self.assertFalse(result['qualified'])
        self.assertIsNone(result['available_running_torque_nm'])

    def test_invalid_dimensions_and_states_fail(self):
        for side,wall in ((0,.1),(.01,.01),(math.nan,.1)):
            with self.assertRaises(ValueError):
                e.square_section(side,wall)
        for extension in (-.1,.51,math.nan):
            with self.assertRaises(ValueError):
                e.bodies(extension)
        with self.assertRaises(ValueError):
            e.catch_energy(.05,4,0)


if __name__=='__main__':
    unittest.main()
