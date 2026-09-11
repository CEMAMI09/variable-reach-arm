"""Regression tests for physically false acceptance, timing and SI geometry.

Run: python -m unittest discover -s tests -p test_host*.py -v
Core tests use only the Python standard library; image detection is optional.
"""
import math
import importlib.util
import random
import unittest
import tempfile
from functools import partial
from pathlib import Path
from host.kinematics.arm_kinematics import ArmLimits, JointState, Pose, forward, inverse, tip_velocity
from host.planning.reach import select_reach
from host.planning.intercept import (BallState, PlannerLimits, CostWeights, plan_intercept,
                                    predict_ball, time_to_reach, shell_crossing_times, _roots_in_interval)
from host.trajectories.quintic import QuinticSegment, minimum_duration, multi_axis_quintic
from host.planning.collision import KeepoutBox, motion_clear
from host.planning.grasp import ClawTiming, evaluate_grasp, assess_retraction
from host.estimation.ball_estimator import Detection, fit_ballistic, fit_ballistic_result, BallisticTracker
from host.vision.geometry import StereoCalibration, triangulate_rectified
from host.planning.throw import plan_throw_toward
from host.telemetry.logger import TelemetryLogger
from simulation.arm_model.sim_core import run_catch_scenario

# These mathematical regressions deliberately analyze the simplified boom.
# Full-assembly default rejection is exercised separately in test_host_dispatch.
plan_intercept = partial(plan_intercept, collision_model="ideal_boom")
motion_clear = partial(motion_clear, collision_model="ideal_boom")


H = ArmLimits.from_design_file().h

def incoming_horizontal(t=.25, reach=.7):
    return BallState(reach+2*t,0,H-.5*9.81*t*t,-2,0,9.81*t)


class KinematicsTests(unittest.TestCase):
    def test_ik_does_not_clamp_unreachable_positions(self):
        for p in (Pose(.1,0,H),Pose(1.21,0,H),Pose(-.8,0,H),Pose(.1,0,1.5)):
            self.assertIsNone(inverse(p))

    def test_nonfinite_and_invalid_geometry(self):
        self.assertIsNone(inverse(Pose(float('nan'),0,0)))
        with self.assertRaises(ValueError):
            forward(JointState(0,0,float('inf')))
        with self.assertRaises(ValueError):
            ArmLimits(L_min=1.3)

    def test_round_trip_random_workspace(self):
        rng=random.Random(7)
        for _ in range(100):
            q=JointState(rng.uniform(-1.2,1.2),rng.uniform(-.25,1.2),rng.uniform(.7,1.2))
            actual=inverse(forward(q))
            self.assertIsNotNone(actual)
            for a,b in zip(q.__dict__.values(),actual.__dict__.values()):
                self.assertAlmostEqual(a,b,places=11)

    def test_jacobian_velocity_matches_finite_difference(self):
        q,rates=JointState(.2,.3,1),JointState(.4,-.5,.2)
        velocity=tip_velocity(q,rates)
        eps=1e-6
        before=forward(q)
        after=forward(JointState(q.yaw+eps*rates.yaw,q.pitch+eps*rates.pitch,q.L+eps*rates.L))
        for a,b,v in zip(before.__dict__.values(),after.__dict__.values(),velocity.__dict__.values()):
            self.assertAlmostEqual((b-a)/eps,v,places=5)

    def test_reach_shell_not_filled_sphere(self):
        self.assertFalse(select_reach(Pose(.5,0,H)).reachable)
        retracted=select_reach(Pose(.7,0,H))
        self.assertTrue(retracted.reachable)
        self.assertFalse(retracted.extended)
        partial=select_reach(Pose(.9,0,H))
        self.assertAlmostEqual(partial.L_cmd,.9)
        self.assertLess(partial.L_cmd,1.2)

    def test_margin_requires_measured_capture_depth(self):
        with self.assertRaises(ValueError):
            select_reach(Pose(.9,0,H),margin_m=.03)
        self.assertTrue(select_reach(Pose(.69,0,H),capture_depth_m=.02).reachable)
        self.assertFalse(select_reach(Pose(.65,0,H),capture_depth_m=.02).reachable)

    def test_shared_geometry_matches_cad_reference(self):
        lim=ArmLimits.from_design_file()
        self.assertAlmostEqual(lim.L_max-lim.L_min,.5)
        self.assertAlmostEqual(forward(JointState(0,0,lim.L_min),lim).x,.7)


class TrajectoryTests(unittest.TestCase):
    def test_general_quintic_end_conditions(self):
        segment=QuinticSegment(5,1.7,.1,.9,.2,-.1,.3,-.2)
        for actual,expected in zip(segment.sample(5),(.1,.2,.3)):
            self.assertAlmostEqual(actual,expected,places=10)
        for actual,expected in zip(segment.sample(6.7),(.9,-.1,-.2)):
            self.assertAlmostEqual(actual,expected,places=10)

    def test_exact_peaks_match_dense_sample_both_directions(self):
        for displacement in (.5,-.7):
            s=QuinticSegment(0,1.2,0,displacement)
            values=[s.sample(i*s.T/10000) for i in range(10001)]
            peaks=s.rest_to_rest_peaks()
            self.assertAlmostEqual(max(abs(p[1]) for p in values),peaks[0],places=7)
            self.assertAlmostEqual(max(abs(p[2]) for p in values),peaks[1],places=6)
            self.assertAlmostEqual(max(abs(s.jerk(i*s.T/10000)) for i in range(10001)),peaks[2],places=7)

    def test_minimum_duration_is_executable_quintic(self):
        caps=(.48,1.6,10)
        T=minimum_duration(.5,*caps)
        peaks=QuinticSegment(0,T,0,.5).rest_to_rest_peaks()
        self.assertTrue(all(a <= b+1e-10 for a,b in zip(peaks,caps)))
        faster=QuinticSegment(0,.99*T,0,.5).rest_to_rest_peaks()
        self.assertTrue(any(a > b for a,b in zip(faster,caps)))

    def test_invalid_trajectory_and_caps(self):
        for args in ((0,0,0,1),(0,-1,0,1),(0,1,0,float('nan'))):
            with self.assertRaises(ValueError):
                QuinticSegment(*args)
        with self.assertRaises(ValueError):
            minimum_duration(1,0,1,1)
        with self.assertRaises(ValueError):
            PlannerLimits(ext_vel=float('nan'))
        with self.assertRaises(ValueError):
            CostWeights(w_t=-1)


class PlannerTests(unittest.TestCase):
    def setUp(self):
        self.q=JointState(0,0,.7)
        self.ball=incoming_horizontal()

    def test_exact_shell_crossing_between_search_grid_points(self):
        sol=plan_intercept(self.ball,self.q,dt=.073)
        self.assertIsNotNone(sol)
        self.assertAlmostEqual(sol.t,.25,places=8)
        self.assertAlmostEqual(sol.L_cmd,.7,places=9)
        self.assertFalse(sol.extended)
        self.assertFalse(sol.hardware_ready)
        predicted=predict_ball(self.ball,sol.t)
        self.assertLess(math.dist(tuple(predicted.__dict__.values()),tuple(sol.pose.__dict__.values())),1e-9)

    def test_tangent_and_two_roots_do_not_require_sign_change_on_grid(self):
        roots=_roots_in_interval([.06,-.5,1],0,1)
        self.assertAlmostEqual(roots[0],.2)
        self.assertAlmostEqual(roots[1],.3)
        tangent=_roots_in_interval([.123**2,-2*.123,1],0,1)
        self.assertAlmostEqual(tangent[0],.123)

    def test_stale_or_future_observation_rejected(self):
        zero=JointState(0,0,0)
        self.assertIsNone(plan_intercept(self.ball,self.q,now=.11,initial_rates=zero))
        self.assertIsNone(plan_intercept(self.ball,self.q,now=-.01,initial_rates=zero))

    def test_live_rates_required_and_motion_cannot_be_reset(self):
        self.assertIsNone(plan_intercept(self.ball,self.q,now=0))
        self.assertIsNone(plan_intercept(self.ball,self.q,initial_rates=JointState(.01,0,0)))
        self.assertIsNone(plan_intercept(self.ball,self.q,initial_rates=JointState(float('nan'),0,0)))
        self.assertIsNotNone(plan_intercept(self.ball,self.q,now=0,initial_rates=JointState(0,0,0)))

    def test_excessive_command_latency_rejected(self):
        self.assertIsNone(plan_intercept(self.ball,self.q,command_latency=.3,t_horizon=.3))

    def test_behind_arm_or_wrong_approach_cannot_be_accepted(self):
        backward=BallState(-self.ball.x,0,self.ball.z,2,0,self.ball.vz)
        self.assertIsNone(plan_intercept(backward,self.q))
        outward=BallState(.2,0,H,2,0,0)
        self.assertIsNone(plan_intercept(outward,self.q))

    def test_nonfinite_and_unbounded_loop_inputs(self):
        for kwargs in ({'dt':0},{'dt':1e-9},{'t_horizon':float('inf')}):
            with self.assertRaises(ValueError):
                plan_intercept(self.ball,self.q,**kwargs)
        with self.assertRaises(ValueError):
            plan_intercept(BallState(float('nan'),0,0,0,0,0),self.q)

    def test_claw_is_not_assumed_instantaneous(self):
        self.assertIsNone(plan_intercept(self.ball,self.q,require_grasp_timing=True))
        slow=ClawTiming(.12,.01,.08,.035)
        self.assertIsNone(plan_intercept(self.ball,self.q,claw=slow,require_grasp_timing=True))
        hypothetical_fast=ClawTiming(.02,.005,.08,.035)
        sol=plan_intercept(self.ball,self.q,claw=hypothetical_fast,require_grasp_timing=True)
        self.assertIsNotNone(sol)
        self.assertTrue(sol.grasp.timing_pass)
        self.assertFalse(sol.hardware_ready)

    def test_partial_extension_only_with_explicit_faster_hypothetical_caps(self):
        b=BallState(1.31,.75,1.4+3*.9-.5*9.81*.9**2,-.9,0,-3+9.81*.9)
        q=JointState(math.atan2(.75,.5),math.atan2(.75,math.hypot(.5,.75)),.7)
        caps=PlannerLimits(2,2,1.2,6,6,4,40,40,60)
        sol=plan_intercept(b,q,plim=caps)
        self.assertIsNotNone(sol)
        self.assertTrue(.7 < sol.L_cmd < 1.2)
        self.assertLessEqual(time_to_reach(q,sol.joints,caps),sol.t-sol.start_time+1e-10)
        self.assertIsNone(plan_intercept(b,q))

    def test_normal_catch_preferred_over_earlier_unnecessary_extension(self):
        b=incoming_horizontal(.35)
        q=JointState(0,0,.7)
        # Artificial fast caps isolate the reach policy; not hardware specifications.
        caps=PlannerLimits(2,2,2,10,10,10,200,200,200)
        timing_only=CostWeights(w_e=0,w_a=0,w_v=0)
        normal=plan_intercept(b,q,plim=caps,weights=timing_only)
        earliest=plan_intercept(b,q,plim=caps,weights=timing_only,prefer_retracted=False)
        self.assertFalse(normal.extended)
        self.assertTrue(earliest.extended)
        self.assertGreater(normal.t,earliest.t)

    def test_throw_not_executable_heuristic(self):
        with self.assertRaises(NotImplementedError):
            plan_throw_toward(Pose(2,0,1),self.q)


class CollisionAndGraspTests(unittest.TestCase):
    def test_thin_obstacle_between_endpoints_is_detected(self):
        q0,q1=JointState(-.3,0,.7),JointState(.3,0,.7)
        lim=ArmLimits(swept_radius=.005)
        box=KeepoutBox((.5,-.001,H-.001),(.51,.001,H+.001))
        self.assertTrue(motion_clear(q0,q1,lim))
        self.assertFalse(motion_clear(q0,q1,lim,(box,)))

    def test_rear_overhang_and_floor_are_checked(self):
        q=JointState(0,0,.7)
        rear=KeepoutBox((-.3,-.01,H-.01),(-.28,.01,H+.01))
        self.assertFalse(motion_clear(q,q,ArmLimits(),(rear,)))
        self.assertFalse(motion_clear(q,JointState(0,-.25,1.2),ArmLimits(floor_z=H-.25)))

    def test_closure_depth_and_sideways_constraints(self):
        q=JointState(0,0,.9)
        self.assertFalse(evaluate_grasp(q,Pose(-4,0,0),ClawTiming(.12,.01,.08,.04)).timing_pass)
        side=evaluate_grasp(q,Pose(-.5,3,0),ClawTiming(.03,0,.08,.04))
        self.assertEqual(side.reason,'closure_too_slow_for_lateral_clearance')
        self.assertFalse(evaluate_grasp(q,Pose(1,0,0),ClawTiming(.03,0,.08,.04)).timing_pass)

    def test_retraction_direction_and_no_stroke_at_normal_reach(self):
        zero=JointState(0,0,0)
        result=assess_retraction(JointState(0,0,1),zero,Pose(-4,0,0),.7,1.2)
        self.assertAlmostEqual(result.suggested_retraction_rate_m_s,-1.2)
        self.assertAlmostEqual(result.residual_inward_speed_m_s,2.8)
        self.assertEqual(assess_retraction(JointState(0,0,.7),zero,Pose(-4,0,0),.7,1.2).suggested_retraction_rate_m_s,0)
        self.assertEqual(assess_retraction(JointState(0,0,1),zero,Pose(4,0,0),.7,1.2).suggested_retraction_rate_m_s,0)


class EstimatorTests(unittest.TestCase):
    def detections(self,epoch=1000000):
        return [Detection(epoch+t,1-2*t,.2+.1*t,1.5+3*t-.5*9.81*t*t) for t in (0,.02,.04,.06,.08)]

    def test_latest_epoch_and_correct_gravity_velocity(self):
        dets=self.detections()
        fit=fit_ballistic_result(dets)
        self.assertIsNotNone(fit)
        self.assertEqual(fit.state.t0,dets[-1].t)
        self.assertAlmostEqual(fit.state.x,dets[-1].x,places=8)
        self.assertAlmostEqual(fit.state.vx,-2,places=7)
        self.assertAlmostEqual(fit.state.vz,3-9.81*.08,places=7)
        self.assertLess(fit.rms_residual_m,1e-8)

    def test_timestamp_reordering_duplicates_gap_and_nonfinite_rejected(self):
        dets=self.detections()
        for seq in (list(reversed(dets)),[dets[0],dets[0],dets[2]],
                    [dets[0],dets[1],Detection(dets[-1].t+1,1,1,1)],
                    [dets[0],dets[1],Detection(dets[2].t,float('nan'),0,0)]):
            self.assertIsNone(fit_ballistic(seq))

    def test_outlier_rejects_fit(self):
        dets=self.detections()
        d=dets[2]
        dets[2]=Detection(d.t,d.x+1,d.y,d.z)
        self.assertIsNone(fit_ballistic(dets))

    def test_tracker_invalidates_on_dropout_and_is_not_stale(self):
        tracker=BallisticTracker()
        dets=self.detections()
        for d in dets:
            tracker.update(d)
        self.assertIsNotNone(tracker.current(dets[-1].t+.02))
        self.assertIsNone(tracker.current(dets[-1].t+.11))
        self.assertIsNone(tracker.update(Detection(dets[-1].t+.2,1,1,1)))
        self.assertIsNone(tracker.current(dets[-1].t+.2))


class VisionTests(unittest.TestCase):
    def setUp(self):
        self.cal=StereoCalibration(600,600,320,240,.12,((0,0,1),(-1,0,0),(0,-1,0)),(0,0,H),'synthetic')

    def test_rectified_world_geometry_and_time(self):
        result=triangulate_rectified((380,240),(320,240),10,10,10.02,self.cal)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.detection.x,1.2)
        self.assertAlmostEqual(result.detection.y,-.12)
        self.assertAlmostEqual(result.detection.z,H)
        self.assertEqual(result.detection.t,10)

    def test_moving_stereo_skew_is_not_disparity_only_uncertainty(self):
        # 4m/s lateral ball at z1.2m moves8mm between the two exposures.
        # Naive triangulation reports1.2857m:85.7mm error, not11.5mm.
        args=((380,240),(324,240),0,.002,.02,self.cal)
        self.assertIsNone(triangulate_rectified(*args))
        self.assertIsNone(triangulate_rectified(*args,max_ball_speed_m_s=4))
        relaxed=triangulate_rectified(*args,max_ball_speed_m_s=4,max_depth_uncertainty_m=.12)
        self.assertIsNotNone(relaxed)
        self.assertGreaterEqual(relaxed.depth_uncertainty_m,abs(relaxed.depth_m-1.2))
        # Synchronization uncertainty matters even when stamped times are equal.
        self.assertIsNone(triangulate_rectified((380,240),(320,240),0,0,.02,self.cal,
                          pair_timestamp_uncertainty_s=.002,max_ball_speed_m_s=4))

    def test_small_bounded_motion_skew_can_pass(self):
        result=triangulate_rectified((380,240),(320.04,240),0,.00002,.02,self.cal,
                                    max_ball_speed_m_s=4)
        self.assertIsNotNone(result)
        self.assertGreaterEqual(result.depth_uncertainty_m,abs(result.depth_m-1.2))

    def test_skew_stale_bad_disparity_and_epipolar_gates(self):
        cases=[((380,240),(320,240),10,10.01,10.02),
               ((380,240),(320,240),10,10,10.2),
               ((320,240),(380,240),10,10,10.02),
               ((380,240),(320,250),10,10,10.02),
               ((322,240),(320,240),10,10,10.02),
               ((380,240),(320,240),10,10,9.9)]
        for args in cases:
            self.assertIsNone(triangulate_rectified(*args,self.cal))

    def test_invalid_calibration_rotation(self):
        with self.assertRaises(ValueError):
            StereoCalibration(600,600,320,240,.12,((1,0,0),(0,1,0),(0,0,-1)),(0,0,0),'bad')


@unittest.skipUnless(importlib.util.find_spec('cv2') and importlib.util.find_spec('numpy'),
                     'optional OpenCV/NumPy image-test dependencies not installed')
class ImageDetectionTests(unittest.TestCase):
    def test_round_ball_beats_larger_elongated_same_color_object(self):
        import cv2
        import numpy as np
        from host.vision.ball_detect import detect_ball_bgr
        image=np.zeros((200,200,3),np.uint8)
        cv2.circle(image,(40,120),16,(0,140,255),-1)
        cv2.rectangle(image,(80,20),(190,40),(0,140,255),-1)
        blob=detect_ball_bgr(image,exposure_s=12.3)
        self.assertIsNotNone(blob)
        self.assertAlmostEqual(blob.u,40,places=1)
        self.assertAlmostEqual(blob.v,120,places=1)
        self.assertEqual(blob.exposure_s,12.3)

    def test_blank_and_invalid_frames(self):
        import numpy as np
        from host.vision.ball_detect import detect_ball_bgr
        self.assertIsNone(detect_ball_bgr(np.zeros((80,80,3),np.uint8)))
        with self.assertRaises(ValueError):
            detect_ball_bgr(np.zeros((80,80),np.uint8))


class LoggingTests(unittest.TestCase):
    def test_existing_runs_cannot_be_silently_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'run.csv'
            with TelemetryLogger(path) as logger:
                logger.log({'timestamp':1,'time_domain':'host_monotonic_s'})
            with self.assertRaises(FileExistsError):
                TelemetryLogger(path)
            self.assertIn('host_monotonic_s',path.read_text())

    def test_misspelled_telemetry_is_not_silently_discarded(self):
        with tempfile.TemporaryDirectory() as directory:
            with TelemetryLogger(Path(directory)/'run.csv') as logger:
                with self.assertRaises(ValueError):
                    logger.log({'yaw_poosition':1})


class SimulationTests(unittest.TestCase):
    def test_simulation_checks_miss_and_never_claims_physical_catch(self):
        result=run_catch_scenario(incoming_horizontal(),q0=JointState(0,0,.7),include_dynamics=True)
        self.assertTrue(result.intercept_found)
        self.assertLess(result.ideal_miss_m,1e-9)
        self.assertTrue(result.derivative_limits_pass)
        self.assertFalse(result.physical_catch_validated)
        self.assertEqual(len(result.arm_path),201)
        self.assertFalse(result.demand_screen['motor_capacity_qualified'])

    def test_inertia_is_recomputed_for_executed_extension(self):
        from simulation.arm_model.dynamics_screen import profile_demand
        lim=ArmLimits.from_design_file()
        segments=multi_axis_quintic([0,0,.7],[.1,.1,1.2],5)
        screen=profile_demand(segments,lim)
        minimum,maximum=screen['pitch_inertia_min_max_kgm2']
        self.assertGreater(maximum,minimum*1.5)
        self.assertGreater(screen['sampled_required_load_peaks']['extension_n'],0)


if __name__ == '__main__':
    unittest.main()

