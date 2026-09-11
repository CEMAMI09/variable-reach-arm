#ifndef SAFETY_H
#define SAFETY_H

#include <stdint.h>

#include "protocol.h"

enum class RobotState : uint8_t {
  Boot = 0,
  SelfTest,
  Disabled,
  Idle,
  Active,
  Fault
};

struct SafetyStatus {
  RobotState state;
  uint16_t fault_bits;
  bool estop_pressed;
  uint32_t last_host_ms;
  uint32_t last_loop_ms;
  uint32_t last_setpoint_ms;
  bool have_host;
};

void safety_init();
struct SafetyInputs {
  bool estop_open = true;
  bool home_open = true;
  bool max_open = true;
  bool feedback_valid = false;
  bool current_valid = false;
  bool current_fault = false;
  bool driver_fault = false;
};
void safety_tick(uint32_t now_ms, const SafetyInputs &inputs);
void safety_note_setpoint(uint32_t now_ms);
void safety_disable();
void safety_note_host(uint32_t now_ms);
void safety_raise(uint16_t bits);
void safety_clear_if_safe();
RobotState safety_state();
uint16_t safety_faults();
bool safety_motion_allowed();
SafetyStatus safety_status(); // read-only diagnostic snapshot; no state mutation API

#endif
