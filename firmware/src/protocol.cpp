#include "protocol.h"

uint16_t protocol_crc16(const uint8_t *data, uint32_t len) {
  uint16_t crc = 0xFFFF;
  for (uint32_t i = 0; i < len; i++) {
    crc ^= data[i];
    for (int b = 0; b < 8; b++) {
      if (crc & 1)
        crc = (crc >> 1) ^ 0xA001;
      else
        crc >>= 1;
    }
  }
  return crc;
}

#include "config.h"
#include <string.h>

bool protocol_sequence_newer(uint32_t incoming, uint32_t previous) {
  const uint32_t difference = incoming - previous;
  return difference != 0 && difference < 0x80000000u;
}

uint16_t protocol_validate_command(const HostCommand &c) {
  if (c.magic != PROTOCOL_MAGIC || c.version != PROTOCOL_VERSION ||
      c.size != sizeof(c) || c.crc16 != protocol_crc16(
        reinterpret_cast<const uint8_t *>(&c), sizeof(c)-2))
    return FLT_PROTOCOL;
  if (c.cmd_id > CMD_RESET_LINK || c.flags || c.latch ||
      c.reserved[0] || c.reserved[1] || c.reserved[2])
    return FLT_PROTOCOL;
  // HOME, TRAJ and claw actuation need real feedback, actuator adapters and tests.
  if (c.cmd_id == CMD_HOME || c.cmd_id == CMD_TRAJ) return FLT_UNQUALIFIED;
  if (c.cmd_id != CMD_SETPOINT) {
    if (c.yaw_mdeg || c.pitch_mdeg || c.extension_mm ||
        c.yaw_vel_mdeg_s || c.pitch_vel_mdeg_s || c.ext_vel_mm_s)
      return FLT_PROTOCOL;
    return FLT_NONE;
  }
  if (c.yaw_mdeg < YAW_MIN_MDEG || c.yaw_mdeg > YAW_MAX_MDEG ||
      c.pitch_mdeg < PITCH_MIN_MDEG || c.pitch_mdeg > PITCH_MAX_MDEG ||
      c.extension_mm < EXT_MIN_MM || c.extension_mm > EXT_MAX_MM ||
      c.yaw_vel_mdeg_s < -YAW_VEL_CAP_MDEG_S || c.yaw_vel_mdeg_s > YAW_VEL_CAP_MDEG_S ||
      c.pitch_vel_mdeg_s < -PITCH_VEL_CAP_MDEG_S || c.pitch_vel_mdeg_s > PITCH_VEL_CAP_MDEG_S ||
      c.ext_vel_mm_s < -EXT_VEL_CAP_MM_S || c.ext_vel_mm_s > EXT_VEL_CAP_MM_S)
    return FLT_WORKSPACE;
  return FLT_NONE;
}

void CommandParser::discard_one() {
  if (used_) { --used_; memmove(buffer_, buffer_+1, used_); }
}

bool CommandParser::feed(uint8_t byte, uint32_t now_ms, HostCommand &out) {
  if (used_ && uint32_t(now_ms-last_byte_ms_) > FRAME_TIMEOUT_MS) {
    used_ = 0;
    ++errors_;
  }
  last_byte_ms_ = now_ms;
  buffer_[used_++] = byte;
  while (used_) {
    if (buffer_[0] != uint8_t(PROTOCOL_MAGIC)) { discard_one(); continue; }
    if (used_ < 2) return false;
    if (buffer_[1] != uint8_t(PROTOCOL_MAGIC >> 8)) { discard_one(); continue; }
    if (used_ < 4) return false;
    if (buffer_[2] != PROTOCOL_VERSION || buffer_[3] != sizeof(HostCommand)) {
      ++errors_; discard_one(); continue;
    }
    if (used_ < sizeof(HostCommand)) return false;
    HostCommand candidate;
    memcpy(&candidate, buffer_, sizeof(candidate));
    if (candidate.crc16 != protocol_crc16(buffer_, sizeof(candidate)-2)) {
      ++errors_; discard_one(); continue;
    }
    out = candidate;
    used_ = 0;
    return true;
  }
  return false;
}
