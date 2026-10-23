#!/usr/bin/env python3
"""Check that a new reel cover or post slide 1 looks different from the page's recent grid (user rule 2026-10-23).

  python3 meshkani-pro/scripts/grid_check.py --new work/story/cover.jpg --prev prev/*.jpg [--crop45]
  -> prints a JSON report and a contact sheet <new>_vs_grid.jpg; exit 0 = different enough, 3 = too similar

For each image: 5 dominant colours (k-means in Lab), mean lightness, light/dark key and a coarse 4x5 layout map
(where the bright, dark and saturated masses sit). Too similar = the palette distance to a previous image is below
the threshold, or palette AND layout are both close, or the same light/dark key as each of the last 2 items.
--crop45 compares the 4:5 grid crop that Instagram shows on the profile.
"""
import argparse, json, sys
from pathlib import Path
import numpy as np
from PIL import Image


def lab(rgb):
    c = rgb / 255.0
    c = np.where(c > .04045, ((c + .055) / 1.055) ** 2.4, c / 12.92)
    xyz = c @ np.array([[.4124, .3576, .1805], [.2126, .7152, .0722], [.0193, .1192, .9505]]).T
    xyz /= np.array([.95047, 1., 1.08883])
    f = np.where(xyz > .008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def profile(path, crop45):
    im = Image.open(path).convert('RGB')
    if crop45:
        w, h = im.size; th = int(w * 5 / 4)
        if h > th: top = (h - th) // 2; im = im.crop((0, top, w, top + th))
    small = np.asarray(im.resize((80, 100))).reshape(-1, 3).astype(float)
    L = lab(small)
    rng = np.random.default_rng(7); cent = L[rng.choice(len(L), 5, replace=False)]
    for _ in range(12):
        d = ((L[:, None] - cent[None]) ** 2).sum(-1); a = d.argmin(1)
        cent = np.array([L[a == k].mean(0) if (a == k).any() else cent[k] for k in range(5)])
    w = np.bincount(a, minlength=5) / len(a)
    grid = np.asarray(im.resize((4, 5))).astype(float)
    g = lab(grid.reshape(-1, 3))
    chroma = np.hypot(g[:, 1], g[:, 2])
    return {'pal': cent, 'w': w, 'light': float(L[:, 0].mean()), 'layout': np.concatenate([g[:, 0] / 100, chroma / 100])}


def pal_dist(p, q):
    # weighted average of each colour's distance to the nearest colour in the other palette (symmetric, ΔE)
    d = np.sqrt(((p['pal'][:, None] - q['pal'][None]) ** 2).sum(-1))
    return float((d.min(1) * p['w']).sum() / 2 + (d.min(0) * q['w']).sum() / 2)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--new', required=True); ap.add_argument('--prev', nargs='+', default=[])
    ap.add_argument('--crop45', action='store_true'); ap.add_argument('--min-pal', type=float, default=18.0)
    a = ap.parse_args()
    N = profile(a.new, a.crop45); rows, bad = [], []
    for i, f in enumerate(a.prev):
        P = profile(f, a.crop45)
        pd, ld = pal_dist(N, P), float(np.abs(N['layout'] - P['layout']).mean())
        same_key = (N['light'] < 45) == (P['light'] < 45)
        r = {'prev': Path(f).name, 'palette_dE': round(pd, 1), 'layout_diff': round(ld, 3), 'same_light_key': same_key}
        if pd < a.min_pal: r['why'] = 'palette too close'
        elif pd < a.min_pal * 1.6 and ld < .08: r['why'] = 'palette and layout both close'
        if 'why' in r: bad.append(r)
        rows.append(r)
    if len(a.prev) >= 2 and all(r['same_light_key'] for r in rows[:2]):
        bad.append({'prev': 'last 2', 'why': 'same light/dark key as the last two items — alternate the grid rhythm'})
    rep = {'new': a.new, 'light': round(N['light'], 1), 'palette_lab': np.round(N['pal'], 1).tolist(), 'compared': rows, 'too_similar': bad, 'ok': not bad}
    # contact sheet: new first, then the previous items
    ims = [Image.open(p).convert('RGB') for p in [a.new] + a.prev]
    th = [im.resize((216, int(216 * im.height / im.width))) for im in ims]
    H = max(t.height for t in th); sheet = Image.new('RGB', (216 * len(th) + 8 * (len(th) - 1), H), 'white')
    for i, t in enumerate(th): sheet.paste(t, (i * 224, 0))
    out = Path(a.new).with_name(Path(a.new).stem + '_vs_grid.jpg'); sheet.save(out, quality=85); rep['sheet'] = str(out)
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    sys.exit(0 if rep['ok'] else 3)


if __name__ == '__main__':
    main()
