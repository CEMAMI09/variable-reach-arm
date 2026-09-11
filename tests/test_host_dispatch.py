"""Deadline and configuration regressions from independent software critique."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from host.kinematics.arm_kinematics import JointState, Pose, forward, inverse
from host.planning.intercept import BallState, plan_intercept, dispatch_schedule_valid, schedule_timing_valid
from host.planning.collision import motion_clear
from host.kinematics.arm_kinematics import ArmLimits
from host.planning.reach import select_reach
from host.trajectories.quintic import QuinticSegment


class DispatchTests(unittest.TestCase):
    def test_segment_time_domain_has_consistent_derivatives(self):
        held=QuinticSegment(0,1,0,2)
        self.assertEqual(held.sample(2),(2,0,0))
        self.assertEqual(held.jerk(2),0)
        moving=QuinticSegment(0,1,0,2,v1=1)
        with self.assertRaises(ValueError):moving.sample(2)
        with self.assertRaises(ValueError):moving.jerk(-1)
    def setUp(self):
        self.q=JointState(0,0,.7)
        self.rates=JointState(0,0,0)
        self.ball=BallState(1.2,0,ArmLimits.from_design_file().h-.5*9.81*.25**2,-2,0,9.81*.25)

    def plan(self,**kwargs):
        return plan_intercept(self.ball,self.q,now=0,initial_rates=self.rates,
                              collision_model="ideal_boom",**kwargs)

    def test_planning_budget_is_reserved_and_overrun_rejects(self):
        sol=self.plan(clock=lambda:0)
        self.assertIsNotNone(sol)
        self.assertAlmostEqual(sol.start_time,.04)
        times=iter([0,.096])
        self.assertIsNone(self.plan(dt=.00012,clock=lambda:next(times,.096)))

    def test_dispatch_rejects_late_changed_moving_and_stale_states(self):
        sol=self.plan(clock=lambda:0)
        def check(q=None,rates=None,**kw):
            args=dict(now=.01,measurement_time=.009,command_latency=.02)
            args.update(kw)
            return schedule_timing_valid(sol,q or self.q,rates or self.rates,**args)
        self.assertTrue(check())
        self.assertFalse(sol.hardware_ready)
        self.assertFalse(check(now=.03))  # cannot arrive before reserved start
        self.assertFalse(check(q=JointState(.001,0,.7)))
        self.assertFalse(check(rates=JointState(0,0,.01)))
        self.assertFalse(check(measurement_time=-.1))
        self.assertFalse(check(measurement_time=.02))
        self.assertFalse(check(command_latency=float('nan')))

    def test_default_geometry_comes_from_shared_file(self):
        source=Path(__file__).resolve().parents[1]/'engineering/design_parameters.json'
        data=json.loads(source.read_text())
        data['geometry'].update(pivot_height_m=.9,normal_reach_m=.8,maximum_reach_m=1.3)
        with patch('host.kinematics.arm_kinematics.Path.read_text',return_value=json.dumps(data)):
            q=JointState(0,0,.8)
            self.assertEqual(forward(q),Pose(.8,0,.9))
            self.assertEqual(inverse(Pose(.8,0,.9)),q)
            self.assertFalse(select_reach(Pose(.7,0,.9)).reachable)
            ball=BallState(1.3,0,.9-.5*9.81*.25**2,-2,0,9.81*.25)
            sol=plan_intercept(ball,q,collision_model="ideal_boom")
            self.assertIsNotNone(sol)
            self.assertAlmostEqual(sol.L_cmd,.8)

    def test_full_assembly_default_fails_closed_without_changing_requirements(self):
        self.assertAlmostEqual(ArmLimits.from_design_file().pitch_max, 70*3.141592653589793/180)
        self.assertIsNone(plan_intercept(self.ball,self.q))
        self.assertFalse(motion_clear(self.q,self.q,ArmLimits.from_design_file()))
        sol=self.plan(clock=lambda:0)
        self.assertIsNotNone(sol)
        self.assertEqual(sol.collision_model,"ideal_boom")
        self.assertFalse(sol.self_collision_verified)
        self.assertFalse(dispatch_schedule_valid(sol,self.q,self.rates,
            now=.01,measurement_time=.009,command_latency=.02))
        # A textual status edit alone cannot create a continuous collision proof.
        source=Path(__file__).resolve().parents[1]/'engineering/design_parameters.json'
        data=json.loads(source.read_text())
        data['workspace_validation']={'status':'qualified','validated_envelope':None}
        with patch('host.kinematics.arm_kinematics.Path.read_text',return_value=json.dumps(data)):
            self.assertIsNone(plan_intercept(self.ball,self.q))

    def test_unknown_collision_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            plan_intercept(self.ball,self.q,collision_model="qualified")
        with self.assertRaises(ValueError):
            motion_clear(self.q,self.q,ArmLimits(),collision_model="qualified")


if __name__=='__main__':unittest.main()

