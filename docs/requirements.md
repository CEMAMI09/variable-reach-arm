# Requirements — Variable-Reach Dynamic Catching Arm

**Project:** Stationary 3-DOF high-speed manipulator with dynamically telescoping reach for intercepting lightweight foam balls, with stretch goals for throwing.

**Document status:** Derived from project specification. Conflicts with budget or physics are resolved in `engineering/calculations.md`.

---

## 1. Objective

Build a purpose-built catching robot that can:

1. Detect a thrown lightweight foam ball.
2. Predict its trajectory.
3. Move to an interception point.
4. **Change physical reach while moving** when the interception point exceeds normal reach.
5. Catch and retain the ball.
6. Eventually throw toward a specified target.

Central capability: **dynamic morphology as part of interception planning** — extend only as far as necessary; remain retracted when possible (lighter, stiffer, faster).

### Non-goals (v1)

- Generic industrial 6-DOF arm.
- Anthropomorphic elbow or multi-axis wrist.
- Humanoid multi-finger hand.
- Hard projectiles (baseballs, metal, rocks).
- Reinforcement learning as first control approach.
- Separate flywheel launcher for throwing.

---

## 2. Kinematic architecture

```
Fixed base → yaw → pitch → variable-length telescoping boom → lightweight catcher
```

| DOF | Axis | Notes |
|-----|------|--------|
| 1 | Shoulder yaw | Vertical axis, bearing-supported |
| 2 | Shoulder pitch | Highest torque axis |
| 3 | Linear extension | Single active telescoping stage |

Configuration: \( q = [\theta_y, \theta_p, L] \)

---

## 3. Geometry

| Parameter | Min | Target | Max | Unit |
|-----------|-----|--------|-----|------|
| Base footprint | — | ≤350×350 | 350×350 | mm |
| Pivot height \(h\) | 500 | 650 | 800 | mm |
| Retracted reach \(L_{\min}\) | 650 | **700** | 750 | mm |
| Extended reach \(L_{\max}\) | 1100 | **1200** | 1250 | mm |
| Extension stroke \(\Delta L\) | — | **500** | — | mm |
| Min telescoping overlap | 180 | 200 | 250 | mm |

### Workspace

| Axis | Range |
|------|--------|
| Yaw \(\theta_y\) | \(-70^\circ \leq \theta_y \leq +70^\circ\) (min total 140°) |
| Pitch \(\theta_p\) | \(-15^\circ \leq \theta_p \leq +70^\circ\) |

Software limits must prevent boom contact with floor, base, frame, operators, or electronics. Primary workspace: forward hemisphere.

### Forward kinematics (world frame)

\[
x = L\cos(\theta_p)\cos(\theta_y),\quad
y = L\cos(\theta_p)\sin(\theta_y),\quad
z = h + L\sin(\theta_p)
\]

Inverse: \( L = \sqrt{x^2+y^2+(z-h)^2} \) with appropriate \(\theta_y,\theta_p\), clamped to workspace.

---

## 4. Target object

| Spec | Value |
|------|--------|
| Type | Lightweight foam ball |
| Diameter | 60–80 mm (preferred ~70 mm) |
| Mass | 20–80 g (hard max 100 g) |
| Incoming speed | 2–4 m/s initial; stretch 5–6 m/s |

---

## 5. Performance

### Static / positioning

| Metric | Target |
|--------|--------|
| Yaw repeatability | ≤ ±1° |
| Pitch repeatability | ≤ ±1° |
| Extension repeatability | ≤ ±10 mm |
| End-effector static error | < 25 mm over most workspace |
| Tip deflection at \(L_{\max}\) | < 25 mm under normal static loading |

### Dynamic

| Metric | Minimum | Target |
|--------|---------|--------|
| Extension speed | 0.8 m/s | 1.2–1.5 m/s |
| Extension acceleration | — | 3–5 m/s² |
| Yaw / pitch angular velocity | — | 100–150 °/s |

Initial software limits must be considerably lower (~40% of design targets).

### Mass

| Item | Target |
|------|--------|
| Catcher | < 150 g |
| Catcher + tip sensors | < 180 g |
| Major motors | Near base / yaw / pitch — **not** on extending tube |

Structural safety factor ≈ 2.5× static. Drivetrain torque margin ≈ 2× where practical.

---

## 6. Mechanical subsystems

### Telescoping boom

- Single active stage (outer tube + inner sliding tube).
- Replaceable low-friction guides (≥2 widely spaced regions).
- Materials: carbon fiber and/or thin-wall aluminum primary structure; 3D print for guides, mounts, catcher, brackets.
- Both extension and retraction actively driven (no gravity/spring-only return).

### Extension drive (selection by calculation)

Preferred candidates:

- **Option A:** Timing-belt-driven telescope (proximal motor).
- **Option B:** Dyneema / high-strength cable capstan (proximal motor).

Lead screw only if calculations prove dynamics are met (expected rejection for speed).

### Yaw

Rigid base attachment, bearing radial+axial support, closed-loop encoder, preferred belt reduction, hard stops / clearance, software limits. No unsupported motor-shaft cantilever of the full assembly.

### Pitch

Sized with \( \tau = I\alpha + \tau_g + \tau_f \). Controller must know \(L\) because \(I = I(L)\). Optional counterbalance only if it does not harm dynamics.

### End effector

Forgiving capture: 3 compliant fingers or funnel basket + soft cradle/net.

| Spec | Value |
|------|--------|
| Entrance diameter | 120–150 mm |
| Depth | 100–150 mm |
| Retention | Compliant gate / micro-servo / cable latch (lightweight) |
| Capture confirm | IR break-beam, switch, Hall, FSR, etc. |

Active impact absorption (stretch): controlled short retraction after capture to reduce \(v_{rel}\).

---

## 7. Electronics & sensing

### Required feedback

- Yaw position (encoder)
- Pitch position (encoder)
- Extension position (motor encoder and/or linear/string encoder)
- Homing / limit switches on extension
- Hardware e-stop cutting motor power independent of software

### Recommended / optional

Motor current; boom strain; catch force; tip acceleration.

### Control split

| Layer | Role | Loop rate |
|-------|------|-----------|
| Embedded MCU | Motors, encoders, safety, trajectories, watchdog, telemetry | 500–1000 Hz |
| Host PC | Vision, estimation, planning, logging, visualization | Best-effort |

Wired link only for hard real-time path (USB CDC / serial / CAN / Ethernet). No Wi-Fi for motor control.

Budget: **hard max $500**; preferred **$300–450**; ≥10–15% reserve.

---

## 8. Perception & planning

### Vision phases

1. Manual commands only.
2. Single-camera planar tracking.
3. Stereo 3D (preferred ≥60 FPS, target 120 FPS; latency > resolution).

### Ball state

\[
\mathbf{x} = [x,y,z,v_x,v_y,v_z]
\]

Ballistic model initially; drag optional. Estimator: LS fit / KF / EKF.

### Reach selection

- If \(L_{req} \le L_{normal}\): remain retracted.
- If \(L_{normal} < L_{req} \le L_{max}\): extend to \(L_{req} + L_{margin}\) (margin 20–50 mm).
- If \(L_{req} > L_{max}\): unreachable.

### Interception

Search future times \(t_i\); valid only if workspace + actuator limits allow arrival. Minimize configurable cost \(J\) (time, extension, accel, velocity penalties).

### Trajectories

Smooth profiles (trapezoid / S-curve / quintic). No step position jumps. Simultaneous multi-axis motion when beneficial.

---

## 9. Safety & faults

Mandatory: hardware e-stop, current limits, travel limits, watchdog, encoder fault detection, software velocity caps, startup verification, low-speed homing, mechanical extension stops, lightweight foam only, optional barrier for high-speed tests.

Disable high-speed motion on: invalid encoders, unexpected limit, watchdog, lost comms, overcurrent, extension out of range, illegal trajectory. Log fault reason.

---

## 10. Telemetry & testing

Log CSV-exportable: axis positions/targets/velocities, currents, predicted/measured ball state, interception point, catch result.

Quantitative tests required for positioning, dynamics, structure, vision, catching, and impact (see `docs/testing.md`).

### Initial success bar (≈8 weeks)

Autonomous homing, 3-axis position control, rapid extension, ball track + predict, reach decision, catch slow–moderate underhand throws. Target ≈**70%** catch success in a defined test volume — or document measured rate honestly.

### Defining demo

- **A:** Catch inside normal reach without extending.
- **B:** Catch beyond normal reach with dynamic extension.
- **C:** Catch and return / throw (stretch).

---

## 11. Software & CAD deliverables

Repository layout per architecture doc. FreeCAD parametric model with listed parameters. Calculations before frozen mounts. Modular host + firmware. Simulation before autonomous physical intercepts.

### Development order (control)

Manual low-speed → homing → position → velocity → accel → multi-axis → tracking → dynamic extension → vision pose → intercept → velocity-matched catch → throw.

### Milestones

M0 calculations/BOM → M1 extension rig → M2 yaw/pitch → M3 integrate telescope → M4 trajectories → M5 track ball → M6 predict → M7 intercept no contact → M8 drop catch → M9 toss catch → M10 reach decision demo → M11 impact absorption → M12 throwing.

---

## 12. Design priorities

1. Function  
2. Safety  
3. Dynamic performance  
4. Low distal mass  
5. Stiffness  
6. Serviceability  
7. Measurability  
8. Iteration ease  
9. Cost  
10. Appearance  

Visible engineering preferred over decorative panels. Modular subsystems; expect failures and document redesign loops.
