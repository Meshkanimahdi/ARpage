#!/usr/bin/env python3
"""Attention QA gate for a finished reel (user rule 2026-10-24, after REEL-007).

Checks what the audio/spec QA never saw: empty screens, frozen pictures, slow shot rhythm, a weak first
two seconds and the length. It also writes a 1-frame-per-second contact sheet that must be Read before
publishing (cropped elements, cut-off text and visuals that do not match the narration are judged there).

  python3 news-reel/reel_qa.py work/story/reel.mp4 [--out work/story/qa] [--min 40 --max 55]

Exit 0 = pass, 3 = fail (reasons in qa.json and on stdout).
"""
import argparse, json, re, subprocess, sys
from pathlib import Path

from PIL import Image, ImageStat

W, H = 108, 192          # analysis size (1/10 of 1080x1920)
BLOCK = 6                # 6x6 blocks at analysis size = 60x60 px on the real frame


def frames(video, fps, out_dir, size):
    out_dir.mkdir(parents=True, exist_ok=True)
    for f in out_dir.glob('f_*.png'):
        f.unlink()
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(video), '-vf', f'fps={fps},scale={size[0]}:{size[1]}',
                    str(out_dir / 'f_%04d.png')], check=True)
    return sorted(out_dir.glob('f_*.png'))


def flat_ratio(img):
    """Share of the frame made of flat, featureless blocks (empty canvas, plain fills)."""
    g = img.convert('L')
    flat = total = 0
    for y in range(0, H - BLOCK + 1, BLOCK):
        for x in range(0, W - BLOCK + 1, BLOCK):
            s = ImageStat.Stat(g.crop((x, y, x + BLOCK, y + BLOCK))).stddev[0]
            total += 1
            flat += s < 3.0
    return flat / total


def _absdiff(a, b):
    from PIL import ImageChops
    return ImageStat.Stat(ImageChops.difference(a.convert('L'), b.convert('L'))).mean[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('video')
    ap.add_argument('--out')
    ap.add_argument('--min', type=float, default=40)
    ap.add_argument('--max', type=float, default=55)
    ap.add_argument('--max-flat', type=float, default=0.45, help='max mean flat share over the reel')
    ap.add_argument('--max-flat-frames', type=float, default=0.15, help='max share of seconds that are >60%% flat')
    ap.add_argument('--max-hold', type=float, default=1.5, help='longest allowed still stretch, seconds')
    ap.add_argument('--max-shot', type=float, default=3.5, help='max mean shot length, seconds')
    ap.add_argument('--layout', choices=['photo', 'designed'], default='photo',
                    help='designed = typography/UI/editorial on plain grounds: relaxes only the flat-area limits')
    a = ap.parse_args()
    if a.layout == 'designed':
        a.max_flat, a.max_flat_frames = max(a.max_flat, .72), max(a.max_flat_frames, .45)

    video = Path(a.video)
    out = Path(a.out) if a.out else video.parent / 'qa'
    dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(video)],
                               capture_output=True, text=True, check=True).stdout)
    fails, report = [], {'duration_s': round(dur, 2)}

    if not (a.min <= dur <= a.max):
        fails.append(f'length {dur:.1f}s outside {a.min:.0f}-{a.max:.0f}s')

    # 1. empty screens, measured at 2 fps
    fr = frames(video, 2, out / 'a', (W, H))
    flats = [flat_ratio(Image.open(p)) for p in fr]
    mean_flat = sum(flats) / len(flats)
    very_flat = sum(f > 0.60 for f in flats) / len(flats)
    report.update(mean_flat=round(mean_flat, 3), very_flat_share=round(very_flat, 3),
                  flat_by_second=[round(max(flats[i:i + 2]), 2) for i in range(0, len(flats), 2)])
    if mean_flat > a.max_flat:
        fails.append(f'empty screen: mean flat share {mean_flat:.2f} > {a.max_flat}')
    if very_flat > a.max_flat_frames:
        bad = [i // 2 for i, f in enumerate(flats) if f > 0.60]
        fails.append(f'{very_flat:.0%} of the reel is >60% empty (seconds {sorted(set(bad))[:12]})')

    # 2. frozen picture and 3. shot rhythm, measured at 10 fps
    fr10 = frames(video, 10, out / 'b', (W, H))
    imgs = [Image.open(p) for p in fr10]
    d = [_absdiff(imgs[i], imgs[i + 1]) for i in range(len(imgs) - 1)]
    longest, run, holds = 0.0, 0, []
    for i, v in enumerate(d):
        if v < 0.35:
            run += 1
        else:
            if run / 10 > a.max_hold:
                holds.append((round((i - run) / 10, 1), round(run / 10, 1)))
            longest, run = max(longest, run / 10), 0
    if run / 10 > a.max_hold and (len(d) - run) / 10 < dur - 2.2:      # a final CTA hold of ≤ 2 s is allowed
        holds.append((round((len(d) - run) / 10, 1), round(run / 10, 1)))
    longest = max(longest, run / 10)
    cuts = [i / 10 for i, v in enumerate(d) if v > 18]
    merged = []
    for c in cuts:
        if not merged or c - merged[-1] > 0.4:
            merged.append(c)
    mean_shot = dur / (len(merged) + 1)
    report.update(holds=holds, longest_still_s=longest, cuts=len(merged), mean_shot_s=round(mean_shot, 2))
    if holds:
        fails.append(f'frozen picture: {holds[:6]} (start s, length s) > {a.max_hold}s')
    if mean_shot > a.max_shot:
        fails.append(f'slow rhythm: mean shot {mean_shot:.1f}s > {a.max_shot}s ({len(merged)} cuts)')

    # 4. hook: the first 2 s must be a full picture and must move
    hook_flat = max(flats[:4]) if flats else 1
    hook_motion = sum(d[:20]) / max(1, len(d[:20]))
    report.update(hook_flat=round(hook_flat, 2), hook_motion=round(hook_motion, 2))
    if hook_flat > (0.72 if a.layout == 'designed' else 0.45):
        fails.append(f'weak hook: first 2 s are {hook_flat:.0%} empty')
    if hook_motion < 0.8:
        fails.append(f'weak hook: almost no motion in the first 2 s ({hook_motion:.2f})')

    # contact sheet, 1 frame per second, for the visual read
    n = int(dur)
    cols = 8
    rows = (n + cols - 1) // cols
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(video), '-vf',
                    f'fps=1,scale=180:-1,drawtext=text=%{{n}}:x=6:y=6:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.6,tile={cols}x{rows}',
                    '-frames:v', '1', str(out / 'contact.jpg')], check=False)
    if not (out / 'contact.jpg').exists():
        subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(video), '-vf', f'fps=1,scale=180:-1,tile={cols}x{rows}',
                        '-frames:v', '1', str(out / 'contact.jpg')], check=True)

    report['fails'] = fails
    report['pass'] = not fails
    (out / 'qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != 'flat_by_second'}, ensure_ascii=False))
    print('contact sheet:', out / 'contact.jpg', '(Read it: cropped elements, cut text, picture vs. narration)')
    sys.exit(0 if not fails else 3)


if __name__ == '__main__':
    main()
