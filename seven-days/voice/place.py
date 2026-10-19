"""Place picked narration takes on the beat grid without overlaps; write voice/voice.wav and a timing report."""
import json, re, subprocess, sys, wave
import numpy as np
SR, B = 44100, 60 / 90
model = sys.argv[1] if len(sys.argv) > 1 else 'v4'
TEMPO = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
SKIP = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else set()
pick = json.load(open(f'voice/{model}/pick.json'))
pick.update(json.load(open(f'voice/{model}/pick-override.json')) if __import__('os').path.exists(f'voice/{model}/pick-override.json') else {})
lines = [l.rstrip('\n').split('|') for l in open('voice/script.txt', encoding='utf-8') if re.match(r'^V\d+\|', l)]
def load(f):
    y = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-ac', '1', '-ar', str(SR), '-af', f'highpass=f=80,atempo={TEMPO}', '-f', 'f32le', '-'], capture_output=True).stdout, np.float32)
    env = np.abs(y) > 10 ** (-42 / 20); idx = np.where(env)[0]
    a, b = max(0, idx[0] - int(.03 * SR)), min(len(y), idx[-1] + int(.12 * SR))
    return y[a:b]
total = int(123 * SR); out = np.zeros(total, np.float32); prev_end = 0; rep = []
for vid, slot, text in lines:
    if vid in SKIP: continue
    bar, beat = map(float, slot.split(','))
    want = (bar * 4 + beat) * B
    y = load(f'voice/{model}/{vid}_{pick[vid]}.mp3')
    start = max(want - .12, prev_end + .06)
    i = int(start * SR); n = min(len(y), total - i); out[i:i + n] += y[:n]
    prev_end = start + len(y) / SR
    rep.append((vid, want, start, start - want, len(y) / SR))
peak = np.abs(out).max(); out = out / peak * .9
st = np.repeat(out[:, None], 2, 1)
with wave.open('voice/voice.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
for r in rep: print('%s slot %.2f start %.2f late %.2f dur %.2f' % r)
print('max late %.2f' % max(r[3] for r in rep))
