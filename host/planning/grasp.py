"""Conservative active-finger closing-time feasibility, not a contact simulator."""
from __future__ import annotations
import math
from dataclasses import dataclass
from host.kinematics.arm_kinematics import JointState, Pose, tip_velocity


@dataclass(frozen=True)
class ClawTiming:
    # All geometry below must be measured for a specified ball and finger posture.
    close_time_s: float
    sensor_command_latency_s: float
    usable_depth_m: float  # ball-center travel allowed before backstop/escape
    lateral_clearance_m: float  # aperture radius minus ball radius and error budget

    def __post_init__(self):
        values = tuple(self.__dict__.values())
        if not all(math.isfinite(x) for x in values):
            raise ValueError("finite claw parameters required")
        if self.close_time_s <= 0 or self.sensor_command_latency_s < 0:
            raise ValueError("invalid claw timing")
        if self.usable_depth_m <= 0 or self.lateral_clearance_m <= 0:
            raise ValueError("positive ball-center clearance required")


@dataclass(frozen=True)
class GraspFeasibility:
    timing_pass: bool
    inward_speed_m_s: float
    inward_travel_m: float
    lateral_travel_bound_m: float
    time_to_closed_s: float
    reason: str


def evaluate_grasp(q: JointState, ball_velocity: Pose, claw: ClawTiming,
                   gravity: float = 9.81) -> GraspFeasibility:
    """Ball enters the mouth at t=0; arm holds still while fingers close.

    Uses the ballistic ball-center path during measured trigger+closure delay.
    No pre-trigger guessing, instantaneous closing, or passive net is assumed.
    Passing this bound is necessary, not proof fingers retain the ball: finger
    swept volume, grip force, impact compliance and timing jitter need tests.
    """
    if not all(math.isfinite(v) for v in (*q.__dict__.values(), *ball_velocity.__dict__.values(), gravity)) or gravity <= 0:
        raise ValueError("invalid grasp state")
    r = (math.cos(q.pitch)*math.cos(q.yaw), math.cos(q.pitch)*math.sin(q.yaw), math.sin(q.pitch))
    v = (ball_velocity.x, ball_velocity.y, ball_velocity.z)
    vr = sum(a*b for a, b in zip(v, r))
    t = claw.close_time_s + claw.sensor_command_latency_s
    inward_acc = gravity*r[2]
    inward = -vr*t + .5*inward_acc*t*t
    tangent_speed = math.sqrt(max(0, sum(x*x for x in v)-vr*vr))
    tangent_acc = gravity*math.sqrt(max(0, 1-r[2]*r[2]))
    lateral_bound = tangent_speed*t + .5*tangent_acc*t*t
    if min(-vr, -vr+inward_acc*t) <= 0:
        reason = "ball_not_continuously_entering"
    elif inward > claw.usable_depth_m:
        reason = "closure_too_slow_for_depth"
    elif lateral_bound > claw.lateral_clearance_m:
        reason = "closure_too_slow_for_lateral_clearance"
    else:
        reason = "timing_only_pass_requires_contact_testing"
    return GraspFeasibility(reason.startswith("timing_only"), -vr, inward, lateral_bound, t, reason)


@dataclass(frozen=True)
class ImpactAssessment:
    relative_speed_m_s: float
    inward_relative_speed_m_s: float
    tangential_relative_speed_m_s: float
    available_retraction_m: float
    suggested_retraction_rate_m_s: float
    residual_inward_speed_m_s: float


def assess_retraction(q: JointState, rates: JointState, ball_velocity: Pose,
                      L_min: float, ext_speed_cap: float) -> ImpactAssessment:
    """Offline radial velocity-matching assessment. Never emits a motor command.

    Retraction helps an inward-moving ball only. At L_min it is unavailable.
    Tangential relative velocity requires angular motion or local compliance.
    Finite acceleration, jerk, force control and stopping distance are separate
    gates; the suggested steady speed cannot be applied as a step.
    """
    values = (*q.__dict__.values(), *rates.__dict__.values(), *ball_velocity.__dict__.values(), L_min, ext_speed_cap)
    if not all(math.isfinite(v) for v in values) or ext_speed_cap <= 0 or L_min <= 0 or q.L < L_min:
        raise ValueError("invalid impact inputs")
    hand = tip_velocity(q, rates)
    rel = (ball_velocity.x-hand.x, ball_velocity.y-hand.y, ball_velocity.z-hand.z)
    r = (math.cos(q.pitch)*math.cos(q.yaw), math.cos(q.pitch)*math.sin(q.yaw), math.sin(q.pitch))
    radial = sum(a*b for a,b in zip(rel,r))
    speed = math.sqrt(sum(v*v for v in rel))
    stroke = q.L-L_min
    # Absolute desired extension rate = current rate + radial relative speed.
    desired = min(0.0, max(-ext_speed_cap, rates.L+radial)) if stroke > 1e-9 and radial < 0 else 0.0
    # Relative speed after a future steady velocity match, not its acceleration transient.
    residual = max(0.0, -(radial+rates.L-desired))
    return ImpactAssessment(speed, max(0.0,-radial), math.sqrt(max(0,speed*speed-radial*radial)),
                            stroke, desired, residual)
