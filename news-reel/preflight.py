#!/usr/bin/env python3
"""Cheap pre-render check of the cover and the first 2 seconds (user rule 2026-10-27).

Mahdi: «چرا هی میره تو گیت رد میشه… پرامپتش رو دیگه هم سفت و سفت‌تر کن که رد نشه، چون برای هر دفعه هی باید
اون بره اکس جنریت کنه و کلی بر ما هزینه داره». REEL-011/012/013/014 failed the critic on cover, headline or hook
only after a full render (≈ 25 min) and new images. This step judges those three things on stills first.

  node news-reel/reel_render.mjs --dir=work/story --page=<engine> --mode=stills --t=0,0.5,1,1.9
  python3 news-reel/preflight.py --dir work/story sheet      # → work/story/preflight.jpg for the critic
  (independent critic writes work/story/critic_preflight.json {"scores":{cover_stop_power, headline_clarity, hook}, "notes":{…}})
  python3 news-reel/preflight.py --dir work/story check      # exit 0 = pass (every score ≥ 8), 3 = fix and repeat

The bar is 8, one above the final gate's 7, so the full render does not fail on these three scores later.
"""
import argparse, json, subprocess, sys
from pathlib import Path

NEED = ('cover_stop_power', 'headline_clarity', 'hook')
BAR = 8
TS = ('0.00', '0.50', '1.00', '1.90')


def sheet(d):
    files = [d / 'cover.jpg'] + [d / 'out' / f'still_{t}.jpg' for t in TS]
    miss = [str(f) for f in files if not f.exists()]
    if miss:
        sys.exit('missing: ' + ', '.join(miss) + ' (render the cover and the stills at t=0,0.5,1,1.9 first)')
    ins = sum((['-i', str(f)] for f in files), [])
    flt = ''.join(f'[{i}]scale=540:960,setsar=1[s{i}];' for i in range(len(files))) + ''.join(f'[s{i}]' for i in range(len(files))) + f'hstack={len(files)}'
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *ins, '-filter_complex', flt, str(d / 'preflight.jpg')], check=True)
    print(d / 'preflight.jpg', '(cover, then the reel at 0 / 0.5 / 1 / 1.9 s)')


def check(d):
    p = d / 'critic_preflight.json'
    if not p.exists():
        sys.exit('no critic_preflight.json: run the independent critic on preflight.jpg first')
    sc = json.loads(p.read_text()).get('scores', {})
    low = {k: sc.get(k) for k in NEED if (sc.get(k) or 0) < BAR}
    rounds = json.loads((d / 'preflight.json').read_text()).get('rounds', 0) + 1 if (d / 'preflight.json').exists() else 1
    out = {'pass': not low, 'scores': {k: sc.get(k) for k in NEED}, 'low': low, 'rounds': rounds}
    (d / 'preflight.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0 if not low else 3)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('cmd', choices=['sheet', 'check'])
    a = ap.parse_args()
    (sheet if a.cmd == 'sheet' else check)(Path(a.dir))
