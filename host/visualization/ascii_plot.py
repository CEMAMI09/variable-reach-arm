"""Minimal ASCII visualization of planner output."""

from __future__ import annotations

from host.planning.intercept import InterceptSolution
from simulation.arm_model.sim_core import SimResult


def render_sim(result: SimResult, sol: InterceptSolution | None = None) -> str:
    lines = [result.message]
    if result.intercept_found:
        lines.append(f"t={result.t_intercept:.3f}s  L={result.L_cmd:.3f}m  extended={result.extended}")
    lines.append("ball z vs time (ascii):")
    for t, x, y, z in result.ball_path[::3]:
        bar = int(max(0, min(40, z * 20)))
        mark = "*" if result.t_intercept and abs(t - result.t_intercept) < 0.03 else " "
        lines.append(f"{t:5.2f} |{'#' * bar}{mark} z={z:.2f}")
    return "\n".join(lines)
