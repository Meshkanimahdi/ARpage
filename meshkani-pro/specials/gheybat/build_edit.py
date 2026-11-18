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
import argparse, json, os, re, subprocess
from concurrent.futures import ThreadPoolExecutor

ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); a = ap.parse_args()
D = a.dir.rstrip('/') + '/'; OUT = D + 'out/'; os.makedirs(OUT + 'shots', exist_ok=True)
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

# ---- shot list: a cut at every line start, key panels win when they fall inside a line
used_keys, rot, shots = set(), {k: 0 for k in POOL}, []
def pick(pool, avoid):
    for _ in range(len(POOL[pool])):
        img = POOL[pool][rot[pool] % len(POOL[pool])]; rot[pool] += 1
        if img != avoid: return img
    return POOL[pool][0]
cuts = []
for i, u in enumerate(U):
    t0 = u['start'] if i else 0.0
    t1 = U[i + 1]['start'] if i + 1 < len(U) else EP
    keys_in = [(kt, k) for kt, k in KEYS if (kt, k) not in used_keys and t0 - 0.9 <= kt < t1]
    seg_start = t0
    for kt, k in keys_in:
        used_keys.add((kt, k))
        if kt - seg_start > 1.2: cuts.append([seg_start, None, u])
        cuts.append([max(seg_start, kt - 0.2), k, u]); seg_start = max(seg_start, kt - 0.2)
    if not keys_in: cuts.append([seg_start, None, u])
# merge tiny segments, fill pool images, split long holds
for j, c in enumerate(cuts): c.append(cuts[j + 1][0] if j + 1 < len(cuts) else EP)
merged = []
for c in cuts:
    if merged and c[3] - c[0] < 1.4 and c[1] is None: merged[-1][3] = c[3]; continue
    merged.append(c)
prev = None
for s, img, u, e in merged:
    pool = 'group' if u['ev'] else u['sp']
    if img is None and u['words'] and re.search(r'مهدی|مشکانی|مشگانی|رئیس|رییس', ' '.join(w['text'] for w in u['words'])) and pool != 'group':
        img = pick('mahdi', prev)   # every line that talks about Mahdi shows him
    seq, t = [], s
    first = img or pick(pool, prev)
    while e - t > 5.6:                          # split: speaker → listener/group → speaker …
        seq.append((t, t + 4.2, first)); t += 4.2
        alt = 'group' if len(seq) % 2 else pool
        first = pick(alt, first)
    seq.append((t, e, first))
    for a0, a1, im in seq:
        shots.append({'start': round(a0 + OFF, 3), 'end': round(a1 + OFF, 3), 'img': im}); prev = im
shots[0]['start'] = OFF
clean = []                                   # no flash shots: anything under 0.9 s joins the shot before it
for s in shots:
    if clean and s['end'] - s['start'] < 0.9: clean[-1]['end'] = s['end']; continue
    if clean and s['img'] == clean[-1]['img']: clean[-1]['end'] = s['end']; continue
    clean.append(s)
shots = clean
json.dump(shots, open(OUT + 'shots.json', 'w'), indent=0)

# ---- render each shot with a slow move (crop on a 1.14x scaled panel)
MOVES = [('(iw-ow)*t/{d}', '(ih-oh)/2'), ('(iw-ow)*(1-t/{d})', '(ih-oh)/2'), ('(iw-ow)/2', '(ih-oh)*t/{d}'), ('(iw-ow)/2', '(ih-oh)*(1-t/{d})')]
def render(i_s):
    i, s = i_s; d = s['end'] - s['start']; f = f"{OUT}shots/{i:04d}.mp4"
    if os.path.exists(f): return
    mx, my = MOVES[i % 4]
    vf = f"scale=1232:2190,crop=1080:1920:'{mx.format(d=d)}':'{my.format(d=d)}',fps=30,format=yuv420p"
    if i == 0: vf += ",fade=t=in:st=0:d=0.7"
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', f'{d:.3f}', '-i', f"{D}panels/{s['img']}.jpg", '-vf', vf,
                    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-r', '30', f], check=True)
with ThreadPoolExecutor(4) as ex: list(ex.map(render, enumerate(shots)))
# cover segment: title cover under the intro voice, then fade to black
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-t', f'{COVER_END:.3f}', '-i', D + 'cover_2_emoji.jpg', '-vf',
                f"scale=1080:1920,fps=30,format=yuv420p,fade=t=out:st={COVER_END - 0.6:.3f}:d=0.6", '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-r', '30', OUT + 'shots/cover.mp4'], check=True)
with open(OUT + 'concat.txt', 'w') as f:
    f.write(f"file 'shots/cover.mp4'\n" + ''.join(f"file 'shots/{i:04d}.mp4'\n" for i in range(len(shots))))
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', OUT + 'concat.txt', '-c', 'copy', OUT + 'video_raw.mp4'], check=True)

# ---- subtitles (ASS, RTL via libass/fribidi): ≤ 5 words a line, timed by word, speaker name in colour
FIX = [('مشگانی', 'مشکانی'), ('نووا', 'نُوا'), ('هووou', 'هوووو'), ('رییس', 'رئیس')]
def ts(t): h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60; return f"{h}:{m:02d}:{s:05.2f}"
ev = []
for u in U:
    if u['ev'] or not u['words']: continue
    ws = u['words']; chunks = [ws[k:k + 5] for k in range(0, len(ws), 5)]
    for n, ch in enumerate(chunks):
        txt = ' '.join(w['text'] for w in ch)
        for x, y in FIX: txt = txt.replace(x, y)
        t0, t1 = ch[0]['start'] + OFF, (chunks[n + 1][0]['start'] if n + 1 < len(chunks) else ch[-1]['end'] + 0.25) + OFF
        lead = f"{{\\c{COL[u['sp']]}}}{NAME[u['sp']]}{{\\c&HFFFFFF&}}: " if n == 0 else ''
        ev.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},Sub,,0,0,0,,{lead}{txt}")
ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sub,Vazirmatn Bold,64,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,6,2,2,90,90,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""" + '\n'.join(ev) + '\n'
open(OUT + 'subs.ass', 'w').write(ass)

# ---- audio: intro at 0, episode at OFF, mastered to −14 LUFS; burn subtitles; ~4.5 Mbps for Instagram
af = (f"[1:a]aresample=48000,loudnorm=I=-16:TP=-2[i];[2:a]aresample=48000,adelay={int(OFF * 1000)}|{int(OFF * 1000)}[e];"
      f"[i][e]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', OUT + 'video_raw.mp4', '-i', D + 'audio/intro.mp3', '-i', D + 'audio/ep1.mp3',
                '-filter_complex', af + f";[0:v]ass={OUT}subs.ass:fontsdir={D}fonts[v]", '-map', '[v]', '-map', '[a]',
                '-c:v', 'libx264', '-preset', 'medium', '-crf', '23', '-maxrate', '4500k', '-bufsize', '9000k', '-pix_fmt', 'yuv420p',
                '-c:a', 'aac', '-b:a', '160k', '-ar', '48000', '-movflags', '+faststart', '-shortest', OUT + 'gheybat_ep1.mp4'], check=True)
print('shots', len(shots), 'subtitle lines', len(ev), 'offset', OFF)
