#!/usr/bin/env python3
"""Real photo -> line drawing SVG for the line engine (`lineart` visual, drawn on stroke by stroke).

  python3 news-reel/lineart.py in.jpg out.svg [--width 900] [--detail 1.0]

Difference-of-Gaussians edges (keeps contours, drops flat areas), cleaned and traced to vector paths with
potrace (node, logo-motion/node_modules). Use real photos only (Wikimedia / press kits, credited); never a
generated likeness of a real person.
"""
import argparse, subprocess, sys
from pathlib import Path
from PIL import Image, ImageFilter, ImageOps, ImageChops

HERE = Path(__file__).resolve().parent
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--width', type=int, default=900); ap.add_argument('--detail', type=float, default=1.0)
a = ap.parse_args()
im = Image.open(a.src).convert('L'); im = im.resize((a.width, round(im.height * a.width / im.width)), Image.LANCZOS)
im = ImageOps.autocontrast(im, cutoff=1)
d = ImageChops.subtract(im.filter(ImageFilter.GaussianBlur(4.0 / a.detail)), im.filter(ImageFilter.GaussianBlur(1.0)), scale=1, offset=0)
d = ImageOps.autocontrast(d, cutoff=2)
bw = d.point(lambda v: 0 if v > 70 else 255).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.MaxFilter(3))   # black lines on white
tmp = Path(a.out).with_suffix('.edges.png'); bw.save(tmp)
subprocess.run(['node', '-e', f'''
const p=require("{HERE.parent}/logo-motion/node_modules/potrace");
p.trace("{tmp}",{{turdSize:40,optTolerance:.6,threshold:128,blackOnWhite:true}},(e,svg)=>{{if(e)throw e;require("fs").writeFileSync("{a.out}",svg);}});'''], check=True)
# one <path> per contour, so the engine can draw them on one after another (top to bottom)
import re
svg = Path(a.out).read_text(); head = re.search(r'<svg[^>]*>', svg).group(0)
subs = [m for d in re.findall(r' d="([^"]+)"', svg) for m in re.split(r'(?=M )', d) if m.strip()]
def top(m): n = re.findall(r'[-\d.]+', m); return float(n[1]) if len(n) > 1 else 0
subs.sort(key=top)
Path(a.out).write_text(head + ''.join(f'<path d="{m.strip()}"/>' for m in subs) + '</svg>')
print(a.out, len(subs), 'contours')
