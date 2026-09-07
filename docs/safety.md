# Safety

## Hard rules

1. Hardware e-stop **must** cut motor DC bus independent of software.
2. Foam balls only — never baseballs, metal, rocks, or hard projectiles.
3. No head/torso/hands in the sweep volume during autonomous high-speed motion.
4. Initial software velocity caps ≈ 40% of design targets.
5. Optional transparent barrier for high-speed autonomous tests.

## Required protections

| Protection | Implementation |
|------------|----------------|
| E-stop | NC mushroom → relay opens 24 V bus |
| Travel limits | Soft limits + extension hard stops + switches |
| Watchdog | MCU disables motion if loop stalls |
| Host timeout | FAULT if no packets within 200 ms when active |
| Overcurrent | Driver / firmware thresholds |
| Encoder fault | Invalid/missing feedback → FAULT |
| Homing | Low-speed only; verify sensors before arming |

## Fault latch

Any fault enters `FAULT` until e-stop released, cause cleared, and `CMD_CLEAR_FLT`. Log `fault_bits` every event.

## Test volume etiquette

Announce autonomous runs. Keep observers behind barrier. Power down for mechanical work.
