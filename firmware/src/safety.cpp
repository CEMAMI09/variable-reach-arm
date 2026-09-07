#include "safety.h"

#include "config.h"

#if defined(ARDUINO)
#include <Arduino.h>
#else
static int digitalRead(int) { return 1; }
static uint32_t millis() { return 0; }
#endif

static SafetyStatus g_safety;

void safety_init() {
  g_safety.state = RobotState::Boot;
  g_safety.fault_bits = FLT_NONE;
  g_safety.estop_pressed = false;
  g_safety.last_host_ms = 0;
  g_safety.last_loop_ms = 0;
  g_safety.state = RobotState::Disabled;
}

void safety_raise(uint16_t bits) {
  g_safety.fault_bits |= bits;
  g_safety.state = RobotState::Fault;
}

void safety_note_host(uint32_t now_ms) { g_safety.last_host_ms = now_ms; }

void safety_tick(uint32_t now_ms) {
  g_safety.last_loop_ms = now_ms;
  g_safety.estop_pressed = (digitalRead(PIN_ESTOP_SENSE) == 0);

  if (g_safety.estop_pressed) {
    safety_raise(FLT_ESTOP);
    return;
  }

  if (g_safety.state == RobotState::Active || g_safety.state == RobotState::Idle) {
    if (g_safety.last_host_ms > 0 &&
        (now_ms - g_safety.last_host_ms) > HOST_TIMEOUT_MS) {
      safety_raise(FLT_HOST_TIMEOUT);
    }
  }
}

void safety_clear_if_safe() {
  if (g_safety.estop_pressed)
    return;
  g_safety.fault_bits = FLT_NONE;
  g_safety.state = RobotState::Disabled;
}

RobotState safety_state() { return g_safety.state; }
uint16_t safety_faults() { return g_safety.fault_bits; }

bool safety_motion_allowed() {
  return g_safety.state == RobotState::Idle || g_safety.state == RobotState::Active;
}
