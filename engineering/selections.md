# Component Selection Summary

Selections follow `engineering/calculations.md` and `bom.csv`. Total BOM ≈ **$449** before reserve; if over, defer stereo camera #2 until Milestone 5.

## Actuators

| Axis | Motor | Reduction | Reason |
|------|-------|-----------|--------|
| Yaw | NEMA23 closed-loop (SERVO57-class) | HTD5 6:1 | NEMA17 failed torque margin |
| Pitch | NEMA23 closed-loop | HTD5 8:1 + ~45% counterbalance | Highest τ; budget vs BLDC |
| Extension | NEMA17 closed-loop | Direct / 1:1 on 22 mm GT2 pulley | F_peak≈7 N; keep motor proximal |
| Latch | 9 g micro-servo | Direct | Minimal tip mass |

Closed-loop steppers include encoders — satisfy “closed-loop motors required” without industrial servo pricing.

## Structure

| Part | Choice | Reason |
|------|--------|--------|
| Outer boom | CF Ø40×2 mm wall × ~750 mm | Stiffness/mass; deflection ≪25 mm in calc |
| Inner boom | CF Ø32×2 mm × ~750 mm | 200 mm overlap at full extend |
| Guides | Printed PETG/nylon + UHMW tape | Replaceable inserts |
| Base | 6 mm Al 300×300 | ≤350 mm footprint |

## Sensing / control

| Part | Choice | Reason |
|------|--------|--------|
| MCU | Teensy 4.1 | 1 kHz control + USB CDC proven class |
| Extension limits | Mechanical switches | Homing mandatory |
| Catch sense | IR break-beam | Light, cheap |
| Vision | USB ≥60 FPS (1 now, 2 later) | Latency over 4K |

## Safety

Hardware e-stop → relay opens 24 V motor bus. MCU watches e-stop input and latches FAULT.
