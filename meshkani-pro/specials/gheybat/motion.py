#!/usr/bin/env python3
"""Motion renderer for «پشت درهای بسته | قسمت اول»: every frame is a pure function of time, so 4 workers render
independent ranges and nothing can drift.

  python3 motion.py --dir work/gheybat --off 6.28 --ep 660.6     (called by build_edit.py)

Reads <dir>/out/shots.json (absolute times), audio/stt.json (word anchors), panels/, cover_2_emoji.jpg, fx/stickers/,
fonts/. Writes <dir>/out/video_raw.mp4 (no audio, no subtitles).
Look: camera moves per shot (dolly in/out, pans, arcs), entries (whip pans with motion blur, focus pulls, flashes),
snap/crash zooms with colour fringing and shockwaves, shakes, glitches, 3D stickers (perspective swing-in, squash and
stretch, drop shadow, rim glow, motion trails), 3D extruded gold titles with a shine sweep, glass chips, phone
notifications, a REC viewfinder for the meta reveal, lens flares, light leaks, sparks, confetti, glitter, vignette.
"""
import argparse, json, math, os, re, subprocess, sys
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

ap = argparse.ArgumentParser()
ap.add_argument('--dir', required=True); ap.add_argument('--off', type=float, required=True); ap.add_argument('--ep', type=float, required=True)
ap.add_argument('--workers', type=int, default=4); ap.add_argument('--worker', type=int, default=-1)
ap.add_argument('--only', default='', help='debug: comma list of seconds to render as PNG stills')
A = ap.parse_args()
D = A.dir.rstrip('/') + '/'; OUT = D + 'out/'; HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE); from cues import CUES
W, H, FPS = 1080, 1920, 30
OFF, EP = A.off, A.ep
NT = round((OFF + EP) * FPS); NC = round(OFF * FPS)
SH = json.load(open(OUT + 'shots.json'))
FB = D + 'fonts/Vazirmatn-Bold.ttf'; FK = D + 'fonts/Vazirmatn-Black.ttf'

# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x
def eio(x): x = clamp(x); return 0.5 - 0.5 * math.cos(math.pi * x)
def eout(x): x = clamp(x); return 1 - (1 - x) ** 3
def eexpo(x): x = clamp(x); return 1 - 2 ** (-10 * x) if x < 1 else 1.0
def spring(t, k=7.0, w=15.0): return 0.0 if t <= 0 else 1 - math.exp(-k * t) * math.cos(w * t)

# ---------------------------------------------------------------- cue resolution (snap to spoken words)
def norm(s): return s.replace('‌', '').replace('ي', 'ی').replace('ك', 'ک')
WORDS = [w for w in json.load(open(D + 'audio/stt.json'))['words'] if w.get('type') == 'word']
def anchor(t, rx, nth=1):
    if not rx: return t
    r = re.compile(norm(rx)); k = 0
    for w in WORDS:
        if w['start'] < t - 1.5: continue
        if w['start'] > t + 12: break
        if r.search(norm(w['text'])):
            k += 1
            if k == nth: return w['start']
    print(f'  ! cue anchor not found: {rx!r} near {t}', file=sys.stderr); return t
EV = []          # (T_abs, kind, params)
for t, rx, kind, p in CUES:
    p = dict(p); ta = anchor(t, rx, p.pop('nth', 1))
    if kind == 'chips':
        items, tt = [], ta
        for crx, text, icon in p['items']:
            tt = anchor(tt, crx); items.append((tt + OFF, text, icon)); tt += 0.2
        p['items'] = items; p['end'] += OFF
    if kind == 'rec': p['end'] += OFF
    EV.append((ta + OFF, kind, p))
# laughs: a 3D 😂 burst and a bounce; long laughs add 🤣
for w in json.load(open(D + 'audio/stt.json'))['words']:
    if w.get('type') == 'audio_event' and 'خنده' in w['text'] and w['end'] - w['start'] >= 0.7:
        d = w['end'] - w['start']
        EV.append((w['start'] + OFF, 'burst', {'s': 'joy', 'n': 3 if d < 2.5 else 5, 'x': 540, 'y': 1250, 'alt': 'rofl' if d >= 2.5 else None}))
        EV.append((w['start'] + OFF, 'bounce', {'dur': min(d, 3.0)}))
EV.sort(key=lambda e: e[0])
def active(T, kinds, span):
    return [(t, k, p) for t, k, p in EV if k in kinds and t <= T < t + span]

# ---------------------------------------------------------------- shots: moves and entries
MAHDI_IMGS = {'m1', 'm2', 'm3', 'm4', 'A4', 'A7', 'A10', 'A11', 'B3', 'B5', 'B9', 'B12', 'C2', 'C3', 'C4', 'C5', 'C6', 'C9', 'C12', 'A9', 'B1', 'B7'}
MOVES = ['in', 'panL', 'out', 'arc', 'tiltU', 'in', 'panR', 'outarc', 'tiltD']
tags = 0
for i, s in enumerate(SH):
    d = s['end'] - s['start']; prev = SH[i - 1] if i else None
    s['move'] = 'push' if d < 2.0 else MOVES[i % len(MOVES)]
    if s['img'] in MAHDI_IMGS: s['entry'] = 'focus'
    elif i > 1 and (prev['end'] - prev['start'] < 1.7 or d < 1.7): s['entry'] = 'whip'
    elif i and i % 5 == 0: s['entry'] = 'zoomblur'
    else: s['entry'] = 'cut'
    s['whipdir'] = 1 if i % 2 else -1
    s['tag'] = s['img'].startswith('m') and tags < 2
    if s['tag']: tags += 1
    s['leak'] = s['entry'] == 'focus' or i == 0
SH_START = [s['start'] for s in SH]

# ---------------------------------------------------------------- assets
PANEL = {}
def panel(name):
    if name not in PANEL:
        im = cv2.imread(f"{D}panels/{name}.jpg", cv2.IMREAD_COLOR)[:, :, ::-1]
        PANEL[name] = cv2.resize(im, (1620, 2880), interpolation=cv2.INTER_LANCZOS4)
    return PANEL[name]
COVER = cv2.resize(cv2.imread(D + 'cover_2_emoji.jpg')[:, :, ::-1], (1620, 2880), interpolation=cv2.INTER_LANCZOS4)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.0 - 0.42 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.47) / (H * 0.62)) ** 2) ** 1.4, 0.45, 1.0)
VIG = (np.dstack([VIG] * 3) * 255).astype(np.uint8)
rng0 = np.random.default_rng(7)
LEAK = np.zeros((1300, 2600, 3), np.float32)
for cx, cy, r, col in [(500, 650, 520, (255, 140, 40)), (1200, 500, 420, (255, 70, 120)), (1900, 760, 560, (255, 180, 60))]:
    g = np.exp(-(((np.mgrid[0:1300, 0:2600][1] - cx) ** 2 + (np.mgrid[0:1300, 0:2600][0] - cy) ** 2) / (2 * r * r)))
    LEAK += g[:, :, None] * np.array(col, np.float32)
LEAK = np.clip(LEAK, 0, 255).astype(np.uint8)

def rgba_f(im):            # PIL RGBA -> premultiplied float32
    a = np.asarray(im.convert('RGBA'), np.float32) / 255.0
    a[:, :, :3] *= a[:, :, 3:4]; return a
STK = {}
def sticker(name, size=300):
    k = (name, size)
    if k not in STK:
        im = Image.open(f"{D}fx/stickers/{name}.png").convert('RGBA'); s = size / max(im.size)
        STK[k] = rgba_f(im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS))
    return STK[k]

def pil_text(draw, xy, txt, font, fill, ltr=False, **kw):
    draw.text(xy, txt, font=font, fill=fill, direction='ltr' if ltr else 'rtl', language='en' if ltr else 'fa', **kw)
TXT = {}
STYLES = {'gold': ((255, 246, 190), (255, 196, 40), (214, 120, 0), (110, 55, 0)),
          'red': ((255, 214, 200), (255, 80, 60), (190, 20, 20), (90, 0, 0)),
          'cyan': ((220, 255, 255), (80, 220, 255), (20, 120, 220), (0, 40, 110)),
          'white': ((255, 255, 255), (240, 240, 245), (190, 190, 205), (70, 70, 90))}
def text3d(txt, style='gold', ltr=False, size=118):
    k = (txt, style, ltr)
    if k in TXT: return TXT[k]
    f = ImageFont.truetype(FK, size)
    while True:
        bb = ImageDraw.Draw(Image.new('L', (10, 10))).textbbox((0, 0), txt, font=f, direction='ltr' if ltr else 'rtl', language='en' if ltr else 'fa')
        if bb[2] - bb[0] <= 940 or size <= 64: break
        size -= 6; f = ImageFont.truetype(FK, size)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]; pad, depth = 40, max(8, size // 9)
    Wt, Ht = tw + 2 * pad + depth, th + 2 * pad + depth
    mask = Image.new('L', (Wt, Ht)); dm = ImageDraw.Draw(mask)
    pil_text(dm, (pad - bb[0], pad - bb[1]), txt, f, 255, ltr, stroke_width=5, stroke_fill=255)
    face = Image.new('L', (Wt, Ht)); pil_text(ImageDraw.Draw(face), (pad - bb[0], pad - bb[1]), txt, f, 255, ltr)
    hi, mid, lo, ext = STYLES[style]
    out = Image.new('RGBA', (Wt, Ht))
    for i in range(depth, 0, -1):                       # extrusion, darker towards the back
        c = tuple(int(ext[j] + (lo[j] - ext[j]) * (1 - i / depth) * 0.6) for j in range(3))
        layer = Image.new('RGBA', (Wt, Ht), c + (255,)); out.paste(layer, (i, i), mask)
    out.paste(Image.new('RGBA', (Wt, Ht), (25, 12, 0, 255) if style != 'white' else (30, 30, 45, 255)), (0, 0), mask)   # outline
    grad = np.zeros((Ht, Wt, 3), np.float32); ys = np.linspace(0, 1, Ht)[:, None]
    for j in range(3): grad[:, :, j] = np.interp(ys, [0, 0.45, 0.55, 1], [hi[j], mid[j], lo[j] * 0.9 + mid[j] * 0.1, lo[j]])
    out.paste(Image.fromarray(grad.astype(np.uint8)).convert('RGBA'), (0, 0), face)
    bevel = np.clip(np.asarray(face, np.float32) - np.roll(np.asarray(face, np.float32), 4, axis=0), 0, 255) * 0.55
    o = np.asarray(out, np.float32); o[:, :, :3] = np.clip(o[:, :, :3] + bevel[:, :, None], 0, 255)
    res = rgba_f(Image.fromarray(o.astype(np.uint8), 'RGBA')); fm = np.asarray(face, np.float32) / 255.0
    TXT[k] = (res, fm); return TXT[k]

CHIP = {}
def chip(text, icon=None, size=50):
    k = (text, icon)
    if k in CHIP: return CHIP[k]
    f = ImageFont.truetype(FB, size)
    bb = ImageDraw.Draw(Image.new('L', (10, 10))).textbbox((0, 0), text, font=f, direction='rtl', language='fa')
    tw = bb[2] - bb[0]; ic = 74 if icon else 0
    w, h = tw + 76 + ic, 98
    im = Image.new('RGBA', (w + 20, h + 20)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 10 + w, 10 + h), radius=49, fill=(16, 14, 24, 215), outline=(255, 200, 70, 255), width=3)
    pil_text(d, (10 + w - 38 - ic - tw - bb[0], 10 + (h - (bb[3] - bb[1])) // 2 - bb[1]), text, f, (255, 255, 255))
    if icon:
        s = Image.open(f"{D}fx/stickers/{icon}.png").convert('RGBA'); s.thumbnail((66, 66), Image.LANCZOS)
        im.alpha_composite(s, (10 + w - 30 - s.width, 10 + (h - s.height) // 2))
    CHIP[k] = rgba_f(im); return CHIP[k]

def notif_card(title, body, icon=None):
    w, h = 980, 196
    im = Image.new('RGBA', (w + 40, h + 40)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((20, 20, 20 + w, 20 + h), radius=44, fill=(248, 248, 252, 238), outline=(255, 255, 255, 255), width=2)
    if icon:
        av = Image.open(f"{D}fx/stickers/{icon}.png").convert('RGBA'); av.thumbnail((120, 120), Image.LANCZOS)
    else:
        m = Image.open(D + 'panels/m1.jpg').convert('RGB').crop((300, 330, 780, 810)).resize((120, 120), Image.LANCZOS)
        mk = Image.new('L', (120, 120)); ImageDraw.Draw(mk).ellipse((0, 0, 119, 119), fill=255); av = m.convert('RGBA'); av.putalpha(mk)
    im.alpha_composite(av, (20 + w - 38 - 120, 20 + (h - 120) // 2))
    ft, fb, fs = ImageFont.truetype(FK, 46), ImageFont.truetype(FB, 40), ImageFont.truetype(FB, 30)
    x = 20 + w - 38 - 120 - 28
    pil_text(d, (x, 58), title, ft, (20, 20, 30), anchor='ra'); pil_text(d, (x, 122), body, fb, (80, 80, 95), anchor='ra')
    pil_text(d, (60, 62), 'الان', fs, (140, 140, 150), anchor='la')
    return rgba_f(im)
NOTIF = {}
def tagcard():
    im = Image.new('RGBA', (640, 190)); d = ImageDraw.Draw(im)
    d.rounded_rectangle((10, 10, 630, 180), radius=40, fill=(14, 12, 20, 220), outline=(255, 200, 70, 255), width=3)
    d.rectangle((600, 40, 612, 150), fill=(255, 196, 40, 255))
    pil_text(d, (580, 34), 'مهدی مشکانی', ImageFont.truetype(FK, 58), (255, 255, 255), anchor='ra')
    d.text((580, 112), '@mahdi.meshkani', font=ImageFont.truetype(FB, 38), fill=(255, 200, 70), anchor='ra')
    return rgba_f(im)
TAG = tagcard()

# ---------------------------------------------------------------- compositing helpers
def blit(fr, spr, cx, cy, alpha=1.0):
    """premultiplied float RGBA sprite over uint8 frame, centred at (cx, cy)"""
    h, w = spr.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb or alpha <= 0.003: return
    s = spr[ya - y0:yb - y0, xa - x0:xb - x0] * alpha
    roi = fr[ya:yb, xa:xb].astype(np.float32) / 255.0
    roi = roi * (1 - s[:, :, 3:4]) + s[:, :, :3]
    fr[ya:yb, xa:xb] = (np.clip(roi, 0, 1) * 255).astype(np.uint8)
def add_light(fr, layer, x0=0, y0=0):
    h, w = layer.shape[:2]; xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + w), min(H, y0 + h)
    if xa >= xb or ya >= yb: return
    fr[ya:yb, xa:xb] = cv2.add(fr[ya:yb, xa:xb], layer[ya - y0:yb - y0, xa - x0:xb - x0])
def screen(fr, layer):
    a = fr.astype(np.float32); b = layer.astype(np.float32)
    fr[:] = (255 - (255 - a) * (255 - b) / 255).astype(np.uint8)

def warp3d(spr, scale=1.0, rz=0.0, ry=0.0, rx=0.0, sx=1.0, sy=1.0):
    """perspective-transform a premultiplied sprite: Y/X rotation (degrees) with a 900 px camera, squash (sx, sy)"""
    h, w = spr.shape[:2]; f = 900.0
    pts = np.array([[-w / 2, -h / 2], [w / 2, -h / 2], [w / 2, h / 2], [-w / 2, h / 2]], np.float32)
    cy_, sy_ = math.cos(math.radians(ry)), math.sin(math.radians(ry)); cx_, sx_ = math.cos(math.radians(rx)), math.sin(math.radians(rx))
    cz, sz = math.cos(math.radians(rz)), math.sin(math.radians(rz)); dst = []
    for x, y in pts:
        x, y = x * scale * sx, y * scale * sy
        X, Z = x * cy_, x * sy_; Y, Z = y * cx_, Z + y * sx_
        p = f / (f + Z); X, Y = X * p, Y * p
        dst.append([X * cz - Y * sz, X * sz + Y * cz])
    dst = np.array(dst, np.float32); mn = dst.min(0); mx = dst.max(0)
    bw, bh = int(math.ceil(mx[0] - mn[0])) + 2, int(math.ceil(mx[1] - mn[1])) + 2
    if bw < 3 or bh < 3: return None
    M = cv2.getPerspectiveTransform(pts + np.array([w / 2, h / 2], np.float32), dst - mn + 1)
    out = cv2.warpPerspective(spr, M, (bw, bh), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    shade = 0.72 + 0.28 * abs(cy_)                          # turning away darkens it: sells the 3D
    out[:, :, :3] *= shade
    return out
def sprite_fx(fr, spr, cx, cy, alpha=1.0, shadow=True, glow=(255, 190, 90), glow_k=0.35):
    if spr is None: return
    if shadow:
        a = spr[:, :, 3]; pad = 30
        sh = cv2.GaussianBlur(cv2.copyMakeBorder(a, pad, pad, pad, pad, cv2.BORDER_CONSTANT), (0, 0), 9) * 0.5 * alpha
        sp = np.zeros(sh.shape + (4,), np.float32); sp[:, :, 3] = sh
        blit(fr, sp, cx + 16, cy + 26)
    if glow_k:
        a = spr[:, :, 3]; pad = 40
        g = cv2.GaussianBlur(cv2.copyMakeBorder(a, pad, pad, pad, pad, cv2.BORDER_CONSTANT), (0, 0), 16) * glow_k * alpha
        layer = (g[:, :, None] * np.array(glow, np.float32)).clip(0, 255).astype(np.uint8)
        add_light(fr, layer, int(cx - layer.shape[1] / 2), int(cy - layer.shape[0] / 2))
    blit(fr, spr, cx, cy, alpha)

# ---------------------------------------------------------------- camera
def camera(T, s, i):
    dt, d = T - s['start'], max(0.05, s['end'] - s['start']); u = eio(dt / d)
    sc, tx, ty, rot = 1.04, 0.0, 0.0, 0.0
    m = s['move']
    if m == 'in': sc = 1.03 + 0.11 * u
    elif m == 'out': sc = 1.15 - 0.11 * u
    elif m == 'push': sc = 1.05 + 0.08 * eout(dt / d)
    elif m in ('panL', 'panR'): sc = 1.14; tx = (1 if m == 'panL' else -1) * (0.5 - u) * 0.8 * (sc - 1) * W
    elif m in ('tiltU', 'tiltD'): sc = 1.14; ty = (1 if m == 'tiltU' else -1) * (0.5 - u) * 0.8 * (sc - 1) * H
    elif m == 'arc': sc = 1.06 + 0.07 * u; rot = -1.4 + 2.8 * u; tx = (u - 0.5) * 40
    elif m == 'outarc': sc = 1.15 - 0.08 * u; rot = 1.2 - 2.4 * u
    # entries
    e, blur, mblur = s['entry'], 0.0, 0
    if e == 'whip' and dt < 0.22:
        k = 1 - eout(dt / 0.22); tx += s['whipdir'] * W * 0.42 * k; mblur = int(120 * k)
    elif e == 'focus' and dt < 0.6:
        k = (1 - eout(dt / 0.6)); blur = 16 * k * k; sc *= 1 + 0.07 * k
    elif e == 'zoomblur' and dt < 0.28:
        k = 1 - eout(dt / 0.28); sc *= 1 + 0.25 * k; blur = 6 * k
    # cue-driven camera (only cues inside this shot act on it)
    for t, kind, p in EV:
        if t > T: break
        if t < s['start'] - 0.06: continue
        x = T - t
        if kind in ('punch', 'crash'):
            sc *= 1 + (p.get('a', 0.2) if kind == 'punch' else 0.2) * eexpo(x / 0.14)
        elif kind == 'dolly': sc *= 1 + 0.14 * eio(x / 3.0)
    for t, kind, p in EV:
        if t > T: break
        x = T - t
        if kind == 'shake' and x < p['dur'] + 0.4:
            amp = p['amp'] * math.exp(-x / max(0.15, p['dur'] * 0.45))
            tx += amp * (math.sin(2 * math.pi * 9.3 * x + t) + 0.5 * math.sin(2 * math.pi * 17.1 * x))
            ty += amp * (math.cos(2 * math.pi * 11.7 * x + 2 * t) + 0.4 * math.sin(2 * math.pi * 23.3 * x))
            rot += amp * 0.035 * math.sin(2 * math.pi * 7.1 * x)
        elif kind == 'crash' and x < 0.7:
            amp = 22 * math.exp(-x / 0.18); tx += amp * math.sin(2 * math.pi * 13 * x); ty += amp * math.cos(2 * math.pi * 15 * x)
        elif kind == 'bounce' and x < p['dur']:
            sc *= 1 + 0.022 * abs(math.sin(2 * math.pi * 2.3 * x)) * math.exp(-x / 1.4)
    sc += abs(rot) * 0.012
    lim_x, lim_y = (sc - 1) * W / 2 - 4, (sc - 1) * H / 2 - 4
    if m not in ('panL', 'panR'): tx = clamp(tx, -lim_x - 60, lim_x + 60) if e != 'whip' or dt >= 0.22 else tx
    return sc, tx, ty, rot, blur, mblur

def render_plate(src, sc, tx, ty, rot):
    k = 1.5                                                     # source is 1.5x upsampled
    a = math.radians(rot); c, s_ = math.cos(a) * sc / k, math.sin(a) * sc / k
    cxs, cys = src.shape[1] / 2, src.shape[0] / 2
    M = np.array([[c, -s_, W / 2 + tx - (c * cxs - s_ * cys)], [s_, c, H / 2 + ty - (s_ * cxs + c * cys)]], np.float32)
    return cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

# ---------------------------------------------------------------- effects
def chroma(fr, k):
    if k < 0.02: return fr
    out = fr.copy()
    for ch, sgn in ((0, 1), (2, -1)):
        sc = 1 + sgn * 0.012 * k; M = np.array([[sc, 0, W / 2 * (1 - sc)], [0, sc, H / 2 * (1 - sc)]], np.float32)
        out[:, :, ch] = cv2.warpAffine(fr[:, :, ch], M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return out
def glitch(fr, T, k):
    r = np.random.default_rng(int(T * 1000)); out = fr.copy(); sh = int(8 + 22 * k)
    out[:, :, 0] = np.roll(fr[:, :, 0], sh, axis=1); out[:, :, 2] = np.roll(fr[:, :, 2], -sh, axis=1)
    for _ in range(int(4 + 8 * k)):
        y = int(r.integers(0, H - 80)); hh = int(r.integers(10, 90)); dx = int(r.integers(-80, 80) * k)
        out[y:y + hh] = np.roll(out[y:y + hh], dx, axis=1)
        if r.random() < 0.25: out[y:y + hh // 3, :, int(r.integers(0, 3))] = 255
    return out
def shockwave(fr, x, k):
    r = int(60 + 1100 * eout(x / 0.55)); a = (1 - x / 0.55) ** 1.5
    if a <= 0: return
    layer = np.zeros((H, W, 3), np.uint8); cv2.circle(layer, (W // 2, int(H * 0.42)), r, (int(255 * a), int(235 * a), int(210 * a)), int(26 * a) + 2)
    add_light(fr, cv2.GaussianBlur(layer, (0, 0), 10))
def flare(fr, px, py, k):
    if k <= 0.01: return
    band = np.zeros((260, W, 3), np.uint8); cv2.ellipse(band, (px, 130), (900, 5), 0, 0, 360, (int(140 * k), int(190 * k), int(255 * k)), -1)
    add_light(fr, cv2.GaussianBlur(band, (0, 0), sigmaX=60, sigmaY=4), 0, py - 130)
    blob = np.zeros((520, 520, 3), np.uint8); cv2.circle(blob, (260, 260), 70, (int(255 * k), int(220 * k), int(170 * k)), -1)
    add_light(fr, cv2.GaussianBlur(blob, (0, 0), 50), px - 260, py - 260)
    for j, (f_, rr, col) in enumerate([(0.6, 60, (80, 255, 200)), (1.3, 34, (255, 120, 220)), (1.8, 90, (90, 140, 255))]):
        gx, gy = int(px + (W / 2 - px) * f_ * 1.2), int(py + (H / 2 - py) * f_ * 1.2)
        g = np.zeros((rr * 4, rr * 4, 3), np.uint8); cv2.circle(g, (rr * 2, rr * 2), rr, tuple(int(c * 0.35 * k) for c in col), -1)
        add_light(fr, cv2.GaussianBlur(g, (0, 0), rr * 0.4), gx - rr * 2, gy - rr * 2)
def leak(fr, x, k):
    if k <= 0.01: return
    ox = int(600 * x); win = LEAK[:, ox % 1200: ox % 1200 + 1400]
    layer = cv2.resize(win, (W, H)); screen(fr, (layer.astype(np.float32) * k * 0.55).astype(np.uint8))
def particles(fr, T):
    layer = None
    for t, kind, p in EV:
        if t > T: break
        x = T - t
        if kind == 'sparks' and x < 1.4:
            layer = layer if layer is not None else np.zeros((H, W, 3), np.uint8); r = np.random.default_rng(int(t * 100))
            for _ in range(70):
                vx, vy = r.uniform(-900, 900), r.uniform(-1500, -400); px = p['x'] + vx * x; py = p['y'] + vy * x + 1400 * x * x
                life = 1 - x / r.uniform(0.6, 1.4)
                if life > 0: cv2.line(layer, (int(px), int(py)), (int(px - vx * 0.02), int(py - (vy + 2800 * x) * 0.02)), (int(255 * life), int(170 * life), int(60 * life)), 3)
        elif kind == 'glitter' and x < 1.8:
            layer = layer if layer is not None else np.zeros((H, W, 3), np.uint8); r = np.random.default_rng(int(t * 100) + 1)
            for _ in range(46):
                px, py = p['x'] + r.uniform(-420, 420), p['y'] + r.uniform(-420, 300) - 120 * x
                tw = max(0, math.sin(math.pi * clamp((x - r.uniform(0, 0.8)) / 0.9))); s_ = int(4 + 10 * tw)
                if tw > 0:
                    c = (int(255 * tw), int(215 * tw), int(120 * tw)); cv2.line(layer, (int(px - s_ * 2), int(py)), (int(px + s_ * 2), int(py)), c, 2)
                    cv2.line(layer, (int(px), int(py - s_ * 2)), (int(px), int(py + s_ * 2)), c, 2); cv2.circle(layer, (int(px), int(py)), 3, c, -1)
        elif kind == 'confetti' and x < 3.0:
            r = np.random.default_rng(int(t * 100) + 2)
            for _ in range(90):
                px = r.uniform(0, W) + 60 * math.sin(3 * x + r.uniform(0, 6)); py = -60 + r.uniform(-500, 0) + 700 * x
                ang = r.uniform(0, 6) + 6 * x; col = [(255, 70, 90), (255, 210, 60), (80, 200, 255), (120, 255, 140), (220, 120, 255)][int(r.integers(0, 5))]
                cw, ch_ = 14, 26 * abs(math.cos(ang * 1.7)) + 4
                box = cv2.boxPoints(((px, py), (cw, ch_), math.degrees(ang))).astype(np.int32); cv2.fillPoly(fr, [box], col)
    if layer is not None:
        add_light(fr, cv2.GaussianBlur(layer, (0, 0), 5)); add_light(fr, layer)

def stickers(fr, T):
    for t, kind, p in EV:
        if t > T + 0.01: break
        x = T - t
        if kind == 'pop' and x < 1.7:
            sp = spring(x, 7, 15); out = clamp((x - 1.45) / 0.25)
            sc = max(0.01, sp * (1 - out)); ry = 75 * (1 - eout(x / 0.45)) - 25 * out
            bob = 10 * math.sin(2 * math.pi * 1.3 * x); rz = 8 * math.sin(2 * math.pi * 0.9 * x + 1)
            sprite_fx(fr, warp3d(sticker(p['s'], 290), sc, rz, ry, rx=6 * math.sin(4 * x)), p['x'], p['y'] + bob, 1 - out)
        elif kind == 'slam' and x < 1.6:
            fall = eexpo(x / 0.22); y = p['y'] - 900 * (1 - fall); land = x - 0.22
            sq = 1 + (0.32 * math.exp(-land / 0.12) * math.cos(2 * math.pi * 3 * land) if land > 0 else -0.25 * (1 - fall))
            out = clamp((x - 1.35) / 0.25); sc = 1.15 * (1 - out) + 0.01
            sprite_fx(fr, warp3d(sticker(p['s'], 320), sc, 0, 0, 0, sx=sq, sy=2 - sq), p['x'], y, 1 - out, glow_k=0.45)
            if 0 < land < 0.5:
                rr = int(40 + 360 * eout(land / 0.5)); a = 1 - land / 0.5; layer = np.zeros((900, 900, 3), np.uint8)
                cv2.ellipse(layer, (450, 450), (rr, int(rr * 0.42)), 0, 0, 360, (int(255 * a), int(230 * a), int(190 * a)), 6)
                add_light(fr, cv2.GaussianBlur(layer, (0, 0), 4), int(p['x'] - 450), int(p['y'] + 110 - 450))
        elif kind == 'burst' and x < 2.0:
            r = np.random.default_rng(int(t * 10)); n = p.get('n', 3)
            for j in range(n):
                vx, vy = r.uniform(-520, 520), r.uniform(-1500, -1000); spin = r.uniform(-260, 260)
                for g, ga in ((0.06, 0.18), (0.03, 0.3), (0.0, 1.0)):          # motion trail ghosts
                    xx_ = x - g
                    if xx_ < 0: continue
                    px, py = p['x'] + vx * xx_, p['y'] + vy * xx_ + 1100 * xx_ * xx_
                    name = p['alt'] if (p.get('alt') and j % 2) else p['s']
                    sc = (0.75 + 0.35 * spring(xx_, 8, 18)) * (1 - clamp((xx_ - 1.5) / 0.4))
                    sprite_fx(fr, warp3d(sticker(name, 210), max(sc, 0.01), spin * xx_, 40 * math.sin(5 * xx_)), px, py, ga * (1 - clamp((xx_ - 1.5) / 0.4)),
                              shadow=ga == 1.0, glow_k=0.3 if ga == 1.0 else 0)
        elif kind == 'flyby' and x < p['dur']:
            for g, ga in ((0.08, 0.15), (0.04, 0.3), (0.0, 1.0)):
                u = eio((x - g) / p['dur'])
                if x - g < 0: continue
                px = p['x0'] + (p['x1'] - p['x0']) * u; py = p['y0'] + (p['y1'] - p['y0']) * u - 160 * math.sin(math.pi * u)
                ang = math.degrees(math.atan2(p['y1'] - p['y0'], p['x1'] - p['x0']))
                sprite_fx(fr, warp3d(sticker(p['s'], 300), 1.0, ang * 0.35, 30 * math.sin(6 * x)), px, py, ga, shadow=ga == 1.0, glow_k=0.5 if ga == 1.0 else 0)

def titles(fr, T):
    for t, kind, p in EV:
        if t > T + 0.01: break
        x = T - t; dur = p.get('dur', 2.4)
        if kind == 'kt' and x < dur:
            spr, face = text3d(p['text'], p.get('style', 'gold'), p.get('ltr', False))
            out = clamp((x - dur + 0.3) / 0.3); sc = spring(x, 6.5, 13) * (1 - 0.6 * out)
            res = spr.copy()
            if 0.15 < x < 0.95:                                   # shine sweep across the face
                hh, ww = face.shape; pos = (x - 0.15) / 0.8 * (ww + hh) - hh
                band = np.clip(1 - np.abs((np.arange(ww)[None, :] + np.arange(hh)[:, None] * 0.6) - pos) / 40, 0, 1) * face * 0.85
                res[:, :, :3] = np.clip(res[:, :, :3] + band[:, :, None], 0, 1)
            sprite_fx(fr, warp3d(res, max(sc, 0.01), 0, 35 * (1 - eout(x / 0.5)) + 20 * out, rx=-12 * (1 - eout(x / 0.5))),
                      540, p.get('y', 1240), 1 - out, glow=(255, 170, 60) if p.get('style', 'gold') == 'gold' else (120, 200, 255), glow_k=0.4)
        elif kind == 'chips' and x < p['end'] - t + 0.4:
            shown = [(ct, txt, ic) for ct, txt, ic in p['items'] if ct <= T]
            fade = clamp((T - p['end']) / 0.35); mx = p.get('max', 5)
            for j, (ct, txt, ic) in enumerate(reversed(shown)):            # newest at the bottom, older ones rise
                if j >= mx + 1: break
                cx_ = T - ct; spr = chip(txt, ic)
                yb = 1350 - j * 112 + 112 * (1 - eout(min(1, (T - shown[-1][0]) / 0.3))) * (j > 0)
                a = (1 - fade) * (1 - clamp(j - mx + 1)) if j >= mx else (1 - fade)
                xo = 900 * (1 - eout(cx_ / 0.35))
                w3 = warp3d(spr, 1.0, 0, -55 * (1 - eout(cx_ / 0.45)))
                if w3 is not None: blit(fr, w3, W - 40 - w3.shape[1] / 2 + xo, yb, a)
        elif kind == 'notif' and x < p['dur']:
            k = (p['title'], p['body'], p.get('icon'))
            if k not in NOTIF: NOTIF[k] = notif_card(*k)
            yin = spring(x, 7, 14); yout = eout(clamp((x - p['dur'] + 0.4) / 0.4))
            sprite_fx(fr, NOTIF[k], 540, -160 + (330 * yin) - 330 * yout, 1.0, glow_k=0)
        elif kind == 'endcard' and T >= t:
            pass

def tagbar(fr, T, s):
    if not s['tag']: return
    x = T - s['start']
    if 0.35 < x < 3.0:
        k = eout((x - 0.35) / 0.4); out = eout(clamp((x - 2.6) / 0.4))
        blit(fr, TAG, W - 40 - TAG.shape[1] / 2 + 700 * (1 - k) + 700 * out, 1260, 1.0)

def rec(fr, T):
    for t, kind, p in EV:
        if kind == 'rec' and t <= T < p['end']:
            x = T - t; a = eout(x / 0.3); c = (235, 235, 235)
            for (x0, y0, dx, dy) in ((70, 210, 1, 1), (W - 70, 210, -1, 1), (70, H - 300, 1, -1), (W - 70, H - 300, -1, -1)):
                cv2.line(fr, (x0, y0), (x0 + dx * 90, y0), c, 6); cv2.line(fr, (x0, y0), (x0, y0 + dy * 90), c, 6)
            if int(x * 2) % 2 == 0:
                g = np.zeros((120, 120, 3), np.uint8); cv2.circle(g, (60, 60), 26, (255, 40, 40), -1)
                add_light(fr, cv2.GaussianBlur(g, (0, 0), 12), 70, 200); cv2.circle(fr, (130, 260), 18, (255, 30, 30), -1)
            cv2.putText(fr, 'REC', (165, 278), cv2.FONT_HERSHEY_DUPLEX, 1.6, (255, 255, 255), 3, cv2.LINE_AA)
            tc = T - OFF; cv2.putText(fr, f"00:{int(tc // 60):02d}:{int(tc % 60):02d}:{int(tc * 30 % 30):02d}", (W - 430, 278),
                                     cv2.FONT_HERSHEY_DUPLEX, 1.3, (255, 255, 255), 2, cv2.LINE_AA)

def endcard(fr, T):
    t = [e[0] for e in EV if e[1] == 'endcard']
    if not t or T < t[0]: return fr
    x = T - t[0]
    bg = cv2.GaussianBlur(fr, (0, 0), 6 + 18 * eout(x / 0.8))
    fr = cv2.addWeighted(bg, 1 - 0.55 * eout(x / 0.8), np.zeros_like(bg), 0, 0)
    spr, face = text3d('ادامه دارد…', 'gold'); sc = spring(x - 0.3, 6, 12)
    if sc > 0: sprite_fx(fr, warp3d(spr, max(0.01, sc * 1.1), 0, 25 * math.sin(1.2 * x)), 540, 820, 1.0, glow_k=0.5)
    if x > 0.9: blit(fr, chip('قسمت دوم به‌زودی', 'clapper'), 540, 1030, eout((x - 0.9) / 0.4))
    if x > 1.4:
        s2 = text3d('@mahdi.meshkani', 'white', True, 70)[0]; blit(fr, s2, 540, 1170, eout((x - 1.4) / 0.4))
    flare(fr, 300, 600, 0.5 * eout(x / 1.0))
    return fr

# ---------------------------------------------------------------- one frame
def shot_at(T):
    lo, hi = 0, len(SH) - 1
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if SH_START[mid] <= T: lo = mid
        else: hi = mid - 1
    return lo
def frame(n):
    T = n / FPS
    if n < NC:                                                  # cover under the intro voice
        x = T / OFF; fr = render_plate(COVER, 1.0 + 0.05 * eio(x), 0, 0, 0)
        leak(fr, x, 0.35 * math.sin(math.pi * clamp(x * 1.3)))
        if T > OFF - 0.6: fr = (fr.astype(np.float32) * clamp((OFF - T) / 0.6)).astype(np.uint8)
        return fr
    i = shot_at(T); s = SH[i]; dt = T - s['start']
    sc, tx, ty, rot, blur, mblur = camera(T, s, i)
    fr = render_plate(panel(s['img']), sc, tx, ty, rot)
    if s['entry'] == 'whip' and dt < 0.22 and i > 0:            # real whip pan: the last shot slides out as this one slides in
        k = 1 - eout(dt / 0.22); d_ = s['whipdir']; p = SH[i - 1]
        psc, ptx, pty, prot, _, _ = camera(min(T, p['end'] - 0.01), p, i - 1)
        prev = render_plate(panel(p['img']), psc, ptx + d_ * W * k - d_ * W, pty, prot)
        cut = int(W * k)
        if d_ > 0: fr[:, :cut] = prev[:, :cut]
        else: fr[:, W - cut:] = prev[:, W - cut:]
    if mblur > 2: fr = cv2.blur(fr, (mblur, 1))
    if blur > 0.3: fr = cv2.GaussianBlur(fr, (0, 0), blur)
    ca, gl, fl = 0.0, 0.0, None
    for t, kind, p in EV:
        if t > T: break
        x = T - t
        if kind == 'crash' and x < 0.6:
            ca = max(ca, 1 - x / 0.6); shockwave(fr, x, 1)
            if x < 0.12: fl = ((255, 60, 60) if p.get('red') else (255, 255, 255), 0.75 * (1 - x / 0.12))
        elif kind == 'punch' and x < 0.3: ca = max(ca, 0.5 * (1 - x / 0.3))
        elif kind == 'glitch' and x < p['dur']: gl = max(gl, 1 - x / p['dur'])
    fr = chroma(fr, ca)
    if gl > 0: fr = glitch(fr, T, gl)
    fr = cv2.multiply(fr, VIG, scale=1 / 255)
    if s['leak'] and dt < 1.1: leak(fr, dt, 0.6 * math.sin(math.pi * clamp(dt / 1.1)))
    if i == 0 and dt < 0.7: fr = (fr.astype(np.float32) * eio(dt / 0.7)).astype(np.uint8)
    for t, kind, p in EV:
        if t > T: break
        if kind == 'flare' and T - t < 1.0: flare(fr, p['x'], p['y'], math.sin(math.pi * clamp((T - t) / 1.0)))
        if kind == 'crash' and T - t < 0.5: flare(fr, 540, int(H * 0.42), 0.8 * (1 - (T - t) / 0.5))
    particles(fr, T)
    rec(fr, T)
    tagbar(fr, T, s)
    stickers(fr, T)
    titles(fr, T)
    fr = endcard(fr, T)
    if fl: fr = cv2.addWeighted(fr, 1 - fl[1], np.full_like(fr, fl[0]), fl[1], 0)
    return fr

# ---------------------------------------------------------------- drive
if A.only:
    os.makedirs(OUT + 'stills', exist_ok=True)
    for t in A.only.split(','):
        n = round(float(t) * FPS); cv2.imwrite(f"{OUT}stills/{float(t):08.2f}.jpg", frame(n)[:, :, ::-1], [cv2.IMWRITE_JPEG_QUALITY, 88])
    sys.exit(0)
if A.worker < 0:
    procs = [subprocess.Popen([sys.executable, __file__, '--dir', A.dir, '--off', str(OFF), '--ep', str(EP), '--workers', str(A.workers), '--worker', str(k)])
             for k in range(A.workers)]
    if any(p.wait() for p in procs): sys.exit('a worker failed')
    with open(OUT + 'parts.txt', 'w') as f: f.write(''.join(f"file 'part_{k}.mp4'\n" for k in range(A.workers)))
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', OUT + 'parts.txt', '-c', 'copy', OUT + 'video_raw.mp4'], check=True)
    print('frames', NT); sys.exit(0)
a, b = NT * A.worker // A.workers, NT * (A.worker + 1) // A.workers
enc = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                        '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '16', '-pix_fmt', 'yuv420p', '-g', '60', '-threads', '1',
                        OUT + f'part_{A.worker}.mp4'], stdin=subprocess.PIPE)
for n in range(a, b):
    enc.stdin.write(np.ascontiguousarray(frame(n)).tobytes())
    if A.worker == 0 and (n - a) % 300 == 0: print(f'  worker 0: {n - a}/{b - a}', flush=True)
enc.stdin.close(); sys.exit(enc.wait())
