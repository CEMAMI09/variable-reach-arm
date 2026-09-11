#ifndef CONTROL_LOOP_H
#define CONTROL_LOOP_H

#include <stdint.h>

struct AxisState {
  float pos;      /* deg or mm */
  float vel;
  float target;
  float target_vel;
  float current_mA;
  float integral;
  float kp, kd, ki;
  bool target_valid;
  bool measurement_valid;
};

struct JointCommand {
  float yaw_deg;
  float pitch_deg;
  float ext_mm;
  float yaw_vel;
  float pitch_vel;
  float ext_vel;
};

void control_init();
void control_reset();
// Reset invalidates measurements and targets. Future arm logic must first
// acquire fresh timestamped measurements and hand off to a measured hold pose.
void control_set_gains(int axis, float kp, float kd, float ki);
void control_set_targets(const JointCommand &cmd);
void control_update_measurement(int axis, float pos, float vel, float current_mA);
void control_step(float dt);
float control_effort(int axis); /* -1..1 duty or step rate scale */
const AxisState &control_axis(int axis);

#endif
