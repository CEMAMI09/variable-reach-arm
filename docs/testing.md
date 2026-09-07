# Testing Procedures

## Milestone 1 — Extension rig

| Test | Method | Pass |
|------|--------|------|
| Stroke | Command 0→500 mm | Full travel, no bind |
| Speed | Step to max soft cap | ≥ 0.8 m/s measured |
| Accel | Differentiate velocity | ≈ 3–5 m/s² region |
| Repeatability | 20 cycles to mid point | ≤ ±10 mm |
| Deflection | Tip load 2 N at L_max | ≤ 25 mm |

## Positioning (integrated)

RMS / peak error, settling time (±2° / ±10 mm band), yaw/pitch repeatability ±1°.

## Vision

Ball position error vs surveyed points; prediction error vs horizon; pipeline latency.

## Catching

Defined volume, underhand tosses 2–4 m/s. Record success %, velocity, intercept distance, extension amount, prediction time. Target ~70% or document actual.

## Impact experiment

Compare rigid hold vs velocity match vs active retract — peak tip accel / force.

## Logging

Every formal run writes CSV under `data/experiments/` with notes linking redesigns.
