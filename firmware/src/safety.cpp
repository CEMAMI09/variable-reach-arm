#include "safety.h"
#include "config.h"

static SafetyStatus status;
static SafetyInputs inputs;

void safety_init() {
  status = {};
  inputs = {};
  // Permanent qualification lock: there are no real drivers, homing, feedback,
  // gripper control, measured current limits or independent watchdog adapters.
  status.state = RobotState::Fault;
  status.fault_bits = FLT_UNQUALIFIED;
  status.estop_pressed = true;
}
void safety_raise(uint16_t bits) {
  status.fault_bits |= bits;
  status.state = RobotState::Fault;
}
void safety_disable() {
  // A requested disable is not a protocol error. Existing faults stay latched.
  status.state = status.fault_bits ? RobotState::Fault : RobotState::Disabled;
}
void safety_note_host(uint32_t now_ms) {
  status.last_host_ms = now_ms;
  status.have_host = true;
}
void safety_note_setpoint(uint32_t now_ms) { status.last_setpoint_ms = now_ms; }
void safety_tick(uint32_t now_ms, const SafetyInputs &next) {
  inputs = next;
  status.last_loop_ms = now_ms;
  status.estop_pressed = inputs.estop_open;
  if (inputs.estop_open) safety_raise(FLT_ESTOP);
  if (inputs.home_open && inputs.max_open) safety_raise(FLT_LIMIT);
  if (!safety_motion_allowed()) return;
  if (inputs.home_open || inputs.max_open) safety_raise(FLT_LIMIT);
  if (!inputs.feedback_valid) safety_raise(FLT_ENCODER);
  if (!inputs.current_valid || inputs.current_fault) safety_raise(FLT_OVERCURRENT);
  if (inputs.driver_fault) safety_raise(FLT_DRIVER);
  if (!status.have_host || uint32_t(now_ms-status.last_host_ms) >= HOST_TIMEOUT_MS)
    safety_raise(FLT_HOST_TIMEOUT);
  if (uint32_t(now_ms-status.last_setpoint_ms) >= SETPOINT_TIMEOUT_MS)
    safety_raise(FLT_SETPOINT_TIMEOUT);
}
void safety_clear_if_safe() {
  if (status.fault_bits & FLT_UNQUALIFIED) return;
  if (inputs.estop_open || inputs.home_open || inputs.max_open ||
      !inputs.feedback_valid || !inputs.current_valid ||
      inputs.current_fault || inputs.driver_fault) return;
  status.fault_bits = FLT_NONE;
  status.state = RobotState::Disabled;
  status.have_host = false;
}
RobotState safety_state() { return status.state; }
uint16_t safety_faults() { return status.fault_bits; }
SafetyStatus safety_status() { return status; }
bool safety_motion_allowed() {
  return status.fault_bits == FLT_NONE &&
    (status.state == RobotState::Idle || status.state == RobotState::Active);
}
