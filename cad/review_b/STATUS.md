# Review B — full assembly and separate telescope study

VariableReachArm_Full_RevB.FCStd contains the base, yaw drive/support, pitch yoke,
external trunnion connections, telescope and three-claw grabber. Original CAD is
preserved separately. No net is part of the current design.

Telescope_0/250/500mm files isolate the telescope for inspection; the fourth file
shows closed claws. They are not the entire robot. Exporting these studies restores
the previous full active document. Bare trunnions in isolated studies are packaging
envelopes; the full assembly uses external stubs, hubs, bearings and clamp rails.

Guides now include nominal recessed screws, nuts and service access. The servo
allowance has a separate cradle and retention straps, pending the actual owned
servo model. Shape checks do not qualify fits or printed structural strength.

Only print_manifest.json lists current unpowered fit-prototype STLs. Hole sizes
need printer/material coupons. Obsolete hoop and backup studies are archived under
superseded/ and are not current deliverables.

NOT RELEASED: full swept workspace (rear boom collides at high pitch), telescope
belt anchorage/tensioner/stops, claw tendon/spring actuation, qualified motors and
brake, complete hardware retention, wiring and protective circuits. A neutral
assembly free of detected overlaps is not proof of manufacturability or safe motion.

## 8 September continuation

Current full baseline is the 850 mm raised/windowed stiffened shoulder, with 381 modeled parts. Five sampled final poses pass the broad solid-intersection screen; the unqualified workspace gate remains because sampling does not prove continuous or cable clearance. New telescope drive details and claw actuation documents distinguish implemented geometry from unresolved supplier/servo interfaces. Both full-CAD GIFs have been regenerated.

The user now accepts lower performance and more printing for a college V1 before a fair version. `docs/college_v1_plan.md` and `engineering/bom_college_v1.csv` define a separate compact concept and cost basket; this does not change the current full CAD or enable powered motion. Current costs with allowances: V1 $705.64, restrained rig $497.29, full machine $1457.12.
