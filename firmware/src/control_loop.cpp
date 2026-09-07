#include "control_loop.h"

#include "config.h"

static AxisState axes[NUM_AXES];

void control_init() {
  for (int i = 0; i < NUM_AXES; i++) {
    axes[i] = {};
    /* Conservative PD defaults — schedule vs L later */
    axes[i].kp = (i == AXIS_EXT) ? 8.0f : 12.0f;
    axes[i].kd = (i == AXIS_EXT) ? 0.4f : 0.8f;
    axes[i].ki = 0.0f;
  }
}

void control_set_gains(int axis, float kp, float kd, float ki) {
  if (axis < 0 || axis >= NUM_AXES)
    return;
  axes[axis].kp = kp;
  axes[axis].kd = kd;
  axes[axis].ki = ki;
}

void control_set_targets(const JointCommand &cmd) {
  axes[AXIS_YAW].target = cmd.yaw_deg;
  axes[AXIS_PITCH].target = cmd.pitch_deg;
  axes[AXIS_EXT].target = cmd.ext_mm;
  axes[AXIS_YAW].target_vel = cmd.yaw_vel;
  axes[AXIS_PITCH].target_vel = cmd.pitch_vel;
  axes[AXIS_EXT].target_vel = cmd.ext_vel;
}

void control_update_measurement(int axis, float pos, float vel, float current_mA) {
  if (axis < 0 || axis >= NUM_AXES)
    return;
  axes[axis].pos = pos;
  axes[axis].vel = vel;
  axes[axis].current_mA = current_mA;
}

void control_step(float dt) {
  for (int i = 0; i < NUM_AXES; i++) {
    float e = axes[i].target - axes[i].pos;
    axes[i].integral += e * dt;
    /* Effort stored in unused target_vel field shadow via ki path — see control_effort */
    (void)e;
  }
}

float control_effort(int axis) {
  if (axis < 0 || axis >= NUM_AXES)
    return 0.f;
  const AxisState &a = axes[axis];
  float e = a.target - a.pos;
  float de = a.target_vel - a.vel;
  float u = a.kp * e + a.kd * de + a.ki * a.integral;
  if (u > 1.f)
    u = 1.f;
  if (u < -1.f)
    u = -1.f;
  return u;
}

const AxisState &control_axis(int axis) { return axes[axis]; }
