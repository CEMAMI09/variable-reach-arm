#ifndef COMMAND_RECEIVER_H
#define COMMAND_RECEIVER_H
#include "protocol.h"

// The production serial receive/dispatch path. Tests inject bytes here without
// replacing safety, motor or controller behavior, and never remove the lock.
class CommandReceiver {
public:
  void feed(uint8_t byte, uint32_t now_ms);
private:
  CommandParser parser_;
  bool have_sequence_ = false;
  uint32_t last_sequence_ = 0;
  void handle(const HostCommand &command, uint32_t now_ms);
};
#endif
