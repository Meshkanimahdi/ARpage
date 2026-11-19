#!/usr/bin/env python3
"""30-second teaser for «پشت درهای بسته | قسمت اول», cut from the finished episode.

  python3 make_teaser.py --dir work/gheybat --cta work/gheybat/teaser/cta_1.mp3

Funniest beats in story order (episode clock), white flash cuts, two whooshes, a hit on the final «نه!», then a
call-to-action card («برای شنیدن کل داستان بیا تو پیج») with the narrator's voice. Output <dir>/out/gheybat_teaser.mp4.
"""
import argparse, math, os, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); ap.add_argument('--cta', required=True)
ap.add_argument('--off', type=float, default=6.28); A = ap.parse_args()
D = A.dir.rstrip('/') + '/'; OUT = D + 'out/'; TD = OUT + 'teaser/'; os.makedirs(TD, exist_ok=True)
SRC = OUT + 'gheybat_ep1.mp4'; SFX = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../news-reel/sfx/')
FB, FK = D + 'fonts/Vazirmatn-Bold.ttf', D + 'fonts/Vazirmatn-Black.ttf'
W, H, FPS = 1080, 1920, 30
CLIPS = [  # (episode start, end, note)
    (0.75, 7.75, 'table slam + «مشکانی، مشکانی، مشکانی! من دیگه نمیکشم»'),
    (28.55, 32.95, '«چون اون یه دونه آدم اسمش مهدیه. فدات شم»'),
    (280.70, 284.65, '«هفده تا! صف من از صف نونوایی بربری درازتر شده»'),
    (408.20, 416.60, '«خودش اخیراً میگه معمار تجربه» / «یعنی چی؟» / «…میترکونتش»'),
    (596.20, 602.60, '«وایسا ببینم / نکنه / یعنی ما الان- / دقیقاً همین کافه. همین گپ»'),
    (657.00, 657.95, '«نه!»'),
]
WHOOSH_INTO = {3, 4}          # clip indexes that open with a whoosh (max two)

def run(cmd): subprocess.run(cmd, check=True)
def rtl(d, xy, txt, f, fill, **kw): d.text(xy, txt, font=f, fill=fill, direction='rtl', language='fa', **kw)

# ---- top label shown over the clips
lab = Image.new('RGBA', (W, 220)); d = ImageDraw.Draw(lab); f = ImageFont.truetype(FK, 44)
txt = 'پشت درهای بسته | قسمت اول'; bb = d.textbbox((0, 0), txt, font=f, direction='rtl', language='fa'); tw = bb[2] - bb[0]
d.rounded_rectangle(((W - tw) // 2 - 40, 120, (W + tw) // 2 + 40, 200), radius=40, fill=(12, 10, 18, 200), outline=(255, 200, 70, 255), width=3)
rtl(d, ((W - tw) // 2 - bb[0], 160 - (bb[1] + bb[3]) // 2), txt, f, (255, 255, 255))
lab.save(TD + 'label.png')

# ---- clips
parts = []
for i, (a, b, _) in enumerate(CLIPS):
    p = TD + f'c{i}.mp4'; dur = b - a
    vf = "[1:v]format=rgba[l];[0:v][l]overlay=0:0" + (",fade=t=in:st=0:d=0.14:color=white" if i else "") + "[v]"
    af = f"[0:a]aresample=48000,afade=t=in:st=0:d=0.03,afade=t=out:st={dur - 0.06:.3f}:d=0.06[a]"
    run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{a + A.off:.3f}', '-t', f'{dur:.3f}', '-i', SRC, '-i', TD + 'label.png',
         '-filter_complex', vf + ';' + af, '-map', '[v]', '-map', '[a]', '-r', str(FPS), '-c:v', 'libx264', '-preset', 'medium', '-crf', '18',
         '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2', p])
    parts.append((p, dur))

# ---- CTA card (3.6 s): blurred last frame, 3D gold «بیا تو پیج», handle chip, glitter
last = CLIPS[-1][1] + A.off - 0.05
bgp = TD + 'bg.png'; run(['ffmpeg', '-y', '-loglevel', 'error', '-ss', f'{last:.3f}', '-i', SRC, '-frames:v', '1', bgp])
BG = np.asarray(Image.open(bgp).convert('RGB'))
def spring(t, k=7.0, w=14.0): return 0.0 if t <= 0 else 1 - math.exp(-k * t) * math.cos(w * t)
def text_img(txt, size, face, ext, depth, stroke=(20, 10, 0)):
    f = ImageFont.truetype(FK, size); dd = ImageDraw.Draw(Image.new('L', (8, 8)))
    bb = dd.textbbox((0, 0), txt, font=f, direction='rtl', language='fa'); tw, th = bb[2] - bb[0], bb[3] - bb[1]; pad = 40
    Wt, Ht = tw + 2 * pad + depth, th + 2 * pad + depth
    m = Image.new('L', (Wt, Ht)); rtl(ImageDraw.Draw(m), (pad - bb[0], pad - bb[1]), txt, f, 255, stroke_width=6, stroke_fill=255)
    fm = Image.new('L', (Wt, Ht)); rtl(ImageDraw.Draw(fm), (pad - bb[0], pad - bb[1]), txt, f, 255)
    out = Image.new('RGBA', (Wt, Ht))
    for k in range(depth, 0, -1): out.paste(Image.new('RGBA', (Wt, Ht), ext + (255,)), (k, k), m)
    out.paste(Image.new('RGBA', (Wt, Ht), stroke + (255,)), (0, 0), m)
    g = np.zeros((Ht, Wt, 3), np.uint8); ys = np.linspace(0, 1, Ht)
    for c in range(3): g[:, :, c] = np.interp(ys, [0, 0.5, 1], [face[0][c], face[1][c], face[2][c]])[:, None]
    out.paste(Image.fromarray(g).convert('RGBA'), (0, 0), fm)
    glow = out.split()[3].filter(ImageFilter.GaussianBlur(18))
    halo = Image.new('RGBA', (Wt, Ht), (255, 180, 60, 0)); halo.putalpha(glow.point(lambda v: int(v * 0.55)))
    res = Image.alpha_composite(halo, out); return res
L1 = text_img('برای شنیدن کل داستان', 84, ((255, 255, 255), (240, 240, 245), (200, 200, 215)), (60, 60, 80), 7, (20, 20, 30))
L2 = text_img('بیا تو پیج', 172, ((255, 246, 190), (255, 196, 40), (214, 120, 0)), (110, 55, 0), 14)
chip = Image.new('RGBA', (620, 130)); d = ImageDraw.Draw(chip)
d.rounded_rectangle((5, 5, 615, 125), radius=60, fill=(12, 10, 18, 225), outline=(255, 200, 70, 255), width=4)
d.text((310, 65), '@mahdi.meshkani', font=ImageFont.truetype(FB, 58), fill=(255, 210, 90), anchor='mm')
chip2 = Image.new('RGBA', (560, 96)); d = ImageDraw.Draw(chip2); f2 = ImageFont.truetype(FB, 42)
d.rounded_rectangle((4, 4, 556, 92), radius=46, fill=(255, 255, 255, 230))
rtl(d, (280, 48), 'قسمت کامل · ۱۱ دقیقه', f2, (20, 20, 30), anchor='mm')
MEGA = Image.open(D + 'fx/stickers/megaphone.png').convert('RGBA')
def paste(fr, im, cx, cy, sc=1.0, alpha=1.0, rot=0.0):
    if sc <= 0.02 or alpha <= 0.01: return
    im2 = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    if rot: im2 = im2.rotate(rot, resample=Image.BICUBIC, expand=True)
    if alpha < 1: im2.putalpha(im2.split()[3].point(lambda v: int(v * alpha)))
    fr.alpha_composite(im2, (int(cx - im2.width / 2), int(cy - im2.height / 2)))
CTA_D = 3.6; n = int(CTA_D * FPS); cta_v = TD + 'cta.mp4'
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', cta_v], stdin=subprocess.PIPE)
rng = np.random.default_rng(5); stars = [(rng.uniform(80, 1000), rng.uniform(500, 1500), rng.uniform(0, 2.5)) for _ in range(40)]
for k in range(n):
    t = k / FPS
    z = 1.0 + 0.04 * t / CTA_D; bg = cv2.resize(BG, None, fx=z, fy=z)[int((BG.shape[0] * z - H) / 2):][:H, int((BG.shape[1] * z - W) / 2):][:, :W]
    bg = cv2.GaussianBlur(bg, (0, 0), 4 + 16 * min(1, t / 0.5)); bg = (bg * (1 - 0.55 * min(1, t / 0.5))).astype(np.uint8)
    if t < 0.12: bg = cv2.addWeighted(bg, 1 - (1 - t / 0.12) * 0.8, np.full_like(bg, 255), (1 - t / 0.12) * 0.8, 0)
    fr = Image.fromarray(bg).convert('RGBA'); dr = ImageDraw.Draw(fr)
    for x, y, ph in stars:                                   # gold glitter
        a = max(0.0, math.sin(math.pi * ((t * 1.3 + ph) % 1.0))); s = 3 + 9 * a
        if a > 0.05:
            c = (255, 215, 120, int(220 * a)); dr.line((x - 2 * s, y, x + 2 * s, y), fill=c, width=2); dr.line((x, y - 2 * s, x, y + 2 * s), fill=c, width=2)
    paste(fr, L1, 540, 700, spring(t - 0.15), 1.0)
    pulse = 1 + 0.035 * math.sin(2 * math.pi * 1.6 * max(0, t - 1.0)) if t > 1.0 else 1.0
    paste(fr, L2, 540, 900, spring(t - 0.45, 6, 12) * pulse, 1.0)
    paste(fr, MEGA, 870, 560, 0.62 * spring(t - 0.8), 1.0, rot=12 * math.sin(3 * t))
    if t > 1.2: paste(fr, chip, 540 + 700 * (1 - min(1, spring(t - 1.2))), 1110, 1.0, 1.0)
    if t > 1.6: paste(fr, chip2, 540, 1250, 1.0, min(1.0, (t - 1.6) / 0.3))
    enc.stdin.write(np.asarray(fr.convert('RGB')).tobytes())
enc.stdin.close(); enc.wait()

# ---- assemble picture, then the sound (clips + whooshes + hit + bass drop + CTA voice), master to -14 LUFS
with open(TD + 'list.txt', 'w') as f:
    for p, _ in parts: f.write(f"file '{os.path.basename(p)}'\n")
starts, t = [], 0.0
for _, dur in parts: starts.append(t); t += dur
cta_at = t; total = t + CTA_D
run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', TD + 'list.txt', '-an', '-c:v', 'libx264', '-preset', 'medium',
     '-crf', '18', '-pix_fmt', 'yuv420p', TD + 'clips_v.mp4'])
run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', TD + 'list.txt', '-vn', '-c:a', 'pcm_s16le', TD + 'clips_a.wav'])
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', TD + 'clips_v.mp4', '-i', cta_v, '-filter_complex', '[0:v][1:v]concat=n=2:v=1:a=0[v]', '-map', '[v]',
     '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', TD + 'video.mp4'])
ins, mix, labels = ['-i', TD + 'clips_a.wav'], ['[1:a]aresample=48000[m0]'], ['[m0]']   # input 0 is the video
def add(path, at, vol):
    k = len(labels) + 1; ins.extend(['-i', path]); ms = int(at * 1000)
    mix.append(f'[{k}:a]aresample=48000,volume={vol},adelay={ms}|{ms}[m{k}]'); labels.append(f'[m{k}]')
for i in WHOOSH_INTO: add(SFX + 'whoosh.mp3', max(0, starts[i] - 0.35), 0.55)
add(SFX + 'hit.mp3', starts[-1] + 0.12, 0.9)
add(SFX + 'bass_drop.mp3', cta_at, 0.8)
add(A.cta, cta_at + 0.35, 1.6)
mix.append(''.join(labels) + f'amix=inputs={len(labels)}:duration=longest:normalize=0,apad,atrim=0:{total:.3f},loudnorm=I=-14.5:TP=-2:LRA=11,alimiter=limit=0.72:level=false:attack=2:release=60[a]')
run(['ffmpeg', '-y', '-loglevel', 'error', '-i', TD + 'video.mp4', *ins, '-filter_complex', ';'.join(mix), '-map', '0:v', '-map', '[a]',
     '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', '-t', f'{total:.3f}', OUT + 'gheybat_teaser.mp4'])
print('teaser', round(total, 2), 's ->', OUT + 'gheybat_teaser.mp4')
