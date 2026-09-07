#!/usr/bin/env python3
"""Plot telemetry CSV columns. Usage: python3 tools/plot_run.py data/experiments/run.csv"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    path = Path(args.csv_path)
    rows = list(csv.DictReader(path.open()))
    if not rows:
        print("empty csv")
        return
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print(f"Loaded {len(rows)} rows. Install matplotlib to plot.")
        for k in ("yaw_pos", "ext_pos", "catch_result"):
            if k in rows[0]:
                print(k, "sample", rows[0][k])
        return

    t = [float(r["timestamp"] or 0) for r in rows]

    fig, axs = plt.subplots(3, 1, sharex=True, figsize=(10, 8))
    axs[0].plot(t, [float(r["yaw_pos"] or 0) for r in rows], label="yaw")
    axs[0].plot(t, [float(r["yaw_target"] or 0) for r in rows], "--", label="yaw_tgt")
    axs[0].legend()
    axs[0].set_ylabel("yaw")

    axs[1].plot(t, [float(r["pitch_pos"] or 0) for r in rows], label="pitch")
    axs[1].plot(t, [float(r["pitch_target"] or 0) for r in rows], "--")
    axs[1].legend()
    axs[1].set_ylabel("pitch")

    axs[2].plot(t, [float(r["ext_pos"] or 0) for r in rows], label="ext")
    axs[2].plot(t, [float(r["ext_target"] or 0) for r in rows], "--")
    axs[2].legend()
    axs[2].set_ylabel("extension")
    axs[2].set_xlabel("time")
    fig.suptitle(path.name)
    out = args.out or str(path.with_suffix(".png"))
    fig.savefig(out, dpi=120)
    print("wrote", out)


if __name__ == "__main__":
    main()
