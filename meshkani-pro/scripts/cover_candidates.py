#!/usr/bin/env python3
"""Eight cover candidates from two 4-panel boards (RUNBOOK §00.23, user rule 2026-11-04).

  python3 meshkani-pro/scripts/cover_candidates.py --boards b1.png b2.png --out work/cover_x --cover-json cover.json
Crops every board into its 4 vertical panels (9:16 from the centre), renders news-reel/cover.html with the same
cover.json on each (bg swapped), and writes <out>/cover_candidates.jpg (4x2 contact sheet) plus <out>/cand_N/cover.jpg.
"""
import argparse, json, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent.parent.parent


def panels(board, n=4):
    im = Image.open(board).convert('RGB'); W, H = im.size; pw = W // n
    out = []
    for i in range(n):
        p = im.crop((i * pw, 0, (i + 1) * pw, H))
        # trim black gutters: shave 1.5 % each side, then crop to 9:16 from the centre
        w, h = p.size; m = int(w * 0.015); p = p.crop((m, 0, w - m, h)); w, h = p.size
        th = int(w * 16 / 9)
        if th <= h: y = (h - th) // 2; p = p.crop((0, y, w, y + th))
        else: tw = int(h * 9 / 16); x = (w - tw) // 2; p = p.crop((x, 0, x + tw, h))
        out.append(p.resize((1080, 1920), Image.LANCZOS))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--boards', nargs='+', required=True); ap.add_argument('--out', required=True); ap.add_argument('--cover-json', required=True)
    a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    cj = json.loads(Path(a.cover_json).read_text()); covers = []
    k = 0
    for b in a.boards:
        for p in panels(b):
            k += 1; d = out / f'cand_{k}'; d.mkdir(exist_ok=True)
            p.save(d / 'bg.jpg', quality=92); c = dict(cj); c['bg'] = 'bg.jpg'
            (d / 'cover.json').write_text(json.dumps(c, ensure_ascii=False))
            r = subprocess.run(['node', str(HERE / 'news-reel' / 'cover_render.mjs'), f'--dir={d}'], capture_output=True, text=True)
            if r.returncode != 0: print(f'cand_{k}:', (r.stdout + r.stderr)[-300:], file=sys.stderr)
            covers.append(d / 'cover.jpg')
    tw, th = 540, 960; cols = 4; rows = (len(covers) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12 + rows * 40), (18, 18, 18))
    dr = ImageDraw.Draw(sheet)
    try: font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
    except Exception: font = ImageFont.load_default()
    for i, c in enumerate(covers):
        if not c.exists(): continue
        x = 12 + (i % cols) * (tw + 12); y = 12 + (i // cols) * (th + 12 + 40)
        sheet.paste(Image.open(c).resize((tw, th), Image.LANCZOS), (x, y + 40)); dr.text((x + 8, y + 4), str(i + 1), fill=(255, 212, 0), font=font)
    sheet.save(out / 'cover_candidates.jpg', quality=90); print(out / 'cover_candidates.jpg', len(covers), 'candidates')


if __name__ == '__main__':
    main()
