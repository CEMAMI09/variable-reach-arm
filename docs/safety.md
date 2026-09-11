# Safety and release gates — engineering review B

The repository is **not a high-speed motion release**. Firmware boots into a persistent
`FLT_UNQUALIFIED` lock. A host command cannot clear it, home the axes, drive the
three-finger claw or enable motor outputs. Native tests and a successful firmware
build prove software properties only. `motors_disable_all()` is still an unimplemented
hardware adapter and therefore provides **no physical stopping guarantee**.

## Independent stop architecture

Use a hardwired normally-closed E-stop loop with a deliberate manual restart. It must
drop motor power/driver enable independently of the MCU and host. The MCU senses an
auxiliary NC contact; GPIO HIGH means pressed, disconnected or broken wire. A shorted
sense wire is not diagnosed by this single-channel circuit. This is a prototype
architecture, not a certified safety system.

Place the regenerative clamp/dump across the **driver-side** DC bus so it remains
connected when the contactor opens. Keep logic power available for diagnostics. Select
a contactor with a published DC interrupt rating at the actual voltage/current and
inrush, fuse the bus and branches, and verify contact welding/manual-reset behavior.
A generic automotive relay rating alone is insufficient. Do not cut motor phases.

Power removal alone can make the pitch axis fall and can allow the telescope to
slide. A normally engaged mechanical pitch brake or independent load restraint must
hold the worst extended load after loss of power; a motor-side brake cannot protect
against a failed belt. Provide a secondary catch/restraint for initial tests, capture
the sliding tube with mechanical stops, and keep all pinch/sweep zones inaccessible.
Brake **holding** torque does not establish dynamic stop-energy capacity. Establish
stop distance with measured inertia, driver stop behavior and brake delay before
any autonomous motion.

Mandatory physical guard/barrier for autonomous or high-speed trials; a nominal
speed percentage is not a safety argument. Clamp/bolt the base to the test bench.
Use only the qualified soft foam ball mass/speed envelope. The specified end effector
is a three-finger claw; its closure is a separate pinch hazard. No net/funnel
substitute, throwing or automatic closure is authorized by a protocol latch bit.

## Fault behavior and software limits

- Startup, brownout, reset, reconnect and fault clear must remain disabled until
  referencing, sensor checks and deliberate enable are complete.
- E-stop, unexpected travel switch, lost/stale encoder, driver fault, measured current
  violation, loop deadline, host timeout, setpoint timeout or invalid command requires
  latched disarm. No automatically resumed cached trajectory.
- Firmware checks NC extension contacts. Both asserted simultaneously is invalid;
  an asserted travel switch during motion faults. Homing requires separate bounded
  seek/backoff/re-approach logic; it is deliberately not faked in this release.
- A 2 ms loop-overrun diagnostic detects a recovered stall. It **cannot** act during
  a permanent MCU stall. Independent watchdog/driver timeout and reset-safe enable
  gating remain hardware implementation gates.
- Proposed commissioning caps are 20 degrees/s for yaw/pitch and 150 mm/s extension.
  Start below these after qualification. Acceleration/jerk, travel, following error,
  feedback age, current and stopping margins must be enforced in the future real
  actuator adapter; the diagnostic scaffold does not execute a trajectory.
- Host freshness is based on local arrival of valid, new sequence packets, not on
  incomparable host/MCU clocks. A distinct 50 ms setpoint deadline prevents NOP
  heartbeats from keeping stale motion alive; this path cannot yet be hardware tested.
- The disabled qualification lock is intentional. Removing its bit without implementing
  and testing the missing adapters is not a completed fix.

## Release tests and measurable pass conditions

1. **Logic-only fault injection:** no motor bus connected. Boot, enable, clear, home,
   trajectory, claw field, malformed CRC, dropped bytes, overflow, replay and reconnect
   must never remove the qualification lock. Match host and C++ golden frames.
2. **Stop-chain bench:** use a dummy load first; scope E-stop, contactor, driver enable,
   bus voltage and brake signal. Record contactor drop time, voltage decay, reclose
   inhibition and broken wire behavior. No re-energization on E-stop release alone.
3. **Gravity hold:** support the arm independently. Test maximum extension and worst
   pitch with power removed, failed enable and simulated drive fault. No uncontrolled
   fall/sliding; verify secondary restraint and brake separately.
4. **Single-axis commissioning:** detached or safely restrained mechanism, current
   limited supply, guards. Verify direction, encoder sign, absolute reference, startup
   offset, both switches, disconnection, frozen feedback, impossible velocity, current
   trip and obstruction. Set current/following-error thresholds from these measurements.
5. **Timing:** scope the 1 kHz scheduler over at least 10 minutes under saturated USB,
   telemetry backpressure and encoder/driver load. Log worst execution/jitter and
   overrun count. Inject firmware hang and host unplug; independent stop must occur
   inside the measured safe-stop allowance. USB CDC baud is not timing assurance.
6. **Motion envelope:** validate deceleration distance at each reach and load, including
   actuator saturation, braking lag, compliance, gravity and sensor uncertainty. Keep
   software limits inward of physical switches/stops by this measured margin.
7. **Three-finger claw:** quantify closure latency under load, aperture versus measured
   actuator position, finger force, cable stretch/hysteresis, missed closure, obstruction
   current and retained-ball sensing. Loss of power must not launch an object.
   No catch/throw integration before guarded drop and low-speed catch trials.

High-priority design work still required: a reviewed wiring schematic and exact
parts, brake/restraint attachment and failure load path, independent watchdog/enable
circuit, true encoder/current/driver adapters, bounded homing, qualified motion
profiles and claw actuation. These are design/implementation gaps, not merely
unknown physical coefficients. Friction, thermal limits, repeatability, stop delay,
vibration and impact absorption then require physical measurement.
