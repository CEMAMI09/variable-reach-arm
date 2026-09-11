/**
 * Qualification firmware: protocol and safety diagnostics ONLY.
 * No command can enable motion until tested hardware adapters replace the lock.
 * Build may be flashed on a logic-only bench by a human; this is not motion firmware.
 */
#include "config.h"
#include "control_loop.h"
#include "protocol.h"
#include "command_receiver.h"
#include "safety.h"
#include "motors.h"
#include <string.h>
#if defined(ARDUINO)
#include <Arduino.h>
#else
#include <stdio.h>
struct FakeSerial {
  void begin(int) {}
  int available() { return 0; }
  int read() { return -1; }
  int availableForWrite() { return 128; }
  size_t write(const uint8_t *, size_t n) { return n; }
} Serial;
void pinMode(int, int) {}
int digitalRead(int) { return 1; }
#define INPUT_PULLUP 2
#define OUTPUT 1
unsigned long micros() { static uint32_t t=0; t+=1000; return t; }
unsigned long millis() { return micros()/1000; }
#endif

static CommandReceiver receiver;

static void publish_telemetry(uint32_t now_us) {
  TelemetryFrame t={};
  t.magic=PROTOCOL_MAGIC;t.version=PROTOCOL_VERSION;t.size=sizeof(t);
  t.timestamp_us=now_us;t.status=uint8_t(safety_state());
  t.catch_sensor=255; // unavailable until actual three-finger claw capture sensing exists
  t.yaw_mdeg=t.pitch_mdeg=t.extension_mm=INT32_MIN;
  t.yaw_vel_mdeg_s=t.pitch_vel_mdeg_s=t.ext_vel_mm_s=INT32_MIN;
  t.yaw_target_mdeg=control_axis(AXIS_YAW).target_valid ?
    int32_t(control_axis(AXIS_YAW).target*1000) : INT32_MIN;
  t.pitch_target_mdeg=control_axis(AXIS_PITCH).target_valid ?
    int32_t(control_axis(AXIS_PITCH).target*1000) : INT32_MIN;
  t.ext_target_mm=control_axis(AXIS_EXT).target_valid ?
    int32_t(control_axis(AXIS_EXT).target) : INT32_MIN;
  t.current_yaw_mA=t.current_pitch_mA=t.current_ext_mA=INT32_MIN;
  t.fault_bits=safety_faults();
  t.crc16=protocol_crc16(reinterpret_cast<const uint8_t*>(&t),sizeof(t)-2);
  Serial.write(reinterpret_cast<const uint8_t*>(&t),sizeof(t));
}

void setup() {
  motors_init();motors_disable_all(); // adapter stays unqualified; no imaginary output pins
  pinMode(PIN_ESTOP_SENSE,INPUT_PULLUP);
  pinMode(PIN_EXT_HOME,INPUT_PULLUP);
  pinMode(PIN_EXT_MAX,INPUT_PULLUP);
  pinMode(PIN_CATCH_SENSOR,INPUT_PULLUP);
  // Latch pin intentionally not configured: there is no qualified gripper adapter.
  safety_init();control_init();Serial.begin(921600);
}

void loop() {
  static bool started=false;
  static uint32_t last_us=0,last_tlm_ms=0;
  const uint32_t now_us=micros(),now_ms=millis();
  const uint32_t elapsed=now_us-last_us;
  if(started && elapsed<1000000u/CONTROL_HZ)return;
  if(started && elapsed>WATCHDOG_MS*1000u)safety_raise(FLT_WATCHDOG);
  started=true;last_us=now_us;
  // No catch-up burst after an overrun. Actual WCET/jitter still needs on-target measurement.
  SafetyInputs input;
  input.estop_open=digitalRead(PIN_ESTOP_SENSE)!=0;
  input.home_open=digitalRead(PIN_EXT_HOME)!=0;
  input.max_open=digitalRead(PIN_EXT_MAX)!=0;
  safety_tick(now_ms,input);
  for(unsigned budget=0;budget<128 && Serial.available()>0;++budget) {
    const int byte=Serial.read();
    if(byte<0)break;
    receiver.feed(uint8_t(byte),now_ms);
  }
  if(!safety_motion_allowed()) { motors_disable_all(); control_reset(); }
  // NO step generator, effort output, driver polling or gripper actuation is implemented.
  if(uint32_t(now_ms-last_tlm_ms)>=10 &&
      Serial.availableForWrite()>=int(sizeof(TelemetryFrame))) {
    last_tlm_ms=now_ms;publish_telemetry(now_us);
  }
}
#ifndef ARDUINO
int main(){setup();for(int i=0;i<3;++i)loop();printf("qualification firmware smoke ok; motion locked\n");return safety_motion_allowed()?1:0;}
#endif
