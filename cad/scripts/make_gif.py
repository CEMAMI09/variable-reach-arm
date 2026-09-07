#!/usr/bin/env python3
"""Stitch FreeCAD PNG frames into an animated GIF."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--frames",
        default="/Users/user/Documents/chat/variable-reach-arm/cad/animations/frames",
    )
    ap.add_argument(
        "--out",
        default="/Users/user/Documents/chat/variable-reach-arm/cad/animations/arm_motion.gif",
    )
    ap.add_argument("--fps", type=float, default=12.0)
    ap.add_argument("--scale", type=float, default=0.75, help="Downscale for smaller GIF")
    args = ap.parse_args()

    frame_dir = Path(args.frames)
    files = sorted(frame_dir.glob("frame_*.png"))
    if not files:
        raise SystemExit(f"No frames in {frame_dir}")

    images = []
    for f in files:
        im = Image.open(f).convert("RGBA")
        if args.scale != 1.0:
            w = int(im.width * args.scale)
            h = int(im.height * args.scale)
            im = im.resize((w, h), Image.Resampling.LANCZOS)
        # GIF-friendly palette
        images.append(im.convert("P", palette=Image.Palette.ADAPTIVE, colors=256))

    duration = int(1000 / args.fps)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(
        out,
        save_all=True,
        append_images=images[1:],
        duration=duration,
        loop=0,
        optimize=True,
    )
    print(f"Wrote {out} ({len(images)} frames, {out.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    main()
