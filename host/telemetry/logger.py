"""CSV telemetry logger."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


TELEMETRY_FIELDS = [
    "timestamp",
    "yaw_pos",
    "yaw_target",
    "yaw_vel",
    "pitch_pos",
    "pitch_target",
    "pitch_vel",
    "ext_pos",
    "ext_target",
    "ext_vel",
    "current_yaw",
    "current_pitch",
    "current_ext",
    "ball_x",
    "ball_y",
    "ball_z",
    "ball_x_meas",
    "ball_y_meas",
    "ball_z_meas",
    "intercept_x",
    "intercept_y",
    "intercept_z",
    "catch_result",
    "fault_bits",
]


class TelemetryLogger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w", newline="")
        self._w = csv.DictWriter(self._fh, fieldnames=TELEMETRY_FIELDS)
        self._w.writeheader()

    def log(self, row: dict[str, Any]) -> None:
        full = {k: row.get(k, "") for k in TELEMETRY_FIELDS}
        self._w.writerow(full)
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()
