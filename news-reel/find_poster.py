#!/usr/bin/env python3
"""Find the blank poster / frame a scene image reserved for our headline (maxi-photo look).

  python3 news-reel/find_poster.py scene.png [--seed X,Y]  ->  {"poster": [x, y, w, h]} in 1080x1920 frame coords

Flood-fills from the seed (default: image centre, 40% height) over near-identical pixels and returns the
bounding box, shrunk by a small margin. Check it by eye: Read the image, and re-run with another --seed
(in 1080x1920 coords) if the box is wrong.
"""
import argparse, json
from PIL import Image, ImageDraw
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--seed'); a = ap.parse_args()
im = Image.open(a.src).convert('RGB'); W, H = im.size; s = 1080 / W
sx, sy = (map(float, a.seed.split(',')) if a.seed else (540, 1920 * .4))
im2 = im.copy(); ImageDraw.floodfill(im2, (int(sx / s), int(sy / s)), (255, 0, 255), thresh=28)
px = im2.load(); xs, ys = [], []
for y in range(0, H, 2):
    for x in range(0, W, 2):
        if px[x, y] == (255, 0, 255): xs.append(x); ys.append(y)
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys); m = .04 * (x1 - x0)
box = [round((x0 + m) * s), round((y0 + m) * s), round((x1 - x0 - 2 * m) * s), round((y1 - y0 - 2 * m) * s)]
print(json.dumps({'poster': box, 'area_frac': round((x1 - x0) * (y1 - y0) / (W * H), 3)}))
