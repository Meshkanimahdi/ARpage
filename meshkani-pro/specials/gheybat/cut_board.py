#!/usr/bin/env python3
"""Cut a 6 x 2 storyboard board into twelve 1080x1920 panels by finding its black gutters.

  python3 cut_board.py work/gheybat/sbD_raw.png D work/gheybat/panels      -> panels/D1.jpg … D12.jpg
"""
import sys
import numpy as np
from PIL import Image

src, prefix, out = sys.argv[1], sys.argv[2], sys.argv[3]
im = Image.open(src).convert('RGB'); a = np.asarray(im, np.float32).mean(axis=2); H, W = a.shape

def runs(profile, lo, hi, want):
    """dark runs (gutters) inside [lo, hi): return the `want` widest, as (start, end), sorted"""
    dark = profile < 22; rs, s = [], None
    for i in range(lo, hi):
        if dark[i] and s is None: s = i
        if not dark[i] and s is not None: rs.append((s, i)); s = None
    if s is not None: rs.append((s, hi))
    rs = [r for r in rs if r[1] - r[0] >= 3]
    return sorted(sorted(rs, key=lambda r: r[1] - r[0], reverse=True)[:want])

rowgut = runs(a.mean(axis=1), int(H * 0.35), int(H * 0.65), 1)
mid = (rowgut[0][0] + rowgut[0][1]) // 2 if rowgut else H // 2
rows = [(0, mid), (mid, H)]
n = 0
for y0, y1 in rows:
    band = a[y0:y1]; prof = band.mean(axis=0)
    g = runs(prof, int(W * 0.08), int(W * 0.92), 5)
    if len(g) < 5:                                   # fall back to equal columns
        g = [(int(W * k / 6) - 2, int(W * k / 6) + 2) for k in range(1, 6)]
    edges = [0] + [x for r in g for x in r] + [W]
    for k in range(6):
        x0, x1 = edges[2 * k], edges[2 * k + 1]
        # trim gutter rows/cols at the panel border
        p = a[y0:y1, x0:x1]; ys = np.where(p.mean(axis=1) > 22)[0]; xs = np.where(p.mean(axis=0) > 22)[0]
        cy0, cy1 = y0 + ys.min(), y0 + ys.max() + 1; cx0, cx1 = x0 + xs.min(), x0 + xs.max() + 1
        w, h = cx1 - cx0, cy1 - cy0
        if w / h > 9 / 16: nw = int(h * 9 / 16); cx0 += (w - nw) // 2; cx1 = cx0 + nw
        else: nh = int(w * 16 / 9); cy0 += (h - nh) // 2; cy1 = cy0 + nh
        n += 1
        im.crop((cx0, cy0, cx1, cy1)).resize((1080, 1920), Image.LANCZOS).save(f"{out}/{prefix}{n}.jpg", quality=92)
        print(f"{prefix}{n}: {cx1 - cx0}x{cy1 - cy0} from x {cx0}-{cx1}, y {cy0}-{cy1}")
