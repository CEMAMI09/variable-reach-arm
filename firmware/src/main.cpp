/**
 * Variable-reach arm firmware — Teensy 4.1 / Arduino-compatible entry.
 *
 * Control development order (do not skip):
 * 1 manual low-speed  2 homing  3 position  4 velocity
 * 5 accel limits  6 multi-axis  7 traj tracking  8 dynamic extension
 */

#include "config.h"
#include "control_loop.h"
#include "protocol.h"
#include "safety.h"

#include <string.h>

#if defined(ARDUINO)
#include <Arduino.h>
#else
/* Host-side compile smoke test stubs */
#include <stdio.h>
#define SERIAL_PORT_USBVIRTUAL
struct FakeSerial {
  void begin(int) {}
  int available() { return 0; }
  int readBytes(char *, int) { return 0; }
  size_t write(const uint8_t *, size_t n) { return n; }
} Serial;
void pinMode(int, int) {}
#define INPUT_PULLUP 2
#define OUTPUT 1
unsigned long micros() { return 0; }
unsigned long millis() { return 0; }
void delay(int) {}
#endif

static HostCommand rx_cmd;
static TelemetryFrame tx_tlm;
static JointCommand joint_cmd;
static uint8_t rx_buf[sizeof(HostCommand)];
static unsigned rx_len = 0;

static void apply_limits(JointCommand &c) {
  if (c.yaw_deg < YAW_MIN_MDEG / 1000.0f)
    c.yaw_deg = YAW_MIN_MDEG / 1000.0f;
  if (c.yaw_deg > YAW_MAX_MDEG / 1000.0f)
    c.yaw_deg = YAW_MAX_MDEG / 1000.0f;
  if (c.pitch_deg < PITCH_MIN_MDEG / 1000.0f)
    c.pitch_deg = PITCH_MIN_MDEG / 1000.0f;
  if (c.pitch_deg > PITCH_MAX_MDEG / 1000.0f)
    c.pitch_deg = PITCH_MAX_MDEG / 1000.0f;
  if (c.ext_mm < EXT_MIN_MM)
    c.ext_mm = EXT_MIN_MM;
  if (c.ext_mm > EXT_MAX_MM)
    c.ext_mm = EXT_MAX_MM;
}

static void handle_command(const HostCommand &c, uint32_t now_ms) {
  safety_note_host(now_ms);
  uint16_t crc = protocol_crc16(reinterpret_cast<const uint8_t *>(&c),
                                sizeof(HostCommand) - 2);
  if (crc != c.crc16) {
    safety_raise(FLT_ENCODER); /* reuse bit: treat as protocol/encoder class fault log */
    return;
  }

  switch (c.cmd_id) {
  case CMD_ENABLE:
    if (safety_faults() == FLT_NONE) {
      /* transition handled externally when wiring drivers */
    }
    break;
  case CMD_DISABLE:
    break;
  case CMD_CLEAR_FLT:
    safety_clear_if_safe();
    break;
  case CMD_HOME:
    /* Extension slow seek toward PIN_EXT_HOME — implement with driver layer */
    break;
  case CMD_SETPOINT:
  case CMD_TRAJ:
    joint_cmd.yaw_deg = c.yaw_mdeg / 1000.0f;
    joint_cmd.pitch_deg = c.pitch_mdeg / 1000.0f;
    joint_cmd.ext_mm = c.extension_mm;
    joint_cmd.yaw_vel = c.yaw_vel_mdeg_s / 1000.0f;
    joint_cmd.pitch_vel = c.pitch_vel_mdeg_s / 1000.0f;
    joint_cmd.ext_vel = c.ext_vel_mm_s;
    apply_limits(joint_cmd);
    if (safety_motion_allowed())
      control_set_targets(joint_cmd);
    break;
  default:
    break;
  }
}

static void publish_telemetry(uint32_t now_us) {
  tx_tlm.timestamp_us = now_us;
  tx_tlm.status = static_cast<uint8_t>(safety_state());
  tx_tlm.catch_sensor = 0;
  tx_tlm.yaw_mdeg = static_cast<int16_t>(control_axis(AXIS_YAW).pos * 1000);
  tx_tlm.pitch_mdeg = static_cast<int16_t>(control_axis(AXIS_PITCH).pos * 1000);
  tx_tlm.extension_mm = static_cast<int16_t>(control_axis(AXIS_EXT).pos);
  tx_tlm.yaw_vel_mdeg_s = static_cast<int16_t>(control_axis(AXIS_YAW).vel * 1000);
  tx_tlm.pitch_vel_mdeg_s = static_cast<int16_t>(control_axis(AXIS_PITCH).vel * 1000);
  tx_tlm.ext_vel_mm_s = static_cast<int16_t>(control_axis(AXIS_EXT).vel);
  tx_tlm.yaw_target_mdeg = static_cast<int16_t>(control_axis(AXIS_YAW).target * 1000);
  tx_tlm.pitch_target_mdeg = static_cast<int16_t>(control_axis(AXIS_PITCH).target * 1000);
  tx_tlm.ext_target_mm = static_cast<int16_t>(control_axis(AXIS_EXT).target);
  tx_tlm.current_yaw_mA = static_cast<int16_t>(control_axis(AXIS_YAW).current_mA);
  tx_tlm.current_pitch_mA = static_cast<int16_t>(control_axis(AXIS_PITCH).current_mA);
  tx_tlm.current_ext_mA = static_cast<int16_t>(control_axis(AXIS_EXT).current_mA);
  tx_tlm.fault_bits = safety_faults();
  tx_tlm.crc16 = protocol_crc16(reinterpret_cast<const uint8_t *>(&tx_tlm),
                                sizeof(TelemetryFrame) - 2);
  Serial.write(reinterpret_cast<const uint8_t *>(&tx_tlm), sizeof(tx_tlm));
}

void setup() {
  Serial.begin(921600);
  pinMode(PIN_ESTOP_SENSE, INPUT_PULLUP);
  pinMode(PIN_EXT_HOME, INPUT_PULLUP);
  pinMode(PIN_EXT_MAX, INPUT_PULLUP);
  pinMode(PIN_CATCH_SENSOR, INPUT_PULLUP);
  pinMode(PIN_LATCH_SERVO, OUTPUT);
  safety_init();
  control_init();
}

void loop() {
  static uint32_t last_us = 0;
  uint32_t now_us = micros();
  uint32_t now_ms = millis();
  float dt = (last_us == 0) ? (1.0f / CONTROL_HZ) : (now_us - last_us) * 1e-6f;
  last_us = now_us;

  while (Serial.available() > 0 && rx_len < sizeof(rx_buf)) {
    int n = Serial.readBytes(reinterpret_cast<char *>(rx_buf + rx_len),
                             sizeof(rx_buf) - rx_len);
    if (n <= 0)
      break;
    rx_len += static_cast<unsigned>(n);
  }
  if (rx_len >= sizeof(HostCommand)) {
    memcpy(&rx_cmd, rx_buf, sizeof(HostCommand));
    handle_command(rx_cmd, now_ms);
    rx_len = 0;
  }

  safety_tick(now_ms);

  /* TODO: read encoders into control_update_measurement(...) */
  if (safety_motion_allowed())
    control_step(dt);
  /* TODO: write control_effort(i) to drivers */

  static uint32_t last_tlm_ms = 0;
  if (now_ms - last_tlm_ms >= 10) {
    last_tlm_ms = now_ms;
    publish_telemetry(now_us);
  }
}

#ifndef ARDUINO
int main() {
  setup();
  for (int i = 0; i < 3; i++)
    loop();
  printf("firmware smoke ok\n");
  return 0;
}
#endif
