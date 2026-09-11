# Embedded verification

From repository root:

```sh
g++ -std=c++17 -Wall -Wextra -Werror -I firmware/include firmware/tests/test_native.cpp firmware/src/command_receiver.cpp firmware/src/protocol.cpp firmware/src/safety.cpp firmware/src/control_loop.cpp firmware/src/motors.cpp -o vra_native_tests
./vra_native_tests
VRA_NATIVE_TEST_BINARY=./vra_native_tests python -m unittest discover -s firmware/tests -v
python -m platformio run -d firmware
```

On Windows, set VRA_NATIVE_TEST_BINARY to the absolute .exe path using a process
environment variable. Zig's C++ frontend can replace g++ if necessary. Tests cover
the standard CRC check vector, 32-bit angular range, invalid values, unsupported
claw/home/trajectory commands, sequence wrap/replay, corrupt/dropped/truncated frame
recovery, qualification lock, missing feedback and anti-windup. The optional
cross-language test compares exact C++ command bytes with Python and decodes C++
telemetry; it must run before a protocol change is accepted.

The production CommandReceiver shared with main.cpp is exercised in actual byte
receive/dispatch order: boot, enable, clear, unsupported HOME/TRAJ/claw, invalid
range/flags/CRC, old-sequence disable, reset-link, duplicate/stale/new sequence,
wraparound, truncated/dropped-frame recovery and reboot. Read-only safety snapshots
verify invalid or replayed traffic does not refresh host-arrival health. No test
replaces the safety implementation or adds an enable bypass.

Controller reset clears and invalidates targets and measured state. Tests verify
that a new measurement alone cannot revive the old target. The future measured-pose
handoff still requires timestamped feedback and an explicit, qualified arm transition;
this release supplies neither.

No tests invoke a serial port or flash a board. No test bypasses FLT_UNQUALIFIED.
Host/native tests cannot exercise real driver shutdown, encoder loss timing, current
trips, homing, independent watchdog or brake behavior because those adapters do not
exist. Follow docs/safety.md before any powered axis testing.

A Teensy compile checks target syntax/linking, not measured 1 kHz timing, electrical
safety or real motion performance.
