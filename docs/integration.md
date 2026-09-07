# Integration Procedure

## Mechanical

1. Base leveled; column plumb.
2. Yaw bearing preload: free rotation, minimal play.
3. Pitch shaft alignment; boom clamps torque-limited (protect CF).
4. Extension belt tension; verify active retract.
5. Catcher + IR beam alignment; latch open/close.
6. Cable service loops for full yaw/pitch/extend.

## Electrical

1. Star ground at base; e-stop wired NC.
2. Motor phases / encoder maps documented in `data/calibration/wiring.md`.
3. Catch sensor, limits, latch on MCU pins per `firmware/include/config.h`.

## Software integration sequence

Follow control development order in requirements §30 / firmware header comment.

1. Manual low-speed  
2. Homing  
3. Position control  
4. Velocity measurement  
5. Accel-limited moves  
6. Multi-axis  
7. Trajectory tracking  
8. Dynamic extension  
9. Vision positioning  
10. Interception  
11. Velocity-matched catch  
12. Throwing  

## Defining demo checklist

- [ ] Case A: catch at ~700 mm without extend  
- [ ] Case B: predict `L_req > L_normal`, extend, catch  
- [ ] Case C (stretch): catch → throw  

## Go / no-go

No autonomous catch attempts until: e-stop proven, soft caps on, simulation planner checked, prediction error characterized, barrier optional in place.
