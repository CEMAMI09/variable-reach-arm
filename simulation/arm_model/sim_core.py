"""Projectile + arm kinematics simulation for planner validation."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from host.kinematics.arm_kinematics import ArmLimits, JointState, forward, in_workspace
from host.planning.intercept import BallState, plan_intercept, predict_ball, PlannerLimits
from host.trajectories.quintic import multi_axis_quintic
from host.planning.grasp import ClawTiming
from host.planning.collision import KeepoutBox


@dataclass
class SimResult:
    intercept_found: bool
    t_intercept: float | None
    extended: bool
    L_cmd: float | None
    ball_path: list[tuple[float, float, float, float]]
    message: str
    ideal_miss_m: float | None = None
    derivative_limits_pass: bool = False
    physical_catch_validated: bool = False
    grasp_timing_pass: bool | None = None
    arm_path: list[tuple[float,float,float,float]] = field(default_factory=list)
    demand_screen: dict | None = None
    collision_model: str = "ideal_boom"
    self_collision_verified: bool = False


def run_catch_scenario(
    ball: BallState,
    q0: JointState | None = None,
    lim: ArmLimits | None = None,
    plim: PlannerLimits | None = None,
    *,
    claw: ClawTiming | None = None,
    require_grasp_timing: bool = False,
    keepouts: tuple[KeepoutBox, ...] = (),
    include_dynamics: bool = False,
) -> SimResult:
    lim = lim or ArmLimits.from_design_file()
    q0 = q0 or JointState(0.0, math.radians(20), lim.L_normal)
    path = []
    for i in range(60):
        t = ball.t0 + i * 0.02
        p = predict_ball(ball, t)
        path.append((t, p.x, p.y, p.z))
        if p.z < 0:
            break

    plim=plim or PlannerLimits()
    sol = plan_intercept(ball, q0, lim=lim,plim=plim,claw=claw,
                         require_grasp_timing=require_grasp_timing,keepouts=keepouts,
                         collision_model="ideal_boom")
    if sol is None:
        return SimResult(False, None, False, None, path, "no_feasible_intercept")
    segments=multi_axis_quintic([q0.yaw,q0.pitch,q0.L],[sol.joints.yaw,sol.joints.pitch,sol.joints.L],sol.t-sol.start_time,sol.start_time)
    limits=[(plim.yaw_vel,plim.yaw_acc,plim.yaw_jerk),(plim.pitch_vel,plim.pitch_acc,plim.pitch_jerk),(plim.ext_vel,plim.ext_acc,plim.ext_jerk)]
    derivatives_ok=all(all(a<=b+1e-9 for a,b in zip(seg.rest_to_rest_peaks(),cap)) for seg,cap in zip(segments,limits))
    arm_path=[]
    for i in range(201):
        time=sol.start_time+(sol.t-sol.start_time)*i/200
        q=JointState(*(seg.sample(time)[0] for seg in segments))
        arm_path.append((time,q.yaw,q.pitch,q.L))
        if not in_workspace(q,lim):
            raise AssertionError('planner path leaves workspace')
    actual=forward(q,lim)
    predicted=predict_ball(ball,sol.t)
    miss=math.dist((actual.x,actual.y,actual.z),(predicted.x,predicted.y,predicted.z))
    demand = None
    if include_dynamics:
        from simulation.arm_model.dynamics_screen import profile_demand
        demand = profile_demand(segments,lim)
    return SimResult(
        True,
        sol.t,
        sol.extended,
        sol.L_cmd,
        path,
        f"ideal geometry only: miss={miss:.6f}m derivatives_ok={derivatives_ok} extended={sol.extended}",
        miss,derivatives_ok,False,
        sol.grasp.timing_pass if sol.grasp else None,arm_path,demand,
    )


def demo() -> None:
    # Start roughly aimed to illustrate planner (not cold from zero).
    q0 = JointState(0.0, 0.0, 0.70)

    # Exact 700mm shell crossing at t=.25; pre-aimed arm holds its position.
    ball_a = BallState(x=1.2, y=0.0, z=0.65-0.5*9.81*0.25**2, vx=-2.0, vy=0.0, vz=9.81*0.25)

    # Case B: bench caps correctly reject the original optimistic vertical toss.
    ball_b = BallState(x=1.0, y=0.0, z=1.4, vx=0.0, vy=0.0, vz=2.0)

    for name, ball in [("A_normal", ball_a), ("B_extend", ball_b)]:
        r = run_catch_scenario(ball, q0=q0)
        print(
            name,
            r.message,
            "L_cmd",
            None if r.L_cmd is None else round(r.L_cmd, 3),
            "t",
            None if r.t_intercept is None else round(r.t_intercept, 3),
            "extended",
            r.extended,
        )
    # Explicitly hypothetical design-target caps. This demonstrates partial
    # extension only, not motor capacity or a completed grasp.
    target_caps=PlannerLimits(2,2,1.2,6,6,4,40,40,60)
    # Its constant 750mm lateral offset makes every normal-shell target impossible.
    ball_c=BallState(1.31,.75,1.4+3*.9-.5*9.81*.9**2,-.9,0,-3+9.81*.9)
    prepared=JointState(math.atan2(.75,.5),math.atan2(.75,math.hypot(.5,.75)),.7)
    r=run_catch_scenario(ball_c,q0=prepared,plim=target_caps,include_dynamics=True)
    print("C_hypothetical_partial_extension",r.message,"physical_catch_validated",r.physical_catch_validated)
    print("Required load screen:",r.demand_screen)
    slow_claw=ClawTiming(.12,.01,.08,.035)
    r=run_catch_scenario(ball_a,q0=q0,claw=slow_claw,require_grasp_timing=True)
    print("D_closure_delay_rejection",r.message)


if __name__ == "__main__":
    demo()
