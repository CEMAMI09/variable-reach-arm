# Variable-Reach Dynamic Catching Arm

Stationary **3-DOF** manipulator with a **telescoping boom** that changes reach during interception of lightweight foam balls.

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
- `engineering/bom.csv` — bill of materials (~$449 + reserve)
- `engineering/selections.md` — why each part

## CAD

- FreeCAD assembly: `cad/freecad/VariableReachArm.FCStd`
- Parametric build: `cad/scripts/build_arm.py`
- **Printable STLs:** `cad/stl/` (regenerate via `cad/scripts/export_printables.py`)
- **Print / buy cut-list:** [`cad/drawings/print_guide.md`](cad/drawings/print_guide.md)
- Animations: `cad/animations/`

## Status

Milestone 0 deliverables: requirements, architecture, calculations, BOM, selections, CAD seed, firmware/host skeletons, simulation, test/bring-up docs.
