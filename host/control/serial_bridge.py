"""Host-side serial bridge (stub + framing)."""

from __future__ import annotations

import struct
from dataclasses import dataclass


def crc16(data: bytes) -> int:
    crc = 0xFFFF
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = (crc >> 1) ^ 0xA001 if (crc & 1) else (crc >> 1)
    return crc & 0xFFFF


@dataclass
class Setpoint:
    yaw_deg: float
    pitch_deg: float
    ext_mm: float
    yaw_vel: float = 0.0
    pitch_vel: float = 0.0
    ext_vel: float = 0.0
    latch: int = 0


def pack_setpoint(sp: Setpoint, timestamp_us: int = 0, cmd_id: int = 3) -> bytes:
    body = struct.pack(
        "<IBBhhh hhh B11s",
        timestamp_us,
        cmd_id,
        0,
        int(sp.yaw_deg * 1000),
        int(sp.pitch_deg * 1000),
        int(sp.ext_mm),
        int(sp.yaw_vel * 1000),
        int(sp.pitch_vel * 1000),
        int(sp.ext_vel),
        sp.latch,
        bytes(11),
    )
    # Above pack may be wrong size — build explicitly
    raw = bytearray(32)
    struct.pack_into("<I", raw, 0, timestamp_us)
    raw[4] = cmd_id
    raw[5] = 0
    struct.pack_into("<hhh", raw, 6, int(sp.yaw_deg * 1000), int(sp.pitch_deg * 1000), int(sp.ext_mm))
    struct.pack_into(
        "<hhh",
        raw,
        12,
        int(sp.yaw_vel * 1000),
        int(sp.pitch_vel * 1000),
        int(sp.ext_vel),
    )
    raw[18] = sp.latch
    c = crc16(bytes(raw[:30]))
    struct.pack_into("<H", raw, 30, c)
    return bytes(raw)


class ArmController:
    """High-level state machine placeholder for Milestone 3+."""

    def __init__(self, port: str | None = None):
        self.port = port
        self.ser = None

    def connect(self) -> None:
        if not self.port:
            return
        import serial  # type: ignore

        self.ser = serial.Serial(self.port, 921600, timeout=0.05)

    def send_setpoint(self, sp: Setpoint) -> None:
        frame = pack_setpoint(sp)
        if self.ser:
            self.ser.write(frame)
