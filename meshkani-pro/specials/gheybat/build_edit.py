#!/usr/bin/env python3
"""Edit «غیبت کردن هوش مصنوعی» (پشت درهای بسته، قسمت ۱) from the storyboard panels and the finished audio.

  python3 meshkani-pro/specials/gheybat/build_edit.py --dir work/gheybat
Inputs in <dir>: audio/intro.mp3, audio/ep1.mp3, audio/stt.json (ElevenLabs scribe, word timings + speakers),
panels/*.jpg (1080x1920 cuts of the boards), cover_2_emoji.jpg, fonts/Vazirmatn-*.ttf.
Output: <dir>/out/gheybat_ep1.mp4 (+ shots.json, subs.ass).
Edit logic: the black title cover plays under the intro voice, fades to black, the café fades in. Every dialogue line
has its own image (plan.json), cut 0.12 s before its first word; motion.py animates every frame.
"""
import argparse, json, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); ap.add_argument('--plan-only', action='store_true'); ap.add_argument('--reuse-video', action='store_true'); a = ap.parse_args()
D = a.dir.rstrip('/') + '/'; OUT = D + 'out/'; os.makedirs(OUT, exist_ok=True)
INTRO = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', D + 'audio/intro.mp3'], capture_output=True, text=True).stdout)
EP = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', D + 'audio/ep1.mp3'], capture_output=True, text=True).stdout)
OFF = round(INTRO + 0.25, 2)            # episode audio starts here
COVER_END = OFF                          # cover + fade-to-black end; the café fades in at OFF

SPK = {'speaker_0': 'nima', 'speaker_1': 'kaveh', 'speaker_5': 'kaveh', 'speaker_2': 'amir', 'speaker_3': 'nova', 'speaker_4': 'sara'}
NAME = {'nima': 'نیما', 'kaveh': 'کاوه', 'amir': 'امیر', 'nova': 'نُوا', 'sara': 'سارا'}
COL = {'nima': '&H3C64FF&', 'kaveh': '&H34C8FF&', 'amir': '&H6EE08A&', 'nova': '&HC8F0B4&', 'sara': '&H4FB4FF&'}  # ASS BGR


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

# ---- shot list from plan.json: one dedicated image per dialogue line (no image twice). The line's shot opens 0.12 s
# before its first word (or at a same-speaker laugh just before it); a long line may change to its second image at a
# named word; long audio events (the head-bang, big laughs, the phone lighting up) get their own image; any hold over
# ~6 s is cut into framings of the same image (wide -> close) so the picture never sits still.
PLAN = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plan.json')))
def nrm(s): return s.replace('‌', '').replace('ي', 'ی').replace('ك', 'ک')
L, cur = [], None
for w in [w for w in stt['words'] if w.get('type') == 'word']:
    sp = SPK.get(w.get('speaker_id'), 'group')
    if cur and (sp != cur['sp'] or w['start'] - cur['end'] > 0.8): L.append(cur); cur = None
    if not cur: cur = {'sp': sp, 'sid': w.get('speaker_id'), 'start': w['start'], 'end': w['end'], 'words': []}
    cur['end'] = w['end']; cur['words'].append(w)
L.append(cur)
assert len(L) == len(PLAN['lines']), f"{len(L)} dialogue lines but plan.json has {len(PLAN['lines'])}"
EVS = [w for w in stt['words'] if w.get('type') == 'audio_event' and w['end'] - w['start'] >= 1.2]
LEAD = 0.12
starts = []
for i, l in enumerate(L):
    s = l['start'] - LEAD
    for e_ in EVS:
        if e_.get('speaker_id') == l['sid'] and 0 <= l['start'] - e_['end'] < 0.6: s = min(s, e_['start'] - LEAD)
    starts.append(max(0.0, s) if i else 0.0)
raw = []
for i, l in enumerate(L):
    s, e = starts[i], (starts[i + 1] if i + 1 < len(L) else EP)
    items = PLAN['lines'][str(i + 1)]; cuts = [(s, items[0])]
    if len(items) > 1:
        img, rx = (items[1] + [None])[:2] if isinstance(items[1], list) else (items[1], None); t = None
        if rx:
            r = re.compile(nrm(rx))
            for w in l['words']:
                if w['start'] > l['start'] + 1.0 and r.search(nrm(w['text'])): t = w['start'] - LEAD; break
        if t is None:
            mid = (l['start'] + l['end']) / 2
            c = [w['end'] + 0.05 for w in l['words'][:-1] if w['text'].strip().endswith(('.', '!', '؟', '?', '،'))]
            t = min(c, key=lambda x: abs(x - mid)) if c else mid
        if s + 1.0 < t < e - 1.0: cuts.append((t, img))
        else: print('  ! second image skipped for line', i + 1)
    for j, (t, img) in enumerate(cuts): raw.append([t, cuts[j + 1][0] if j + 1 < len(cuts) else e, img])
for t, img in PLAN['events']:
    t -= LEAD; nxt = min([l['start'] - LEAD for l in L if l['start'] - LEAD > t + 0.3] + [EP])   # the next spoken word
    for k, (a0, a1, im) in enumerate(raw):
        if a0 <= t < a1:
            end = min(a1, nxt); parts = [[a0, t, im]] if t - a0 > 0.4 else []
            parts.append([max(a0, t) if t - a0 > 0.4 else a0, end, img])
            if a1 - end > 0.4: parts.append([end, a1, im])
            else: parts[-1][1] = a1
            raw[k:k + 1] = parts; break
shots = []
for a0, a1, im in raw:
    if shots and a1 - a0 < 0.3: shots[-1]['end'] = round(a1 + OFF, 3); continue
    n = max(1, round((a1 - a0) / 5.0)) if a1 - a0 > 6.5 else 1
    for k in range(n):
        shots.append({'start': round(a0 + (a1 - a0) * k / n + OFF, 3), 'end': round(a0 + (a1 - a0) * (k + 1) / n + OFF, 3), 'img': im, 'sub': k})
shots[0]['start'] = OFF; shots[-1]['end'] = round(OFF + EP, 3)
seen = set()
for s in shots:
    s['mahdi'] = s['img'] in PLAN['mahdi']
    s['tag'] = s['img'] in PLAN['tag'] and s['img'] not in seen and s['sub'] == 0; seen.add(s['img'])
used = {s['img'] for s in shots}; print('images used', len(used), 'shots', len(shots))
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
        RLM = '\u200f'                                   # a strong RTL mark first, so a line that starts with Latin
        ev.append([t0, t1, RLM + f"{lead}{txt}".replace(r'\N', '\\N' + RLM)])  # (Founder, GPU) still reads RTL
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
if not (a.reuse_video and os.path.exists(OUT + 'video_raw.mp4')):
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
