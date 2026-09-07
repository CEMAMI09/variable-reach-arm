# Firmware unit-test notes

Host-side smoke:

```bash
g++ -std=c++17 -I firmware/include -o /tmp/vra_fw_smoke \
  firmware/src/main.cpp firmware/src/protocol.cpp \
  firmware/src/safety.cpp firmware/src/control_loop.cpp
/tmp/vra_fw_smoke
```

On-target: PlatformIO `teensy41` env in `firmware/platformio.ini`.
Wire motor adapters in `motors.cpp` before enabling `ACTIVE` state.
