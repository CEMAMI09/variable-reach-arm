# Embedded protocol v2 and implementation boundary

This document supersedes the v1 protocol section in the original architecture
document. Both endpoints must be updated together. V1 has no compatibility fallback:
its signed 16-bit millidegrees cannot represent the required ±70 degree travel.

## Wire format

Little-endian, signed two's-complement 32-bit motion/current fields, packed without
padding. Supported targets are Teensy 4.1 and little-endian native test hosts.
`protocol.h` compile-time size assertions and the Python/C++ cross-language test
check the exact layout. USB CDC is configured at 921600; the host is not a hard
real-time scheduler.

Command is **44 bytes**, Python struct `<HBBIIBB6iB3sH`:

- Bytes 0–1: magic 0x5AA5 (wire A5 5A).
- Byte 2: version 2; byte 3: total size 44.
- Bytes 4–7: unsigned sequence; bytes 8–11: host monotonic timestamp microseconds.
- Byte 12: command ID; byte 13: flags, must be zero.
- Bytes 14–37: six signed int32 values: yaw mdeg, pitch mdeg, extension stroke mm,
  yaw mdeg/s, pitch mdeg/s, extension mm/s.
- Byte 38: legacy latch field, must be zero; bytes 39–41: reserved, must be zero.
- Bytes 42–43: CRC16/MODBUS of bytes 0–41, initial 0xFFFF, reflected polynomial
  0xA001, no final XOR. Check vector ASCII 123456789 gives 0x4B37.

Telemetry is **62 bytes**, Python struct `<HBBIBB12iHH`:

- Bytes 0–3: identical header except total size 62.
- Bytes 4–7: MCU microseconds since boot (wraps approximately every 71.6 minutes).
- Byte 8: state (Boot=0, SelfTest=1, Disabled=2, Idle=3, Active=4, Fault=5).
- Byte 9: capture sensor 0/1, or 255 when unavailable.
- Bytes 10–57: signed int32 triples of measured position, measured velocity,
  commanded target, measured current mA; angular units remain mdeg.
- Bytes 58–59: fault bits; bytes 60–61: CRC over bytes 0–59.
- INT32_MIN is **missing**, never zero. Python converts it to None. Targets are
  setpoints only and are never evidence of measured motion.

## Commands and freshness

NOP=0, ENABLE=1, DISABLE=2, SETPOINT=3, HOME=4, TRAJ=5, CLEAR_FAULT=6,
RESET_LINK=7. Non-setpoint commands require all motion fields zero.
HOME and TRAJ return an unqualified fault; no motion adapter exists. Nonzero claw
actuation is rejected rather than controlling a servo without feedback.

ENABLE always leaves the qualification fault asserted. DISABLE is accepted with
any sequence after CRC/semantic validation and preserves real faults. RESET_LINK
resets the receive sequence baseline only when motion is disarmed; it cannot clear
faults or arm. The host connection sends DISABLE followed by RESET_LINK.

Normal sequence acceptance is `0 < (new-old) mod 2^32 < 2^31`; duplicates, backward
and half-range-ambiguous packets do not refresh freshness. CRC/header/semantic
validation precedes freshness refresh. No outgoing command retry or background
heartbeat silently keeps an old trajectory running.

Current timeouts: inter-byte 20 ms, loop-overrun diagnostic 2 ms, host traffic 200 ms,
setpoint stream 50 ms. The parser reads at most 128 serial bytes per scheduled cycle,
uses a fixed 44-byte buffer, and resynchronizes after corruption, insertions and
dropped bytes. Telemetry is best-effort at 100 Hz and skips transmission if the USB
buffer lacks space. The host bounds a poll to 4096 bytes and rejects stale, faulty,
inactive or missing-feedback telemetry before a setpoint write.

The host timestamp is diagnostic only: clocks have no synchronization contract.
MCU arrivals use local time. A CRC is error detection, not authentication. RESET_LINK
does not establish cryptographic replay protection or a new boot identity. Before
an enabled production protocol exists, add a board-generated boot/session challenge,
command acknowledgement and scheduled-execution/deadline semantics; queued USB
traffic and stale sequences must then be tested across every reset/reconnect case.

## Implemented versus absent

Implemented: version/range/CRC/framing validation; rollover-safe sequence comparison;
bounded parsing; valid-arrival freshness bookkeeping; missing-measurement decoding;
persistent qualification lock; NC switch diagnostics; no automatic arm or retry;
zero untuned controller gains; finite checks, reset and conditional anti-windup.

Absent: step/dir or vendor serial motor adapters, real joint feedback and age checking,
current measurement/thresholds, homing, hardware watchdog setup, qualified gain
scheduling/feedforward, acceleration/jerk execution, stopping envelope, brake timing,
joint output position supervision, capture feedback and three-finger claw actuation.
The target scheduler is a cooperative 1 kHz diagnostic loop, not measured deterministic
closed-loop control. Do not connect a loaded robot on the strength of software tests.

Firmware commissioning cap is 20 degrees/s yaw/pitch, 150 mm/s extension. The
host packer matches it; higher simulation requirements cannot be sent to hardware.
Extension is **stroke**, not total reach: L = 0.700 + extension_mm/1000 meters.
