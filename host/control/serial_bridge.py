"""Version 2 serial codec and fail-closed host interface.

Wire angles are signed int32 millidegrees; extension is millimeters of stroke.
This is a commissioning interface, not a hardware-qualified trajectory executor.
"""
from __future__ import annotations

import math
import struct
import time
from dataclasses import dataclass
from enum import IntEnum

MAGIC = 0x5AA5
VERSION = 2
COMMAND = struct.Struct("<HBBIIBB6iB3sH")
TELEMETRY = struct.Struct("<HBBIBB12iHH")
INVALID = -(1 << 31)
MAX_TELEMETRY_AGE_S = 0.100
FRAME_TIMEOUT_S = 0.020
assert COMMAND.size == 44 and TELEMETRY.size == 62


class CommandId(IntEnum):
    NOP = 0
    ENABLE = 1
    DISABLE = 2
    SETPOINT = 3
    HOME = 4
    TRAJ = 5
    CLEAR_FAULT = 6
    RESET_LINK = 7


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if crc & 1 else crc >> 1
    return crc & 0xFFFF


def sequence_newer(incoming: int, previous: int) -> bool:
    return 0 < ((incoming - previous) & 0xFFFFFFFF) < 0x80000000


@dataclass(frozen=True)
class Setpoint:
    yaw_deg: float
    pitch_deg: float
    ext_mm: float
    yaw_vel: float = 0.0
    pitch_vel: float = 0.0
    ext_vel: float = 0.0
    latch: int = 0


def _u32(value: int, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 0xFFFFFFFF:
        raise ValueError(f"{name} must be a uint32")
    return value


def pack_setpoint(
    sp: Setpoint, timestamp_us: int = 0, cmd_id: int = CommandId.SETPOINT,
    *, sequence: int = 0,
) -> bytes:
    """Encode v2; reject unsupported claw/home/trajectory actions and bad units."""
    command_id = CommandId(cmd_id)
    if command_id in (CommandId.HOME, CommandId.TRAJ):
        raise ValueError("Homing/trajectory adapters are not qualified")
    if sp.latch != 0:
        raise ValueError("Three-finger claw actuation requires a qualified adapter")
    values = (sp.yaw_deg, sp.pitch_deg, sp.ext_mm, sp.yaw_vel, sp.pitch_vel, sp.ext_vel)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("Setpoint must contain finite values")
    # Match config.h commissioning caps; performance simulation may use a separate envelope.
    lower = (-70.0, -15.0, 0.0, -20.0, -20.0, -150.0)
    upper = (70.0, 70.0, 500.0, 20.0, 20.0, 150.0)
    if any(not low <= value <= high for value, low, high in zip(values, lower, upper)):
        raise ValueError("Command exceeds the unqualified commissioning envelope")
    if command_id != CommandId.SETPOINT and any(values):
        raise ValueError("Non-setpoint commands must have zero motion fields")
    units = (1000, 1000, 1, 1000, 1000, 1)
    quantized = [round(value * scale) for value, scale in zip(values, units)]
    raw = COMMAND.pack(
        MAGIC, VERSION, COMMAND.size, _u32(sequence, "sequence"),
        _u32(timestamp_us, "timestamp_us"), command_id, 0, *quantized,
        0, bytes(3), 0,
    )
    return raw[:-2] + struct.pack("<H", crc16(raw[:-2]))


def pack_command(command: CommandId, *, sequence: int, timestamp_us: int = 0) -> bytes:
    if command == CommandId.SETPOINT:
        raise ValueError("Use pack_setpoint for motion fields")
    return pack_setpoint(Setpoint(0, 0, 0), timestamp_us, command, sequence=sequence)


@dataclass(frozen=True)
class Telemetry:
    timestamp_us: int
    state: int
    catch_sensor: bool | None
    positions: tuple[float | None, ...]  # deg, deg, mm
    velocities: tuple[float | None, ...]  # deg/s, deg/s, mm/s
    targets: tuple[float | None, ...]
    current_mA: tuple[float | None, ...]
    faults: int
    received_at: float

    @property
    def feedback_valid(self) -> bool:
        return all(value is not None for value in (*self.positions, *self.velocities, *self.current_mA))


def decode_telemetry(frame: bytes, *, received_at: float | None = None) -> Telemetry:
    if len(frame) != TELEMETRY.size:
        raise ValueError("Wrong telemetry length")
    fields = TELEMETRY.unpack(frame)
    if fields[:3] != (MAGIC, VERSION, TELEMETRY.size) or crc16(frame[:-2]) != fields[-1]:
        raise ValueError("Invalid telemetry header or CRC")
    if fields[4] not in range(6) or fields[5] not in (0, 1, 255):
        raise ValueError("Invalid telemetry state/sensor")
    raw = fields[6:18]
    def scaled(start: int, scales: tuple[int, int, int]) -> tuple[float | None, ...]:
        return tuple(None if value == INVALID else value / scale
                     for value, scale in zip(raw[start:start+3], scales))
    return Telemetry(fields[3], fields[4], None if fields[5] == 255 else bool(fields[5]),
                     scaled(0, (1000,1000,1)), scaled(3, (1000,1000,1)),
                     scaled(6, (1000,1000,1)), scaled(9, (1,1,1)), fields[-2],
                     time.monotonic() if received_at is None else received_at)


class TelemetryParser:
    """Bounded bytewise resynchronization; a truncated frame expires after 20 ms."""
    def __init__(self) -> None:
        self.buffer = bytearray()
        self.last_byte_at: float | None = None
        self.errors = 0

    def feed(self, data: bytes, *, now: float | None = None) -> list[Telemetry]:
        now = time.monotonic() if now is None else now
        if self.buffer and self.last_byte_at is not None and now-self.last_byte_at > FRAME_TIMEOUT_S:
            self.buffer.clear()
            self.errors += 1
        self.last_byte_at = now
        frames = []
        for value in data:
            self.buffer.append(value)
            while self.buffer:
                if self.buffer[0] != 0xA5:
                    del self.buffer[0]
                    continue
                if len(self.buffer) < 2:
                    break
                if self.buffer[1] != 0x5A:
                    del self.buffer[0]
                    continue
                if len(self.buffer) < 4:
                    break
                if self.buffer[2:4] != bytes((VERSION, TELEMETRY.size)):
                    del self.buffer[0]
                    self.errors += 1
                    continue
                if len(self.buffer) < TELEMETRY.size:
                    break
                try:
                    frame = decode_telemetry(bytes(self.buffer), received_at=now)
                except ValueError:
                    del self.buffer[0]
                    self.errors += 1
                    continue
                self.buffer.clear()
                frames.append(frame)
        return frames


class ArmController:
    """No background heartbeat, auto-enable, auto-retry, or cached motion replay."""

    def __init__(self, port: str | None = None):
        self.port = port
        self.ser = None
        self.sequence = 0
        self.parser = TelemetryParser()
        self.telemetry: Telemetry | None = None
        self._last_mcu_timestamp: int | None = None

    def _write(self, frame: bytes) -> None:
        if self.ser is None:
            raise ConnectionError("No serial port connected")
        if self.ser.write(frame) != len(frame):
            raise ConnectionError("Incomplete serial write; motion must stay disabled")

    def _command(self, command: CommandId) -> None:
        self.sequence = (self.sequence + 1) & 0xFFFFFFFF
        self._write(pack_command(command, sequence=self.sequence,
                                 timestamp_us=int(time.monotonic_ns()//1000)&0xFFFFFFFF))

    def connect(self) -> None:
        if not self.port:
            raise ValueError("An explicit serial port is required")
        if self.ser is not None:
            raise RuntimeError("Already connected")
        import serial
        self.ser = serial.Serial(self.port, 921600, timeout=0, write_timeout=0.05)
        self.ser.reset_input_buffer()
        self.telemetry = None
        self._last_mcu_timestamp = None
        self.parser = TelemetryParser()
        self._command(CommandId.DISABLE)
        self._command(CommandId.RESET_LINK)

    def poll(self) -> Telemetry | None:
        if self.ser is None:
            raise ConnectionError("No serial port connected")
        # One bounded read. GUI/host timing is not the MCU motor timing source.
        data = self.ser.read(min(self.ser.in_waiting, 4096))
        for telemetry in self.parser.feed(data):
            if self._last_mcu_timestamp is not None and not sequence_newer(
                    telemetry.timestamp_us, self._last_mcu_timestamp):
                continue  # duplicate/backward telemetry cannot renew host freshness
            self._last_mcu_timestamp = telemetry.timestamp_us
            self.telemetry = telemetry
        return self.telemetry

    def send_setpoint(self, sp: Setpoint) -> None:
        self.poll()
        telemetry = self.telemetry
        if (telemetry is None or time.monotonic()-telemetry.received_at >= MAX_TELEMETRY_AGE_S
                or telemetry.faults or telemetry.state != 4 or not telemetry.feedback_valid):
            raise RuntimeError("Fresh, fault-free, active measured feedback required; hardware is unqualified")
        self.sequence = (self.sequence+1)&0xFFFFFFFF
        self._write(pack_setpoint(sp, int(time.monotonic_ns()//1000)&0xFFFFFFFF, sequence=self.sequence))

    def disable(self) -> None:
        self._command(CommandId.DISABLE)

    def close(self) -> None:
        if self.ser is not None:
            try:
                self.disable()
            finally:
                self.ser.close()
                self.ser = None
                self.telemetry = None
