#!/usr/bin/env python3
"""Edit «غیبت کردن هوش مصنوعی» (پشت درهای بسته، قسمت ۱) from the storyboard panels and the finished audio.

  python3 meshkani-pro/specials/gheybat/build_edit.py --dir work/gheybat
Inputs in <dir>: audio/intro.mp3, audio/ep1.mp3, audio/stt.json (ElevenLabs scribe, word timings + speakers),
panels/*.jpg (1080x1920 cuts of the boards), cover_2_emoji.jpg, fonts/Vazirmatn-*.ttf.
Output: <dir>/out/gheybat_ep1.mp4 (+ shots.json, subs.ass).
Edit logic: the black title cover plays under the intro voice, fades to black, the café fades in. Each line of dialogue
cuts to its speaker (a pool of panels per character); the key storyboard panels land on their timecodes; every moment
that talks about Mahdi cuts to a Mahdi panel; shots never hold more than ~5 s and always move (slow pan/push).
"""
import argparse, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); ap.add_argument('--plan-only', action='store_true'); a = ap.parse_args()
D = a.dir.rstrip('/') + '/'; OUT = D + 'out/'; os.makedirs(OUT, exist_ok=True)
INTRO = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', D + 'audio/intro.mp3'], capture_output=True, text=True).stdout)
EP = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', D + 'audio/ep1.mp3'], capture_output=True, text=True).stdout)
OFF = round(INTRO + 0.25, 2)            # episode audio starts here
COVER_END = OFF                          # cover + fade-to-black end; the café fades in at OFF

SPK = {'speaker_0': 'nima', 'speaker_1': 'kaveh', 'speaker_5': 'kaveh', 'speaker_2': 'amir', 'speaker_3': 'nova', 'speaker_4': 'sara'}
NAME = {'nima': 'نیما', 'kaveh': 'کاوه', 'amir': 'امیر', 'nova': 'نُوا', 'sara': 'سارا'}
COL = {'nima': '&H3C64FF&', 'kaveh': '&H34C8FF&', 'amir': '&H6EE08A&', 'nova': '&HC8F0B4&', 'sara': '&H4FB4FF&'}  # ASS BGR
POOL = {'nima': ['av2', 'o1_2', 'o1_6', 'A8', 'o1_7', 'A12', 'B4', 'o2_2'],
        'kaveh': ['av4', 'o1_9', 'A11', 'A2', 'o2_3', 'B10'],
        'amir': ['av3', 'o1_3', 'A9', 'o1_8', 'o2_5', 'B11', 'C1'],
        'nova': ['av5', 'o1_4', 'A5', 'o2_7', 'A10', 'B12', 'C8'],
        'sara': ['av1', 'o1_5', 'o1_10', 'B1', 'o2_1', 'o2_4', 'B7', 'C7', 'o2_9'],
        'group': ['o1_1', 'o1_12', 'o2_6', 'o2_11'],
        'mahdi': ['m1', 'm4', 'm2', 'm3']}
# key storyboard panels on the episode clock (seconds), from the timed transcript
KEYS = [(0.8, 'A1'), (9.6, 'A2'), (18.9, 'A3'), (28.6, 'A4'), (39.5, 'A5'), (55.8, 'A6'), (76.3, 'A7'), (94.6, 'A8'),
        (106.0, 'A9'), (121.9, 'A10'), (133.4, 'A11'), (155.7, 'A12'),
        (164.98, 'B1'), (181.9, 'B2'), (192.8, 'B3'), (208.98, 'B4'), (219.7, 'B5'), (244.8, 'B6'), (255.1, 'B7'),
        (284.8, 'm1'), (277.0, 'B8'), (296.1, 'B9'), (310.6, 'B10'), (323.2, 'm4'), (330.8, 'B11'), (352.0, 'B12'),
        (362.8, 'C1'), (370.2, 'C2'), (393.2, 'C3'), (408.3, 'C4'), (437.0, 'C5'), (458.2, 'm3'), (465.3, 'C6'),
        (482.2, 'm1'), (489.2, 'C7'), (494.0, 'C8'), (514.2, 'C9'), (520.2, 'o2_9'), (531.8, 'C10'), (545.0, 'm2'),
        (581.0, 'o2_9'), (584.5, 'm3'), (597.9, 'C11'), (610.9, 'm3'), (618.8, 'C12'), (639.1, 'o2_11'),
        (642.1, 'o2_10'), (646.6, 'm2'), (657.1, 'o2_12')]
KEYS.sort()

stt = json.load(open(D + 'audio/stt.json'))
W = [w for w in stt['words'] if w.get('type') != 'spacing']
U, cur = [], None
for w in W:
    sp, ev = SPK.get(w.get('speaker_id'), 'group'), w.get('type') == 'audio_event'
    if cur and (sp != cur['sp'] or w['start'] - cur['end'] > 0.8 or ev or cur['ev']):
        U.append(cur); cur = None
    if not cur: cur = {'sp': sp, 'start': w['start'], 'end': w['end'], 'ev': ev, 'words': []}
    cur['end'] = w['end']
    if not ev: cur['words'].append(w)
U.append(cur)

# ---- shot list. Each line cuts to its speaker 0.12 s before the first word; short replies get their own shot;
# key storyboard panels land on their timecodes; the word «مهدی/مشکانی/رئیس» cuts to Mahdi for ~2.6 s; long speeches
# stay on the speaker (another angle every ~4.5 s). Short audio events (< 1.2 s laughs, knocks) do not cut.
U = [u for u in U if not (u['ev'] and u['end'] - u['start'] < 1.2)]
LEAD, rot = 0.12, {k: 0 for k in POOL}
MAHDI = re.compile(r'مهدی|مهدیه|مشکانی|مشگانی|رئیس|رییس')
def pick(pool, avoid):
    for _ in range(len(POOL[pool])):
        img = POOL[pool][rot[pool] % len(POOL[pool])]; rot[pool] += 1
        if img != avoid: return img
    return POOL[pool][0]
keys_left = list(KEYS)
raw, prev = [], None
def fill(s, e, pool):
    global prev
    t = s
    while e - t > 5.6:
        im = pick(pool, prev); raw.append([t, t + 4.5, im]); prev = im; t += 4.5
    if e - t > 0.01:
        im = pick(pool, prev); raw.append([t, e, im]); prev = im
for i, u in enumerate(U):
    s = 0.0 if i == 0 else max(0.0, u['start'] - LEAD)
    e = EP if i + 1 == len(U) else max(s + 0.3, U[i + 1]['start'] - LEAD)
    pool = 'group' if u['ev'] else u['sp']
    sp = []                                                     # specials: (at, img, dur)
    for kt, k in list(keys_left):
        if s - 0.9 <= kt < e:
            sp.append((max(s, kt - 0.2), k, 4.2)); keys_left.remove((kt, k))
    if pool != 'group':
        last = -9
        for w in u['words']:
            if MAHDI.search(w['text']) and w['start'] - last > 2.6 and not any(a <= w['start'] < a + dd for a, _, dd in sp):
                sp.append((max(s, w['start'] - 0.1), None, 2.6)); last = w['start']
    sp.sort(key=lambda x: x[0])
    cur = s
    for at, img, dur in sp:
        if at < cur: at = cur
        if at >= e - 0.3: break
        if at - cur >= 0.6: fill(cur, at, pool)
        elif raw and at > cur: raw[-1][1] = at               # tiny gap: previous shot holds
        else: at = cur
        im = img or pick('mahdi', prev)
        end = min(at + dur, e); raw.append([at, end, im]); prev = im; cur = end
    if e - cur >= 0.6 or not raw: fill(cur, e, pool)
    else: raw[-1][1] = e
shots = []
for a0, a1, im in raw:
    if shots and (a1 - a0 < 0.45 or shots[-1]['img'] == im): shots[-1]['end'] = round(a1 + OFF, 3); continue
    shots.append({'start': round(a0 + OFF, 3), 'end': round(a1 + OFF, 3), 'img': im})
shots[0]['start'] = OFF; shots[-1]['end'] = round(OFF + EP, 3)
json.dump(shots, open(OUT + 'shots.json', 'w'), indent=0)

# ---- subtitles (ASS). Encoding -1 = libass detects the paragraph direction, so Persian lines are RTL (name and
# punctuation on the right side) and right-aligned. Phrases break at punctuation, ≤ 7 words, ≤ 2 lines of ≤ 5 words.
FIX = [('مشگانی', 'مشکانی'), ('نووا', 'نُوا'), ('هووou', 'هوووو'), ('رییس', 'رئیس')]
def ts(t): h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f"{h}:{m:02d}:{s:05.2f}"
PUNC = ('.', '،', ',', '!', '?', '؟', '…', ':')
def phrases(ws):
    out, cur = [], []
    for w in ws:
        cur.append(w)
        if w['text'].strip().endswith(PUNC) or len(cur) >= 7: out.append(cur); cur = []
    if cur: out.append(cur)
    merged = []
    for p in out:
        if merged and len(p) <= 2 and len(merged[-1]) + len(p) <= 9: merged[-1] += p
        elif merged and len(merged[-1]) <= 1 and len(merged[-1]) + len(p) <= 9: merged[-1] += p
        else: merged.append(p)
    return merged
def two_lines(words):
    if len(words) <= 5: return ' '.join(words)
    k = len(words) // 2
    for j in range(len(words) - 1, 0, -1):                     # prefer a break after punctuation near the middle
        if abs(j - k) <= 1 and words[j - 1].endswith(PUNC): k = j; break
    return ' '.join(words[:k]) + r'\N' + ' '.join(words[k:])
ev = []
for u in U:
    if u['ev'] or not u['words']: continue
    ps = phrases(u['words'])
    for n, ch in enumerate(ps):
        words = [w['text'].strip() for w in ch]
        txt = two_lines(words)
        for x, y in FIX: txt = txt.replace(x, y)
        t0 = ch[0]['start'] + OFF - 0.05
        t1 = (min(ps[n + 1][0]['start'], ch[-1]['end'] + 0.6) if n + 1 < len(ps) else ch[-1]['end'] + 0.35) + OFF
        lead = f"{{\\c{COL[u['sp']]}}}{NAME[u['sp']]}{{\\c&HFFFFFF&}}: " if n == 0 else ''
        ev.append([t0, t1, f"{lead}{txt}"])
for j in range(len(ev) - 1): ev[j][1] = min(ev[j][1], ev[j + 1][0])      # never two cues at once
HDR = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Vazirmatn Bold,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,{bord},0,3,80,80,400,-1
Style: Box,Vazirmatn Bold,62,&H00000000,&H00000000,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
# Highlight box: semi-transparent black, rounded corners. libass has no rounded box, so measure each cue as libass
# draws it (one frame per cue on black, no outline) and draw a rounded rectangle under it as a vector shape.
X, Y, PADX, PADY, R, LH = 1000, 1520, 30, 18, 22, 58
POS = f"{{\\an3\\pos({X},{Y})}}"
open(OUT + 'measure.ass', 'w').write(HDR.format(bord=0) + '\n'.join(
    f"Dialogue: 0,{ts(j)},{ts(j + 0.5)},Sub,,0,0,0,,{POS}{t}" for j, (_, _, t) in enumerate(ev)) + '\n')
import numpy as np
raw = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', f'color=c=black:s=1080x1920:r=1:d={len(ev)}', '-vf',
                      f"ass={OUT}measure.ass:fontsdir={D}fonts", '-f', 'rawvideo', '-pix_fmt', 'gray', '-'], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, 1920, 1080)
def rbox(x0, y0, x1, y1, r):
    return (f"m {x0 + r} {y0} l {x1 - r} {y0} b {x1} {y0} {x1} {y0} {x1} {y0 + r} l {x1} {y1 - r} b {x1} {y1} {x1} {y1} {x1 - r} {y1} "
            f"l {x0 + r} {y1} b {x0} {y1} {x0} {y1} {x0} {y1 - r} l {x0} {y0 + r} b {x0} {y0} {x0} {y0} {x0 + r} {y0}")
lines = []
for j, (a0, a1, t) in enumerate(ev):
    cols = np.where((fr[j] > 60).any(axis=0))[0]
    left = int(cols.min()) if len(cols) else X - 200
    n = t.count(r'\N') + 1
    x0, x1 = left - PADX, X + PADX
    y1 = Y - 13 + PADY; y0 = Y - 13 - 50 - LH * (n - 1) - PADY
    lines.append(f"Dialogue: 0,{ts(a0)},{ts(a1)},Box,,0,0,0,,{{\\an7\\pos(0,0)\\1a&H5A&\\bord0\\shad0\\p1}}{rbox(x0, y0, x1, y1, R)}")
    lines.append(f"Dialogue: 1,{ts(a0)},{ts(a1)},Sub,,0,0,0,,{POS}{t}")
ass = HDR.format(bord=2) + '\n'.join(lines) + '\n'
open(OUT + 'subs.ass', 'w').write(ass)

if a.plan_only: print('plan only: shots', len(shots), 'subtitle cues', len(ev)); sys.exit(0)
# ---- picture: motion.py renders every frame (camera, 3D stickers, titles, light FX) on the global 30 fps clock
subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'motion.py'), '--dir', D,
                '--off', str(OFF), '--ep', str(EP)], check=True)

# ---- audio: intro at 0, episode at OFF, mastered to −14 LUFS; burn subtitles; ~4.5 Mbps for Instagram
af = (f"[1:a]aresample=48000,loudnorm=I=-16:TP=-2[i];[2:a]aresample=48000,adelay={int(OFF * 1000)}|{int(OFF * 1000)}[e];"
      f"[i][e]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', OUT + 'video_raw.mp4', '-i', D + 'audio/intro.mp3', '-i', D + 'audio/ep1.mp3',
                '-filter_complex', af + f";[0:v]ass={OUT}subs.ass:fontsdir={D}fonts[v]", '-map', '[v]', '-map', '[a]',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-maxrate', '4500k', '-bufsize', '9000k', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart', '-shortest', OUT + 'gheybat_ep1.mp4'], check=True)
print('shots', len(shots), 'subtitle lines', len(ev), 'offset', OFF)
