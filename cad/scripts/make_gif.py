#!/usr/bin/env python3
"""Make captioned, fixed-scale GIFs from current full-CAD animation frames."""
from pathlib import Path
import argparse
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]


def make_gif(frame_dir, output, fps=12, scale=1):
    if fps<=0 or scale<=0: raise ValueError('fps and scale must be positive')
    frame_dir=Path(frame_dir)
    metadata=json.loads((frame_dir/'metadata.json').read_text(encoding='utf-8'))
    images=[]
    def load_font(size):
        for candidate in ('C:/Windows/Fonts/arial.ttf', 'DejaVuSans.ttf'):
            try: return ImageFont.truetype(candidate,size)
            except OSError: pass
        return ImageFont.load_default(size=size)
    font=load_font(17)
    small=load_font(14)
    for row in metadata['frames']:
        with Image.open(frame_dir/row['file']) as source:
            raw=source.convert('RGB')
        if scale!=1:
            raw=raw.resize((round(raw.width*scale),round(raw.height*scale)),Image.Resampling.LANCZOS)
        canvas=Image.new('RGB',(raw.width,raw.height+88),'white')
        canvas.paste(raw,(0,88))
        draw=ImageDraw.Draw(canvas)
        draw.rectangle((0,0,raw.width,88),fill='#152735')
        draw.text((16,9),'VARIABLE REACH ARM | Full CAD clearance prototype',fill='white',font=font)
        draw.text((16,33),'Kinematic demonstration — not measured speed or demonstrated catching',fill='#ffd48d',font=small)
        draw.text((16,56),f"Yaw {row['yaw_deg']:+.0f}°   Pitch {row['pitch_deg']:+.0f}°   Extension {row['extension_mm']:.0f} mm   |   {metadata['pivot_height_mm']:.0f} mm raised shoulder study",fill='white',font=small)
        images.append(canvas.quantize(colors=192,method=Image.Quantize.MEDIANCUT))
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    images[0].save(output,save_all=True,append_images=images[1:],duration=round(1000/fps),loop=0,disposal=2,optimize=False)
    with Image.open(output) as check:
        assert check.n_frames>=2
        dimensions=check.size
    return dict(path=str(output),frames=len(images),size=dimensions,fps=fps,bytes=output.stat().st_size)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--frames',type=Path,default=ROOT/'cad/animations/frames')
    parser.add_argument('--out',type=Path,default=ROOT/'cad/animations/arm_motion.gif')
    parser.add_argument('--fps',type=float,default=12)
    parser.add_argument('--scale',type=float,default=1)
    args=parser.parse_args()
    print(json.dumps(make_gif(args.frames,args.out,args.fps,args.scale),indent=2))


if __name__=='__main__':main()

