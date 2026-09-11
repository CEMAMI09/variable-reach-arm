# Electronics, embedded and power engineering review B

Review date: 2026-09-07. Status: **not ready to order the complete electronics or run
high-speed hardware**. Keep Teensy 4.1 as a capable commissioning controller if already
owned; its compute capacity is not the bottleneck. The old repository described
driver, encoder, homing and safety features that were not implemented.

## Problems, consequences and implemented response

1. **Signed int16 millidegrees overflow at ±32.767 degrees.** Valid ±70 degree poses
   and intended rates failed packing or wrapped telemetry. Replaced with matching
   v2 32-bit command/telemetry fields, static size checks and cross-language tests.
   Tradeoff: larger frames, insignificant at 100 Hz USB telemetry.
2. **Invalid CRC refreshed the watchdog and stream had no recovery framing.**
   Damaged/replayed bytes could appear alive. Added header/version/size/CRC validation,
   sequence checks, bounded resynchronization and inter-byte expiry. Tradeoff:
   corrupted commands latch faults and require diagnosis instead of silent retry.
3. **No drivers/feedback/homing were implemented; fabricated zero looked plausible.**
   Motion now remains under a permanent unqualified fault, telemetry uses explicit
   missing sentinels, unsupported claw/home/trajectory commands reject, and no servo
   output is configured. Tradeoff: honest logic-only release until real adapters exist.
4. **E-stop sensing missed broken wires; software watchdog was unused.**
   Added NC/open-wire sense interpretation and timing diagnostics. A recovered-loop
   diagnostic cannot interrupt a hung MCU; a hardwired stop and independent watchdog
   remain mandatory. Tradeoff: additional verified hardware and cost.
5. **Arbitrary huge gains saturated a normalized output for tiny angular errors.**
   Replaced presumed tuning with zero gains, finite checks, reset and anti-windup.
   This controller is a tested mathematical scaffold, not a motor controller selection.
6. **Three-finger claw was represented by an unverified latch bit.**
   No automatic actuation remains. Select an actuator against closure-time, force,
   travel, stall-current and feedback requirements; qualify aperture and retention.
   Preserve the actual three-finger mechanism, with actuation proximal where feasible.

## Motor/driver decisions

MKS SERVO42C is a candidate board, not a verified motor operating envelope. Its maker
lists 7–28 V operation, current setting up to 3 A and maximum 1000 rpm.
At 36 teeth × 2 mm pitch, 1.2 m/s requires 1000 rpm: there is no speed reserve and
loaded torque is unproven. 1.5 m/s would require 1250 rpm and exceeds that published
limit. Do not substitute holding torque for torque at speed. Verify exact motor,
board revision, firmware version, bus voltage and torque-speed curve before buying.
[Makerbase SERVO42C documentation](https://github.com/makerbase-mks/MKS-SERVO42C).

The old SERVO57C-or-equivalent item is not a sufficiently exact electrical interface.
Choose one exact board/motor combination and archive its manual, torque-speed curve,
current definition (peak/RMS), command protocol, feedback update timing, fault output
and safe-disable behavior. Changing between C/D revisions is not a drop-in software
decision. A closed-loop motor encoder does not detect belt slip, output-shaft damage
or telescoping belt/clamp movement. Provide joint reference and a defensible output
feedback/following-error strategy before releasing autonomous motion.

Prefer timer-generated STEP/DIR into the drive's inner current/position loop if its
interface is qualified. Do not assume a normalized MCU duty value maps to that
interface. Vendor UART may be sufficient for telemetry only after measuring aggregate
poll latency; three axes with sequential blocking transactions are not automatically
a 1 kHz feedback path. Record encoder age, packet counters, following error and faults.

## Power calculation and simultaneous motion

The reproducible screen in `engineering/review_sizing.py` and its generated
`engineering/review_results.json` currently bounds simultaneous mechanical power at
approximately93.19W, assumes65% conversion efficiency,40W major-motor copper loss,
35W extension/driver loss and15W logic, giving approximately233.36W /24V =9.72A.
These are assumption-based procurement screens, not measured current. At 25% reserve
the arithmetic minimum is12.15A, before ambient derating and verified surge/inrush.

Do not sum motor phase-current labels to estimate bus current. For each phase,
copper loss is I_RMS² R; sum actual phases, winding temperature dependence, iron loss,
driver switching/conduction loss and mechanical power, then divide by bus voltage.
Calculate RMS current over the real duty cycle; holding and failed-catch retries can
dominate heating even if average mechanical work is low. Measure peak current on all
axes accelerating together, RMS over repeated trials, supply droop and driver case
temperature. There is no measured continuous thermal envelope yet.

LRS-350-24 remains a possible 24 V supply if enclosure/thermal/AC integration is
appropriate; use its exact model rating and derating curves, not a generic 15 A label.
Its source-current/overvoltage protection is not a regenerative sink specification.
[Mean Well LRS-350 data sheet](https://www.meanwell.com/Upload/PDF/LRS-350/LRS-350-SPEC.PDF).

The revised mechanical screen estimates about8.35J of recoverable stopping/gravity
energy. For an isolated 4700 microfarad bus starting at 24 V,
V_final = sqrt(24² + 2E/C) = approximately64.27V if all of it reaches the capacitor.
This is far above a 28 V-rated drive. Even 10 J would require about 0.096 F just to
stay between 24 and 28 V. A small capacitor or arbitrary TVS is not a braking system.

Select a shunt clamp/dump with documented threshold/tolerance, pulse energy, repetitive
thermal rating and bus-voltage overshoot below the **lowest** drive rating. Keep it
on the driver side of the stop contactor. A 24 V nominal / 28 V maximum driver leaves
a tight tolerance budget; this remains a purchase/design gate. Use a higher-voltage
rated compatible drive or a lower qualified bus only after recalculating motor speed
and clamp behavior. Bulk capacitance also increases contactor inrush.

## Wiring and interfaces

- Teensy GPIO and ADC accept 0–3.3 V and are not 5 V tolerant. Level-shift any 5 V
  encoder/fault interfaces and verify opto-input current/thresholds. Avoid simultaneous
  external VIN and USB power unless the documented VUSB/VIN isolation is performed.
  Keep a separate gripper supply if its transients can reset logic.
  [PJRC Teensy 4.1 electrical documentation](https://www.pjrc.com/store/teensy41.html).
- Use an enclosed mains inlet/supply with protective earth, fuse, strain relief,
  finger-safe terminals and a deliberate disconnect. Printed electronics covers can
  guard low-voltage access; they do not establish a rated mains enclosure.
- Prototype a short16AWG copper trunk for the screened9.72A bus and12.15A reserve
  requirement; qualify
  actual insulation, routing, bundle heating and connector ratings. At 13.2 mOhm/m
  nominal copper resistance, a 2 m total loop at 10 A drops 0.264 V and dissipates
  2.64 W. This is a resistance estimate, not an ampacity certificate.
- Use separately fused branches sized to each conductor and connector. Fuse ratings
  require time/current curves, fault available current and measured inrush. Do not
  treat a fuse as software current control or use unverified Dupont connectors for
  motor power. Locking connectors, keyed pinouts and ferrules where specified.
- Run twisted motor pairs; separate motor wires from encoder/limit wiring. Shield
  according to driver guidance, bond chassis/PE deliberately, keep power returns out
  of logic signal paths. Test USB disconnect immunity while reversing all axes.
- NC switch loops use 3.3 V pullups with filtering/Schmitt inputs appropriate to wire
  length. Their polarity is now explicit in firmware; homing needs bounded debounce
  and fault detection without delaying the hardware E-stop chain.
- Budget real cable flex loops through full yaw, pitch and telescope travel. Add
  strain relief at both stationary and moving ends; verify wire bend radius and
  keep the claw cable out of moving guides and belt teeth.

## Required additions and decisions before purchasing

Price the DC-rated stop/manual-reset chain, independent enable/watchdog, pitch brake
or restraint, regenerative dump, individual fuses/holders, mains enclosure/PE,
locking connectors/level shifting and real gripper actuator/feedback. These are
essential functions, not optional budget cuts. Reuse an owned MCU/PSU/camera only
after checking ratings; stage the single-axis rig before buying all three drives.

Open design work: exact wiring schematic and connector/pin map; driver/encoder
adapters; current channel/thresholds; homing; stop/brake interface; gripper actuation;
bus clamp selection. Prototype measurements: torque-speed and duty temperature,
current/droop/regen waveforms, EMI and timeout behavior, feedback latency and claw
closure/retention. Electronics readiness score: 4/10; embedded motion readiness:
3/10. The safety/protocol scaffold is useful but these scores must not imply a
qualified electromechanical system.

## Build evidence

The root review task successfully compiled the actual Teensy target with
`pio run -d firmware` on2026-09-07 (reported61.90s). No hardware was flashed.
This verifies the current target build in addition to host-side protocol/control
tests; it does not establish driver interfaces, timing under physical I/O load,
encoder accuracy, brake action or a qualified motion system. Permanent unqualified
motion gating remains appropriate until those hardware functions are implemented
and tested.

