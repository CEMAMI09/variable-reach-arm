#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>

#define CMD_NOP       0
#define CMD_ENABLE    1
#define CMD_DISABLE   2
#define CMD_SETPOINT  3
#define CMD_HOME      4
#define CMD_TRAJ      5
#define CMD_CLEAR_FLT 6

#define FLT_NONE          0
#define FLT_ESTOP         (1u << 0)
#define FLT_WATCHDOG      (1u << 1)
#define FLT_HOST_TIMEOUT  (1u << 2)
#define FLT_ENCODER       (1u << 3)
#define FLT_LIMIT         (1u << 4)
#define FLT_OVERCURRENT   (1u << 5)
#define FLT_WORKSPACE     (1u << 6)

#pragma pack(push, 1)
typedef struct {
  uint32_t timestamp_us;
  uint8_t  cmd_id;
  uint8_t  flags;
  int16_t  yaw_mdeg;
  int16_t  pitch_mdeg;
  int16_t  extension_mm;
  int16_t  yaw_vel_mdeg_s;
  int16_t  pitch_vel_mdeg_s;
  int16_t  ext_vel_mm_s;
  uint8_t  latch;          /* 0 open, 1 closed */
  uint8_t  reserved[11];
  uint16_t crc16;
} HostCommand;

typedef struct {
  uint32_t timestamp_us;
  uint8_t  status;
  uint8_t  catch_sensor;
  int16_t  yaw_mdeg;
  int16_t  pitch_mdeg;
  int16_t  extension_mm;
  int16_t  yaw_vel_mdeg_s;
  int16_t  pitch_vel_mdeg_s;
  int16_t  ext_vel_mm_s;
  int16_t  yaw_target_mdeg;
  int16_t  pitch_target_mdeg;
  int16_t  ext_target_mm;
  int16_t  current_yaw_mA;
  int16_t  current_pitch_mA;
  int16_t  current_ext_mA;
  uint16_t fault_bits;
  uint16_t crc16;
} TelemetryFrame;
#pragma pack(pop)

uint16_t protocol_crc16(const uint8_t *data, uint32_t len);

#endif
