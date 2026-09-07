#ifndef MOTORS_H
#define MOTORS_H

void motors_init();
void motors_set_effort(int axis, float effort_minus1_to_1);
void motors_disable_all();
void motors_read_state(int axis, float *pos, float *vel, float *current_mA);

#endif
