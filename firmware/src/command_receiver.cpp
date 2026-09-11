#include "command_receiver.h"
#include "control_loop.h"
#include "motors.h"
#include "safety.h"

void CommandReceiver::feed(uint8_t byte, uint32_t now_ms) {
  const uint32_t old_errors = parser_.errors();
  HostCommand command;
  const bool complete = parser_.feed(byte, now_ms, command);
  if (parser_.errors() != old_errors) {
    safety_raise(FLT_PROTOCOL);
    motors_disable_all();
    control_reset();
  }
  if (complete) handle(command, now_ms);
}

void CommandReceiver::handle(const HostCommand &c, uint32_t now_ms) {
  const uint16_t invalid = protocol_validate_command(c);
  if (invalid) {
    safety_raise(invalid);
    motors_disable_all();
    control_reset();
    return;
  }
  // An old but otherwise valid disable still disarms. It cannot refresh health.
  if (c.cmd_id == CMD_DISABLE) {
    safety_disable();
    motors_disable_all();
    control_reset();
    return;
  }
  if (c.cmd_id == CMD_RESET_LINK) {
    // This is a sequence reset while disabled, not an arm or fault-clear.
    if (safety_motion_allowed()) {
      safety_raise(FLT_PROTOCOL);
      motors_disable_all();
      control_reset();
      return;
    }
    last_sequence_ = c.sequence;
    have_sequence_ = true;
    control_reset();
    return;
  }
  if (have_sequence_ && !protocol_sequence_newer(c.sequence, last_sequence_)) return;
  last_sequence_ = c.sequence;
  have_sequence_ = true;
  // CRC and semantic validity precede freshness. Invalid and replayed traffic
  // never moves this timestamp; unsupported HOME/TRAJ/claw fields cannot hide loss.
  safety_note_host(now_ms);
  switch (c.cmd_id) {
  case CMD_CLEAR_FLT:
    safety_clear_if_safe();
    control_reset();
    break;
  case CMD_ENABLE:
    safety_raise(FLT_UNQUALIFIED);
    control_reset();
    break;
  case CMD_SETPOINT:
    // Disabled commands are discarded, not stored for a later enable.
    if (!safety_motion_allowed()) break;
    control_set_targets({c.yaw_mdeg/1000.f, c.pitch_mdeg/1000.f, float(c.extension_mm),
      c.yaw_vel_mdeg_s/1000.f, c.pitch_vel_mdeg_s/1000.f, float(c.ext_vel_mm_s)});
    safety_note_setpoint(now_ms);
    break;
  default:
    break;
  }
}
