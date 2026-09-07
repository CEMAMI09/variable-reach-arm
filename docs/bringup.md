# Bring-up Instructions

Order matters. Do not enable high-speed motion early.

## 0. Bench power

1. Assemble PSU, e-stop, relay — verify e-stop kills motor bus.
2. Power MCU from logic supply only; confirm USB serial.
3. Flash firmware; confirm telemetry CRC frames.

## 1. Single-axis dry check

1. One motor disconnected from mechanism → confirm direction / encoder sign.
2. Low-current jog; verify `CMD_DISABLE` and e-stop.

## 2. Extension rig (Milestone 1)

1. Outer/inner tubes + guides + belt only (no pitch motion).
2. Home; closed-loop position steps; log speed/accel/bind.
3. Redesign guides before integrating shoulder if binding occurs.

## 3. Yaw / pitch (Milestone 2)

1. Shoulder without full boom mass first if possible.
2. Counterbalance installed before aggressive pitch moves.
3. Soft limits verified against hard clearance.

## 4. Integrate boom (Milestone 3)

Command `[θy, θp, L]` slowly; expand speed after tracking error acceptable.

## 5. Host stack

Run `python3 -m simulation.run_demo` before vision. Then Phase 1 manual setpoints over serial.
