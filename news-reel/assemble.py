#!/usr/bin/env python3
"""Join logo intro + rendered news part and mix narration, music and effects.
   python3 assemble.py  ->  release/reel.mp4"""
import json, subprocess
sc = json.load(open('scenes.json')); tl = json.load(open('voice/timeline.json'))['lines']
END = sc['end']; START = sc['start']
LOGO_V = '../logo-motion/out/meshkani-logo-1080x1920.mp4'; LOGO_A = '../logo-motion/out/mix.wav'
# --- video: logo intro (first START+0.3 s) cross-faded into the news part
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', LOGO_V, '-i', 'out/news.mp4', '-filter_complex',
  f"[0:v]fps=30,trim=0:{START+0.3},setpts=PTS-STARTPTS[a];[1:v]fps=30,setpts=PTS-STARTPTS[b];"
  f"[a][b]xfade=transition=fade:duration=0.3:offset={START}[v]",
  '-map', '[v]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', 'out/video.mp4'], check=True)
# --- audio
ins, f, mixv, mixfx = [], [], [], []
def add(path, at, vol, extra=''):
    i = len(ins) // 2; ins.extend(['-i', path]); ms = int(at * 1000)
    f.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,{extra}volume={vol},adelay={ms}|{ms}[s{i}]"); return f"[s{i}]"
mixfx.append(add(LOGO_A, 0, 1.0, f"atrim=0:{START+0.5},afade=t=out:st={START-0.2}:d=0.7,"))
for k, (a, b) in tl.items(): mixv.append(add(f'voice/trim/{k}.wav', a, 1.0))
music = add('sfx/music.mp3', START - 0.3, 0.30, f"afade=t=in:d=0.6,afade=t=out:st={END-START-0.9}:d=1.2,")
for s in sc['scenes']: mixfx.append(add('sfx/whoosh.mp3', s['t0'] - 0.15, 0.45))
slide2 = next(s for s in sc['scenes'] if s.get('focus')); mixfx.append(add('sfx/tick.mp3', slide2['t0'] + 0.5, 0.35))
mixfx.append(add('sfx/hit.mp3', sc['scenes'][-1]['t0'], 0.6))
f.append(f"{''.join(mixv)}amix=inputs={len(mixv)}:normalize=0,apad=whole_dur={END},asplit=2[voice][key]")
f.append(f"{music}[key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[duck]")
f.append(f"[voice][duck]{''.join(mixfx)}amix=inputs={2+len(mixfx)}:normalize=0,atrim=0:{END},"
         f"loudnorm=I=-13:TP=-2:LRA=8[out]")
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *ins, '-filter_complex', ';'.join(f), '-map', '[out]', '-ar', '48000', 'out/mix.wav'], check=True)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', 'out/video.mp4', '-i', 'out/mix.wav', '-c:v', 'copy', '-af', 'volume=-1.6dB,alimiter=limit=0.8', '-c:a', 'aac', '-b:a', '256k',
                '-shortest', '-movflags', '+faststart', 'release/reel.mp4'], check=True)
print('ok')
