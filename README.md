# Variable-Reach Dynamic Catching Arm

Stationary **3-DOF** manipulator with a **telescoping boom** that changes reach during interception of lightweight foam balls.

> **Engineering review B (2026-09-07): NOT a manufacturing or powered-motion release.**
> The end effector is a **three-finger grabber; no net**. The original CAD, STL files,
> motor claims and $449 budget were conceptual and are superseded where noted below.
> Complete-machine ordering remains blocked. Firmware intentionally cannot arm until
> real drivers, feedback, homing and independent stop hardware are qualified.

Current review entry points:

- `engineering/sizing.py` and `engineering/design_parameters.json`: current SI model.
- `cad/scripts/build_review_telescope.py` and `claw_gripper.py`: current parametric study.
- `cad/review_b/`: actual FreeCAD studies, geometry checks and **unpowered fit-only** STLs.
- `docs/embedded_protocol.md`: matching v2 host/MCU protocol; replaces the old v1 layout.
- `docs/review_progress.md`: accepted user corrections and review continuity.
- `docs/safety.md` and `cad/drawings/print_guide.md`: current release restrictions.

Legacy `cad/freecad/VariableReachArm.FCStd`, `cad/stl/`, old STEP and animations are
retained as historical design evidence. Do not manufacture or infer physical performance
from them. A valid CAD solid and a successful animation do not establish load paths,
assembly feasibility, motor capacity or capture success.

## Quick start

```bash
# Engineering calculations
python3 engineering/sizing.py

# Host simulation (no hardware)
python3 -m simulation.run_demo

# Plot a telemetry CSV
python3 tools/plot_run.py data/experiments/example_run.csv
```

## Docs

| Doc | Content |
|-----|---------|
| [docs/requirements.md](docs/requirements.md) | Spec-derived requirements |
| [docs/architecture.md](docs/architecture.md) | Subsystems & protocol |
| [docs/safety.md](docs/safety.md) | Safety rules |
| [docs/calibration.md](docs/calibration.md) | Homing & camera calib |
| [docs/testing.md](docs/testing.md) | Test procedures |
| [docs/bringup.md](docs/bringup.md) | Bring-up order |
| [docs/integration.md](docs/integration.md) | Full integration |

## Engineering

- `engineering/calculations.md` — results & conflict resolutions
- `engineering/sizing.py` — reproducible sizing
- `engineering/bom.csv` — current itemized cost; original rows totaled $701 before reserve
- `engineering/selections.md` — why each part

## CAD

- FreeCAD assembly: `cad/freecad/VariableReachArm.FCStd`
- Parametric build: `cad/scripts/build_arm.py`
- **Printable STLs:** `cad/stl/` (regenerate via `cad/scripts/export_printables.py`)
- **Print / buy cut-list:** [`cad/drawings/print_guide.md`](cad/drawings/print_guide.md)
- Animations: `cad/animations/`

## Status

Engineering development: revised telescope/gripper studies, reproducible sizing and
protocol/planner tests. Full mechanical integration and powered hardware qualification
remain open; consult the engineering report before buying parts.
