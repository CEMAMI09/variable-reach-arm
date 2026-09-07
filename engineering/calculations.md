# Engineering Calculations — Variable-Reach Catching Arm

**Reproducible source:** `engineering/sizing.py` → `engineering/sizing_results.json`

Run: `python3 engineering/sizing.py`

---

## 1. Assumptions

| Item | Value | Notes |
|------|-------|-------|
| Pivot height \(h\) | 0.65 m | Mid of 0.5–0.8 m band |
| \(L_{\min}\), \(L_{\max}\) | 0.70 m, 1.20 m | Spec targets |
| Pitch \(0^\circ\) | Horizontal | Matches FK \(z=h+L\sin\theta_p\) |
| Catcher + tip sensors | 0.17 kg | Under 180 g budget |
| Outer / inner tubes | CF, ~40/32 mm OD | Density 1600 kg/m³ |
| CF Young’s modulus | 70 GPa | Conservative; verify datasheet |
| Guide friction | 2.5 N | Measure on M1 test rig |
| Initial software speed caps | ~40% of design | Safety |

---

## 2. Masses (from tube geometry)

| Component | Mass (kg) |
|-----------|-----------|
| Outer CF tube | ≈ 0.29 |
| Inner CF tube | ≈ 0.23 |
| Catcher | 0.14 |
| Tip sensors | 0.03 |
| Moving extension clamp | 0.05 |

Distal moving mass for extension ≈ **0.45 kg**.

---

## 3. Pitch gravitational torque

At horizontal (\(\theta_p=0\)), worst static case:

\[
\tau_g = \sum_i m_i g\, r_i \cos\theta_p
\]

| Extension | \(\tau_g\) (Nm) |
|-----------|-----------------|
| \(L_{\min}=0.70\) m | ≈ 3.0 |
| \(L_{\max}=1.20\) m | ≈ **4.84** |

---

## 4. Inertia \(I(L)\)

| Case | \(I\) (kg·m²) |
|------|----------------|
| Pitch @ \(L_{\min}\) | ≈ 0.20 |
| Pitch @ \(L_{\max}\) | ≈ **0.47** |
| Yaw @ \(L_{\max}\), horizontal | ≈ **0.48** |

**Controller implication:** pitch plant gain changes by >2× from retracted to extended → start with conservative PD; schedule or feedforward after ID.

---

## 5. Dynamic pitch / yaw torque

Targets: \(\alpha_p \approx 350^\circ/\mathrm{s}^2\), \(\alpha_y \approx 400^\circ/\mathrm{s}^2\).

\[
\tau = I\alpha + \tau_g + \tau_f
\]

| Axis | Peak load (Nm) | With 2× margin |
|------|----------------|----------------|
| Pitch (raw gravity) | ≈ 8.1 | ≈ 16.3 |
| Pitch (45% counterbalance) | ≈ 6.0 | ≈ **11.9** |
| Yaw | ≈ 3.6 | ≈ **7.2** |

---

## 6. Conflict resolutions (actuators)

### Conflict A — Pitch torque vs budget motor

**Problem:** NEMA23 @ 8:1 (~16–17.6 Nm peak) is borderline vs 16.3 Nm required with full gravity and 2× margin. Industrial BLDC kits exceed $500.

**Change (minimal):**

1. Add pitch spring/gas **counterbalance** cancelling ≈45% of \(\tau_g\) (does not cancel \(I\alpha\)).
2. Keep **MKS SERVO57-class NEMA23** closed-loop + **8:1 HTD5** belt.
3. Capacity ≈ 17.6 Nm > 11.9 Nm required.

### Conflict B — Yaw NEMA17 insufficient

**Problem:** 0.6 Nm × 5 = 3 Nm ≪ 7.2 Nm.

**Change:** Use **NEMA23** on yaw with **6:1** belt (capacity ≈ 13.2 Nm). Cost delta ≈ +$35 vs NEMA17.

### Conflict C — Lead screw extension speed

8 mm lead @ 3000 rpm ≈ **0.4 m/s** < 0.8 m/s minimum → **rejected**.

**Selected:** **Option A — HTD5/GT2 timing belt**, proximal motor.

---

## 7. Extension force & drive

At \(\theta_p=45^\circ\), \(a=4\) m/s²:

| Term | Force (N) |
|------|-----------|
| \(ma\) | ≈ 1.8 |
| Gravity along boom | ≈ 3.1 |
| Friction | 2.5 |
| **Peak** | ≈ **7.4** |

22 mm pitch-diameter pulley:

| Metric | Value |
|--------|--------|
| Pulley torque | ≈ 0.08 Nm |
| With 2× + NEMA17 @ 1:1 | **OK** |
| Speed @ 1.2 m/s | ≈ 1040 rpm at pulley |

Option comparison scores: belt **9**, Dyneema **7**, lead screw **3** (fails velocity).

---

## 8. Structure / bearings

| Metric | Estimate |
|--------|----------|
| Tip deflection (telescoping knock-down) | ≪ 25 mm (~0.6 mm ideal CF cantilever — verify real laminate) |
| Pitch shaft | Ø12 mm steel |
| Bearings | 2× 6001-2RS (or 6801 thin-section if packaging tight) |
| Bearing radial load est. | tens of N + moment/span — 6001 ample |
| Min overlap | 200 mm |

Even if real CF E is lower or joints softer, 40 mm OD tube has margin vs 25 mm tip limit. **Validate on M1 deflection test.**

---

## 9. Electrical

| Item | Selection |
|------|-----------|
| Bus | 24 V |
| PSU | 24 V ≥ 15 A (≈360 W) |
| Peak mechanical power (all axes, rough) | tens of W continuous, higher burst |
| E-stop | NC mushroom cutting motor bus via relay/contactor |

---

## 10. Final component selections (rationale)

| Role | Part class | Why |
|------|------------|-----|
| Pitch motor | NEMA23 closed-loop (SERVO57) | Torque after 8:1; encoder onboard; budget |
| Yaw motor | NEMA23 closed-loop (SERVO57) | Same family; inventory simplicity |
| Extension motor | NEMA17 closed-loop (SERVO42) | Low force; save mass/cost at shoulder |
| Pitch/yaw reduction | HTD5 belts | Stiff, low backlash, serviceable |
| Extension | GT2/HTD5 belt, 22 mm pulley | Speed + proximal mass |
| Tubes | CF 40 mm / 32 mm | Stiffness/mass; Al acceptable substitute |
| MCU | Teensy 4.1 | Reliable ≥1 kHz control, USB CDC |
| Catcher | TPU funnel + mesh | Compliance, <150 g |
| Latch | 9 g micro-servo | Distal mass OK |
| Cameras | 2× ≥60 FPS USB (phase 3) | Latency over megapixels |
| Counterbalance | Gas spring or torsion springs at pitch | Resolves Conflict A |

---

## 11. Energy (order of magnitude)

One aggressive extend + pitch slew ≈ **10–20 J** mechanical — negligible vs PSU; thermal motor duty is the real limit (monitor current logs).
