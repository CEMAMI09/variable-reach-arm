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
#define CMD_RESET_LINK 7

#define FLT_NONE          0
#define FLT_ESTOP         (1u << 0)
#define FLT_WATCHDOG      (1u << 1)
#define FLT_HOST_TIMEOUT  (1u << 2)
#define FLT_ENCODER       (1u << 3)
#define FLT_LIMIT         (1u << 4)
#define FLT_OVERCURRENT   (1u << 5)
#define FLT_WORKSPACE     (1u << 6)
#define FLT_PROTOCOL      (1u << 7)
#define FLT_UNQUALIFIED   (1u << 8)
#define FLT_SETPOINT_TIMEOUT (1u << 9)
#define FLT_DRIVER        (1u << 10)
#define PROTOCOL_MAGIC 0x5AA5
#define PROTOCOL_VERSION 2

#pragma pack(push, 1)
typedef struct {
  uint16_t magic;
  uint8_t version;
  uint8_t size;
  uint32_t sequence;
  uint32_t timestamp_us;
  uint8_t  cmd_id;
  uint8_t  flags;
  int32_t  yaw_mdeg;
  int32_t  pitch_mdeg;
  int32_t  extension_mm;
  int32_t  yaw_vel_mdeg_s;
  int32_t  pitch_vel_mdeg_s;
  int32_t  ext_vel_mm_s;
  uint8_t  latch;          /* must be 0: gripper actuation is not qualified */
  uint8_t  reserved[3];
  uint16_t crc16;
} HostCommand;

typedef struct {
  uint16_t magic;
  uint8_t version;
  uint8_t size;
  uint32_t timestamp_us;
  uint8_t  status;
  uint8_t  catch_sensor;
  int32_t  yaw_mdeg;
  int32_t  pitch_mdeg;
  int32_t  extension_mm;
  int32_t  yaw_vel_mdeg_s;
  int32_t  pitch_vel_mdeg_s;
  int32_t  ext_vel_mm_s;
  int32_t  yaw_target_mdeg;
  int32_t  pitch_target_mdeg;
  int32_t  ext_target_mm;
  int32_t  current_yaw_mA;
  int32_t  current_pitch_mA;
  int32_t  current_ext_mA;
  uint16_t fault_bits;
  uint16_t crc16;
} TelemetryFrame;
#pragma pack(pop)
static_assert(sizeof(HostCommand)==44,"host protocol layout mismatch");
static_assert(sizeof(TelemetryFrame)==62,"telemetry layout mismatch");

uint16_t protocol_crc16(const uint8_t *data, uint32_t len);
bool protocol_sequence_newer(uint32_t incoming, uint32_t previous);
uint16_t protocol_validate_command(const HostCommand &command);
class CommandParser {
public:
  bool feed(uint8_t byte, uint32_t now_ms, HostCommand &out);
  uint32_t errors() const { return errors_; }
private:
  uint8_t buffer_[sizeof(HostCommand)] = {};
  unsigned used_ = 0;
  uint32_t last_byte_ms_ = 0, errors_ = 0;
  void discard_one();
};

#endif
