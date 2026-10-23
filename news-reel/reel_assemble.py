#!/usr/bin/env python3
"""Join the logo intro with the rendered reel and mix narration, music and effects.

  python3 news-reel/reel_assemble.py --dir work/reel-2026-10-20   ->  <dir>/reel.mp4 (+ <dir>/cover.jpg)

Needs <dir>/timeline.json (reel_voice.mjs), <dir>/out/news.mp4 and <dir>/out/scenes.json (reel_render.mjs).
Music: <dir>/music.mp3 if present; otherwise generated once from spec.music_prompt with ElevenLabs
(audio key from env), falling back to the library bed news-reel/sfx/music60.mp3.
"""
import argparse, json, os, shutil, subprocess, sys, urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOGO = HERE.parent / 'logo-motion/release/meshkani-logo-1080x1920.mp4'
SFX = HERE / 'sfx'
START = 4.2


def run(*a):
    subprocess.run(a, check=True)


def probe(f):
    return float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(f)],
                                capture_output=True, text=True, check=True).stdout)


def music(d, spec, length):
    f = d / 'music.mp3'
    if f.exists():
        return f
    key = os.environ.get('Elevenlabs_API_KEY') or os.environ.get('ELEVENLABS_API_KEY')
    prompt = spec.get('music_prompt') or 'Modern tech news underscore, confident and curious, pulsing synth bass, light electronic percussion, clean minimal, steady 110 bpm, no vocals, suitable under a spoken narration'
    if key:
        try:
            req = urllib.request.Request('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192', method='POST',
                                         headers={'xi-api-key': key, 'Content-Type': 'application/json'},
                                         data=json.dumps({'prompt': prompt, 'music_length_ms': int(length * 1000) + 1500, 'force_instrumental': True}).encode())
            with urllib.request.urlopen(req, timeout=240) as r:
                f.write_bytes(r.read())
            print('music: generated from prompt')
            return f
        except Exception as e:  # keep going with the library bed
            print('music generation failed, using library bed:', e)
    shutil.copy(SFX / 'music60.mp3', f)
    return f


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); a = ap.parse_args()
    d = Path(a.dir).resolve(); out = d / 'out'
    spec = json.loads(((d / 'spec.json') if (d / 'spec.json').exists() else (d / 'story.json')).read_text())
    tl = json.loads((d / 'timeline.json').read_text())
    scenes = json.loads((out / 'scenes.json').read_text())
    END = tl['endcard'][1]
    START = tl.get('start', 4.2)     # 0 = story reel: no logo intro (the logo closes it on the end card)
    if START == 0:
        run('ffmpeg', '-y', '-loglevel', 'error', '-i', str(out / 'news.mp4'), '-c:v', 'copy', str(out / 'video.mp4'))
    # video: logo intro (first START+0.3 s) cross-faded into the reel
    else: run('ffmpeg', '-y', '-loglevel', 'error', '-i', str(LOGO), '-i', str(out / 'news.mp4'), '-filter_complex',
        f"[0:v]fps=30,trim=0:{START + 0.3},setpts=PTS-STARTPTS[a];[1:v]fps=30,setpts=PTS-STARTPTS[b];"
        f"[a][b]xfade=transition=fade:duration=0.3:offset={START}[v]",
        '-map', '[v]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-pix_fmt', 'yuv420p', str(out / 'video.mp4'))
    # audio
    ins, f, voice, fx = [], [], [], []

    def add(path, at, vol, extra=''):
        i = len(ins) // 2; ins.extend(['-i', str(path)]); ms = max(0, int(at * 1000))
        f.append(f"[{i}:a]aformat=sample_rates=48000:channel_layouts=stereo,{extra}volume={vol},adelay={ms}|{ms}[s{i}]")
        return f"[s{i}]"
    if START:
        fx.append(add(LOGO, 0, 1.0, f"atrim=0:{START + 0.5},afade=t=out:st={START - 0.2}:d=0.7,"))
    for k, v in tl['lines'].items():
        voice.append(add(d / 'voice/trim' / f'{k}.wav', v['start'] if isinstance(v, dict) else v[0], 1.0))
    m = music(d, spec, END)
    mus = add(m, max(0, START - 0.3) + spec.get('music_delay', 0), 0.30 if START else 0.22, f"aloop=loop=-1:size=2147483647,atrim=0:{END - START + 0.6},afade=t=in:d=0.6,afade=t=out:st={END - START - 0.9}:d=1.2,")
    prev_bg = None
    for s in scenes:
        if START == 0:   # story reel: many quick cuts -> soft swish, stronger on a background change
            fx.append(add(SFX / 'whoosh.mp3', s['t0'] - 0.12, 0.4 if s.get('bg') != prev_bg else 0.14)); prev_bg = s.get('bg')
        else:
            fx.append(add(SFX / 'whoosh.mp3', s['t0'] - 0.15, 0.45))
        for at, name, vol in s.get('sfx', []):   # engine cues (glass.html): clicks, key ticks, hits on hard cuts
            fx.append(add(SFX / f'{name}.mp3', at, vol))
        if s['type'] in ('grid', 'steps', 'points', 'icon_grid', 'network', 'counter'):
            fx.append(add(SFX / 'tick.mp3', s['t0'] + 0.7, 0.35))
        if s['type'] == 'divider':
            fx.append(add(SFX / 'riser.mp3', s['t0'] - 1.4, 0.35))
        if s['type'] in ('divider', 'end'):
            fx.append(add(SFX / 'hit.mp3', s['t0'], 0.6))
    f.append(f"{''.join(voice)}amix=inputs={len(voice)}:normalize=0,apad=whole_dur={END},asplit=2[voice][key]")
    f.append(f"{mus}[key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=350[duck]")
    f.append(f"[voice][duck]{''.join(fx)}amix=inputs={2 + len(fx)}:normalize=0,atrim=0:{END},loudnorm=I=-12:TP=-1.5:LRA=8[out]")
    run('ffmpeg', '-y', '-loglevel', 'error', *ins, '-filter_complex', ';'.join(f), '-map', '[out]', '-ar', '48000', str(out / 'mix.wav'))
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', str(out / 'video.mp4'), '-i', str(out / 'mix.wav'), '-c:v', 'copy',
        '-af', 'alimiter=limit=0.85:level=false', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest', '-movflags', '+faststart', str(d / 'reel.mp4'))
    # cover: a frame from the first news hook (after the logo)
    ct = spec.get('cover_t', START + 1.6)
    run('ffmpeg', '-y', '-loglevel', 'error', '-ss', str(ct), '-i', str(d / 'reel.mp4'), '-frames:v', '1', '-q:v', '2', str(d / 'cover.jpg'))
    st = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(d / 'reel.mp4'), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    lufs = [l.split()[1] for l in st.splitlines() if l.strip().startswith('I:')][-1]
    peak = [l.split()[1] for l in st.splitlines() if l.strip().startswith('Peak:')][-1]
    report = {'file': str(d / 'reel.mp4'), 'duration': round(probe(d / 'reel.mp4'), 2), 'lufs': float(lufs), 'true_peak_dbfs': float(peak),
              'bytes': (d / 'reel.mp4').stat().st_size, 'cover': str(d / 'cover.jpg')}
    (d / 'reel.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report))
    if report['duration'] > (92 if START == 0 else 61) or report['lufs'] > -12 or report['lufs'] < -15.5 or report['true_peak_dbfs'] > -1.0:
        print('QC FAILED: duration/loudness out of range'); sys.exit(6)


if __name__ == '__main__':
    main()
