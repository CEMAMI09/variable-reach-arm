# System Architecture — Variable-Reach Catching Arm

> **Review B status:** this original block diagram describes intended modules, not
> implemented capabilities. The protocol below is historical and replaced by
> `embedded_protocol.md` (v2:44-byte commands/62-byte telemetry). Motor adapters,
> true joint feedback, homing, motion execution and three-finger claw actuation are
> absent; firmware remains locked. Revised geometry/materials are in the shared
> engineering JSON. No net. No automatic throw. Read current software/electronics
> review documents for the tested implementation boundary.

## 1. Overview

```text
┌─────────────────────────────────────────────────────────────────┐
│                         HOST PC                                  │
│  vision → estimation → interception planner → trajectory cmd     │
│  simulation / logging / visualization / calibration              │
└────────────────────────────┬────────────────────────────────────┘
                             │ USB CDC / serial packet protocol
                             │ (not Wi-Fi for RT path)
┌────────────────────────────▼────────────────────────────────────┐
│                    EMBEDDED CONTROLLER (MCU)                     │
│  500–1000 Hz: PID/PD + limits + watchdog + e-stop sense          │
│  axes: yaw | pitch | extension | (latch micro-servo)             │
└───────┬──────────────────┬──────────────────┬───────────────────┘
        │                  │                  │
   ┌────▼────┐        ┌────▼────┐        ┌────▼────┐
   │ Yaw     │        │ Pitch   │        │ Ext.    │
   │ motor+  │        │ motor+  │        │ motor+  │
   │ encoder │        │ encoder │        │ encoder │
   │ belt    │        │ belt    │        │ belt    │
   └────┬────┘        └────┬────┘        └────┬────┘
        │                  │                  │
   Base + yaw         Pitch bracket     Outer boom
   bearing stack      + shaft           + inner tube
                                            │
                                      ┌─────▼─────┐
                                      │ Catcher + │
                                      │ retention │
                                      │ + sense   │
                                      └───────────┘
```

## 2. Mechanical subsystems

| Subsystem | Function | Interfaces |
|-----------|----------|------------|
| Base plate | Mount to bench; e-stop; PSU | Bolted feet; cable glands |
| Yaw stage | Rotate shoulder about Z | Motor → belt → bearing-supported turret |
| Pitch stage | Elevate boom | Motor → belt → shaft + dual bearings |
| Outer boom | Structural tube | Clamped to pitch bracket |
| Inner boom | Telescoping reach | Guides + belt clamp |
| Extension drive | \(\Delta L\) control | Proximal pulley, HTD/GT belt, idlers, hard stops |
| Catcher | Capture foam ball | Bolt pattern on inner tip |
| Retention | Keep ball after catch | Micro-servo or cable from proximal |
| Guards / stops | Safety | Mechanical travel limits |

## 3. Electronics architecture

```text
AC mains → 24V PSU → [E-STOP contactor/relay] → motor drivers (bus)
                   → MCU logic 5V/3.3V buck (always on for status)

MCU ←→ driver UART/STEP-DIR (closed-loop steppers)
MCU ←→ limit switches, e-stop sense, catch sensor
MCU ←→ USB to host
```

**E-stop:** Cuts motor DC bus independently of firmware. MCU only senses state and enters FAULT.

## 4. Software modules

### Host (`host/`)

| Package | Responsibility |
|---------|----------------|
| `vision/` | Capture, color segment, blob center, timestamps |
| `estimation/` | Ballistic fit / KF state |
| `kinematics/` | FK, IK, workspace clamp |
| `planning/` | Reach selection, interception search, cost \(J\) |
| `trajectories/` | Quintic / trapezoidal multi-axis profiles |
| `control/` | High-level state machine, send setpoints |
| `telemetry/` | CSV logging, fault archive |
| `visualization/` | Live overlay + plots |

### Firmware (`firmware/`)

| Module | Responsibility |
|--------|----------------|
| `motors` | Driver interface, current limits |
| `encoders` | Axis state |
| `control_loop` | Cascaded position/velocity at 1 kHz |
| `trajectory` | Execute host or local profiles |
| `safety` | Limits, watchdog, fault latch |
| `protocol` | Packet encode/decode |
| `homing` | Extension + soft zero yaw/pitch |

### Simulation (`simulation/`)

Kinematics + limits + projectile + planner for offline validation.

## 5. Communication protocol (v1)

Little-endian binary frames over USB CDC, 115200–921600 baud.

### Host → MCU command (32 bytes)

| Offset | Type | Field |
|--------|------|-------|
| 0 | u32 | timestamp_us |
| 4 | u8 | cmd_id |
| 5 | u8 | flags |
| 6 | i16 | yaw_mdeg |
| 8 | i16 | pitch_mdeg |
| 10 | i16 | extension_mm |
| 12 | i16 | yaw_vel_mdeg_s |
| 14 | i16 | pitch_vel_mdeg_s |
| 16 | i16 | ext_vel_mm_s |
| 18–29 | — | reserved / latch |
| 30 | u16 | crc16 |

### MCU → Host telemetry (48 bytes)

| Field | Content |
|-------|---------|
| timestamp, cmd_echo | sync |
| yaw/pitch/ext pos & vel | measured |
| motor currents | mA |
| status / faults | bitfield |
| catch_sensor | bool |
| crc16 | integrity |

**cmd_id examples:** ENABLE=1, DISABLE=2, SETPOINT=3, HOME=4, TRAJ=5, ESTOP_ACK=0xFF.

## 6. Control layering

```text
Vision (30–120 Hz)
  → Estimator (per detection)
    → Interception planner (10–50 Hz when ball in flight)
      → Trajectory generator (piecewise, streaming waypoints)
        → MCU setpoint stream (~100–200 Hz)
          → MCU joint PD/PID (500–1000 Hz)
```

Gain scheduling note: pitch gains may scale with \(I(L)\). Start with robust PD; add feedforward after identification.

## 7. Power & grounding

- Single-point chassis ground at base.
- Separate logic and motor returns meeting at PSU.
- Shielded encoder / USB cables where practical.
- Ferrites on motor leads if EMI affects USB.

## 8. Safety state machine

```text
BOOT → SELF_TEST → DISABLED
         ↓ enable
       IDLE (low speed caps)
         ↓ armed
       ACTIVE
         ↓ fault / e-stop / watchdog / lost host
       FAULT (motors powerless or held; latch until clear+reenable)
```

## 9. Data products

- `data/calibration/` — camera intrinsics/extrinsics, axis zero offsets.
- `data/experiments/` — CSV runs + notes linking to redesign log.
- Plots via `tools/plot_run.py`.

## 10. CAD / manufacturing interface

Parametric FreeCAD document(s) under `cad/freecad/`. Exported STEP/STL/drawings under `cad/step|stl|drawings/`. Print metadata in `cad/drawings/print_guide.md`.
