#include "motors.h"

#include "config.h"
#include <math.h>

/* Driver adapters for MKS SERVO42/57 (UART or STEP/DIR) — fill during bring-up. */

void motors_init() {}

void motors_set_effort(int axis, float effort_minus1_to_1) {
  (void)axis;
  (void)effort_minus1_to_1;
}

void motors_disable_all() {}

void motors_read_state(int axis, float *pos, float *vel, float *current_mA) {
  (void)axis;
  if (pos)
    *pos = NAN;
  if (vel)
    *vel = NAN;
  if (current_mA)
    *current_mA = NAN;
}
