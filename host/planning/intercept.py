"""Bounded offline interception search; a candidate is never a hardware permit."""
from __future__ import annotations
import math
import time
from dataclasses import dataclass, field
from typing import Callable
from host.kinematics.arm_kinematics import ArmLimits, JointState, Pose, inverse, in_workspace
from host.planning.reach import select_reach
from host.planning.collision import KeepoutBox, motion_clear
from host.planning.grasp import ClawTiming, GraspFeasibility, evaluate_grasp
from host.trajectories.quintic import minimum_duration


@dataclass(frozen=True)
class BallState:
    x: float
    y: float
    z: float
    vx: float
    vy: float
    vz: float
    t0: float = 0.0  # latest observation epoch in host monotonic exposure time


@dataclass(frozen=True)
class InterceptSolution:
    t: float
    pose: Pose
    joints: JointState
    L_cmd: float
    extended: bool
    cost: float
    start_time: float = 0.0
    grasp: GraspFeasibility | None = None
    hardware_ready: bool = False
    initial_joints: JointState | None = None
    observation_expires_at: float | None = None
    collision_model: str = "ideal_boom"
    self_collision_verified: bool = field(default=False, init=False)


@dataclass(frozen=True)
class PlannerLimits:
    # Proposed BENCH caps only. Hardware torque/thermal qualification is required.
    yaw_vel: float = 0.35
    pitch_vel: float = 0.35
    ext_vel: float = 0.15
    yaw_acc: float = 0.70
    pitch_acc: float = 0.70
    ext_acc: float = 0.50
    yaw_jerk: float = 4.0
    pitch_jerk: float = 4.0
    ext_jerk: float = 3.0

    def __post_init__(self):
        if not all(math.isfinite(v) and v > 0 for v in self.__dict__.values()):
            raise ValueError("planner derivative limits must be finite and positive")


@dataclass(frozen=True)
class CostWeights:
    w_t: float = 1.0
    w_e: float = 0.5
    w_a: float = 0.1  # angular displacement penalty, NOT actual acceleration
    w_v: float = 0.05  # extension displacement penalty, NOT actual velocity

    def __post_init__(self):
        if not all(math.isfinite(v) and v >= 0 for v in self.__dict__.values()):
            raise ValueError("cost weights must be finite and nonnegative")


def predict_ball(b: BallState, t: float, g: float = 9.81) -> Pose:
    if not all(math.isfinite(v) for v in (*b.__dict__.values(), t, g)) or g <= 0:
        raise ValueError("invalid ballistic input")
    dt = t-b.t0
    p = Pose(b.x+b.vx*dt, b.y+b.vy*dt, b.z+b.vz*dt-0.5*g*dt*dt)
    if not all(math.isfinite(v) for v in p.__dict__.values()):
        raise ValueError("ballistic prediction overflow")
    return p


def time_to_reach(q0: JointState, q1: JointState, plim: PlannerLimits) -> float:
    """Exact rest-to-rest quintic duration under the supplied derivative caps.

    This only proves kinematic feasibility. Caps must eventually come from a
    measured length-dependent torque/speed/thermal envelope; fixed bench caps
    are NOT an actuator model and do not certify simultaneous motion.
    """
    return max(minimum_duration(q1.yaw-q0.yaw, plim.yaw_vel, plim.yaw_acc, plim.yaw_jerk),
               minimum_duration(q1.pitch-q0.pitch, plim.pitch_vel, plim.pitch_acc, plim.pitch_jerk),
               minimum_duration(q1.L-q0.L, plim.ext_vel, plim.ext_acc, plim.ext_jerk))


def _roots_in_interval(coeffs: list[float], low: float, high: float) -> list[float]:
    """Isolate roots using derivative extrema, including a tangent shell crossing."""
    while len(coeffs) > 1 and coeffs[-1] == 0:
        coeffs = coeffs[:-1]
    def value(x):
        result = 0.0
        for c in reversed(coeffs):
            result = result*x+c
        return result
    if len(coeffs) == 1:
        return []
    if len(coeffs) == 2:
        root = -coeffs[0]/coeffs[1]
        return [root] if low <= root <= high else []
    extrema = _roots_in_interval([i*c for i,c in enumerate(coeffs)][1:], low, high)
    points = sorted(set([low, high, *extrema]))
    roots = [p for p in points if abs(value(p)) <= 1e-12]
    for a,b in zip(points,points[1:]):
        fa,fb = value(a),value(b)
        if fa*fb >= 0:
            continue
        for _ in range(55):
            mid = (a+b)/2
            fm = value(mid)
            if fa*fm <= 0:
                b = mid
            else:
                a,fa = mid,fm
        roots.append((a+b)/2)
    return sorted(set(roots))


def shell_crossing_times(ball: BallState, radius: float, lim: ArmLimits,
                         start: float, end: float) -> list[float]:
    """Ballistic sphere intersections avoid dependence on candidate-grid luck."""
    dz = ball.z-lim.h
    coefficients = [ball.x**2+ball.y**2+dz**2-radius**2,
                    2*(ball.x*ball.vx+ball.y*ball.vy+dz*ball.vz),
                    ball.vx**2+ball.vy**2+ball.vz**2-9.81*dz,
                    -9.81*ball.vz, 0.25*9.81**2]
    return [ball.t0+t for t in _roots_in_interval(coefficients, start-ball.t0, end-ball.t0)]


def plan_intercept(ball: BallState, q0: JointState, lim: ArmLimits | None = None,
                   plim: PlannerLimits | None = None, weights: CostWeights | None = None,
                   t_horizon: float = 1.2, dt: float = 0.02, *,
                   now: float | None = None, command_latency: float = 0.02,
                   max_observation_age: float = 0.10, initial_rates: JointState | None = None,
                   approach_cosine_min: float = 0.7, claw: ClawTiming | None = None,
                   require_grasp_timing: bool = False,
                   prefer_retracted: bool = True,
                   planning_budget_s: float = .02,
                   clock: Callable[[], float] = time.monotonic,
                   collision_model: str = "full_assembly",
                   keepouts: tuple[KeepoutBox, ...] = ()) -> InterceptSolution | None:
    """Rest-to-rest synchronized motion with exact radial reach and finite jerk.

    Times share the host monotonic exposure clock. now=None is synthetic data
    only. Live callers must supply current time, measured latency and rates.
    Moving-state replanning is explicitly rejected, not reset to zero velocity.
    The mouth faces outward radially, so the ball must enter from that side.

    require_grasp_timing=True requires measured active-claw timing and ball-center
    clearances; successful closure is still a contact-test gate. Torque, CAD
    self-collision and hardware safety qualification are not inferred by a plan.
    A feasible normal-shell catch is preferred before cost optimization. Set
    prefer_retracted=False explicitly to prioritize the weighted timing cost.
    The start schedule reserves planning_budget_s before communication latency.
    Live computation exceeding that budget fails closed. Revalidate the unchanged
    initial state and deadline at dispatch; never compress or skip a late profile.
    Full-assembly planning currently fails closed because its continuous motion
    envelope is unqualified. Explicit ideal_boom mode is offline analysis only.
    """
    live_time_supplied = now is not None
    entered = clock() if live_time_supplied else None
    lim, plim, weights = lim or ArmLimits.from_design_file(), plim or PlannerLimits(), weights or CostWeights()
    now = ball.t0 if now is None else now
    if not all(math.isfinite(v) for v in (*ball.__dict__.values(), now, t_horizon, dt,
                                         command_latency, max_observation_age, approach_cosine_min, planning_budget_s)):
        raise ValueError("non-finite planning input")
    if dt <= 0 or t_horizon <= 0 or command_latency < 0 or planning_budget_s <= 0 or max_observation_age < 0 or not 0 <= approach_cosine_min <= 1:
        raise ValueError("invalid timing or approach constraint")
    if t_horizon/dt > 10000:
        raise ValueError("candidate count exceeds bounded planning budget")
    if not isinstance(prefer_retracted, bool) or not isinstance(require_grasp_timing, bool):
        raise ValueError("planner policy flags must be boolean")
    if collision_model not in ("full_assembly", "ideal_boom"):
        raise ValueError("unknown collision model")
    if collision_model == "full_assembly":
        return None  # Known interference; no validated full-assembly workspace.
    if now < ball.t0 or now-ball.t0 > max_observation_age or not in_workspace(q0, lim):
        return None
    if (live_time_supplied and initial_rates is None) or (require_grasp_timing and claw is None):
        return None
    if initial_rates is not None and any(not math.isfinite(v) or abs(v) > 1e-6
                                         for v in initial_rates.__dict__.values()):
        return None
    if entered is not None and not math.isfinite(entered):
        return None
    def expired():
        if entered is None:
            return False  # deterministic offline replay uses the reserved schedule
        elapsed = clock()-entered
        return not math.isfinite(elapsed) or not 0 <= elapsed <= planning_budget_s
    start, end = now+planning_budget_s+command_latency, now+t_horizon
    if start >= end:
        return None
    times = [start+i*dt for i in range(1, int((end-start)/dt)+1)] + [end]
    for radius in (lim.L_normal, lim.L_max):
        times.extend(shell_crossing_times(ball, radius, lim, start, end))
    best = None
    for t in sorted(set(times)):
        if expired():
            return None
        if t <= start:
            continue
        p = predict_ball(ball, t)
        if p.z < lim.floor_z:
            # Ball at/below ground cannot be intercepted before an unmodeled bounce.
            # Do not break for rising observations: those may enter the volume later.
            continue
        reach = select_reach(p, lim)
        if not reach.reachable or reach.L_req < 1e-6:
            continue
        # Only a roundoff correction at exact normal/max shell crossings.
        scale = reach.L_cmd/reach.L_req
        p_cmd = Pose(p.x*scale, p.y*scale, lim.h+(p.z-lim.h)*scale)
        q = inverse(p_cmd, lim)
        if q is None:
            continue
        q = JointState(q.yaw, q.pitch, reach.L_cmd)
        radial = (math.cos(q.pitch)*math.cos(q.yaw), math.cos(q.pitch)*math.sin(q.yaw), math.sin(q.pitch))
        velocity = (ball.vx, ball.vy, ball.vz-9.81*(t-ball.t0))
        speed = math.sqrt(sum(v*v for v in velocity))
        approach = -sum(a*b for a,b in zip(radial,velocity))
        if speed < 1e-6 or approach/speed < approach_cosine_min:
            continue
        if time_to_reach(q0, q, plim) > t-start+1e-12:
            continue
        if not motion_clear(q0, q, lim, keepouts, collision_model=collision_model):
            continue
        grasp = evaluate_grasp(q, Pose(*velocity), claw) if claw else None
        if grasp is not None and not grasp.timing_pass:
            continue
        angular_distance = abs(q.yaw-q0.yaw)+abs(q.pitch-q0.pitch)
        extension_distance = abs(q.L-q0.L)
        cost = (weights.w_t*(t-now) + weights.w_e*max(0.0,q.L-lim.L_normal)
                + weights.w_a*angular_distance + weights.w_v*extension_distance)
        solution = InterceptSolution(t,p_cmd,q,reach.L_cmd,reach.extended,cost,start,grasp,
                                     initial_joints=q0,observation_expires_at=ball.t0+max_observation_age,
                                     collision_model=collision_model)
        priority = (solution.extended if prefer_retracted else False, solution.cost)
        if best is None or priority < (best.extended if prefer_retracted else False, best.cost):
            best = solution
    return None if expired() else best


def schedule_timing_valid(solution: InterceptSolution, measured: JointState,
                            measured_rates: JointState, *, now: float,
                            measurement_time: float, command_latency: float,
                            max_feedback_age: float = .02) -> bool:
    """Necessary offline scheduling check; NEVER a hardware enable permission.

    Requires the same stationary start state used by the mathematical proof.
    A changed pose requires replanning; this function does not silently stretch,
    compress or splice a trajectory. Actual camera/session/fault/driver/collision
    validity and a deterministic executor remain additional unimplemented gates.
    """
    values=(*measured.__dict__.values(),*measured_rates.__dict__.values(),now,
            measurement_time,command_latency,max_feedback_age,solution.start_time,solution.t)
    if not all(math.isfinite(v) for v in values) or command_latency < 0 or max_feedback_age <= 0:
        return False
    if not 0 <= now-measurement_time <= max_feedback_age:
        return False
    if solution.initial_joints is None or measured != solution.initial_joints:
        return False
    if any(abs(v)>1e-6 for v in measured_rates.__dict__.values()):
        return False
    if solution.observation_expires_at is None or now>solution.observation_expires_at:
        return False
    return now+command_latency <= solution.start_time < solution.t


def dispatch_schedule_valid(solution: InterceptSolution, measured: JointState,
                            measured_rates: JointState, *, now: float,
                            measurement_time: float, command_latency: float,
                            max_feedback_age: float = .02) -> bool:
    """Reject unqualified geometry even when an offline schedule meets its deadline.

    This remains a necessary check, not hardware permission. No current candidate
    can pass: the full assembly has no qualified continuous collision validator.
    """
    if solution.collision_model != "full_assembly" or not solution.self_collision_verified:
        return False
    return schedule_timing_valid(solution, measured, measured_rates, now=now,
                                 measurement_time=measurement_time,
                                 command_latency=command_latency,
                                 max_feedback_age=max_feedback_age)
