#!/usr/bin/env python3
"""Cut a storyboard sheet into single shots (user rule 2026-10-24: one image call per 12 shots).

The sheet is one gen_image.py --kind board image (3840x2160): a grid of 9:16 panels (default 6 columns x 2
rows) on black gutters. Gutters are found from the image itself (dark rows/columns); if that fails the grid is
split evenly. Each panel is trimmed of gutter edges, centre-cropped to 9:16 and upscaled to 1080x1920
(Lanczos + light unsharp) as <out>/<name>.png, in reading order left→right, top→bottom.

  python3 news-reel/storyboard_cut.py board.png --out work/story/raw --names s01,s02,... [--cols 6 --rows 2]
"""
import argparse, json
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat


def runs(profile, dark, min_len):
    """[(start, end)] of consecutive indices whose value is below `dark`."""
    out, s = [], None
    for i, v in enumerate(profile + [255]):
        if v < dark and s is None:
            s = i
        elif v >= dark and s is not None:
            if i - s >= min_len:
                out.append((s, i))
            s = None
    return out


def split(profile, n, size, dark=24):
    """n panel spans [(a, b)] along one axis, from the dark gutters, or an even split."""
    g = runs(profile, dark, max(2, size // 600))
    spans, prev = [], 0
    for a, b in g:
        if a - prev > size / n * .5:
            spans.append((prev, a))
        prev = b
    if size - prev > size / n * .5:
        spans.append((prev, size))
    if len(spans) == n:
        return spans, 'gutters'
    w = size / n
    return [(round(i * w), round((i + 1) * w)) for i in range(n)], 'even'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('sheet'); ap.add_argument('--out', required=True); ap.add_argument('--names', required=True)
    ap.add_argument('--cols', type=int, default=6); ap.add_argument('--rows', type=int, default=2)
    ap.add_argument('--size', default='1080x1920')
    a = ap.parse_args()
    im = Image.open(a.sheet).convert('RGB'); W, H = im.size
    g = im.convert('L')
    colp = list(g.resize((W, 1)).tobytes())                         # mean of each column
    rowp = list(g.resize((1, H)).tobytes())                         # mean of each row
    xs, mx = split(colp, a.cols, W); ys, my = split(rowp, a.rows, H)
    names = a.names.split(','); tw, th = map(int, a.size.split('x'))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    report = {'sheet': a.sheet, 'size': [W, H], 'split': [mx, my], 'panels': []}
    k = 0
    for y0, y1 in ys:
        for x0, x1 in xs:
            if k >= len(names):
                break
            p = im.crop((x0, y0, x1, y1))
            # trim leftover dark edge lines, then centre-crop to the target ratio
            bb = p.convert('L').point(lambda v: 255 if v > 24 else 0).getbbox() or (0, 0, *p.size)
            p = p.crop(bb); pw, ph = p.size; r = tw / th
            if pw / ph > r:
                nw = round(ph * r); p = p.crop(((pw - nw) // 2, 0, (pw - nw) // 2 + nw, ph))
            else:
                nh = round(pw / r); p = p.crop((0, (ph - nh) // 2, pw, (ph - nh) // 2 + nh))
            src = p.size
            p = p.resize((tw, th), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.6, percent=60, threshold=2))
            f = out / f'{names[k]}.png'; p.save(f)
            report['panels'].append({'name': names[k], 'source_px': list(src), 'upscale': round(th / src[1], 2), 'file': str(f)})
            k += 1
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
