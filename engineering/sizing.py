"""Compatibility entry point: Rev B is the only supported sizing model.

Run ``python engineering/sizing.py`` or ``python -m engineering.review_sizing``.
Legacy holding-torque approvals and arbitrary counterbalance credits were removed.
"""
from pathlib import Path
import sys

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from engineering.review_sizing import main, run_all

if __name__ == "__main__":
    main()
