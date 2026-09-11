"""CSV telemetry logger."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


TELEMETRY_FIELDS = [
    "timestamp",
    "time_domain",
    "exposure_time_s",
    "host_receive_time_s",
    "planning_time_s",
    "scheduled_intercept_time_s",
    "perception_age_s",
    "fit_rms_m",
    "prediction_error_m",
    "interception_error_m",
    "claw_trigger_time_s",
    "claw_closed_time_s",
    "calibration_id",
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
    def __init__(self, path: str | Path, *, overwrite: bool = False):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = self.path.open("w" if overwrite else "x", newline="", encoding="utf-8")
        self._w = csv.DictWriter(self._fh, fieldnames=TELEMETRY_FIELDS)
        self._w.writeheader()

    def log(self, row: dict[str, Any]) -> None:
        unknown = set(row)-set(TELEMETRY_FIELDS)
        if unknown:
            raise ValueError(f"unknown telemetry fields: {sorted(unknown)}")
        full = {k: row.get(k, "") for k in TELEMETRY_FIELDS}
        self._w.writerow(full)
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False
