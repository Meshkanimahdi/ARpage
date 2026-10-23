#!/usr/bin/env python3
"""Carousel with music (user rule 2026-10-23).

The Instagram API cannot attach library music to a carousel, so each slide becomes a short video item that
carries one continuous piece of music: slide k plays the track from k*SEG seconds. The music runs on as the
viewer swipes, and the image stays exactly the approved slide, with a slow 3% push so it does not look frozen.

  python3 meshkani-pro/scripts/slides_music.py --slides s1.jpg s2.jpg s3.jpg --out work/final/ \
      (--music track.mp3 | --prompt "music prompt") [--seg 8]

Music: --music, or generated once with ElevenLabs /v1/music from --prompt (audio key from env, instrumental).
Out: <out>/slide1.mp4 … (1080x1350, H.264 yuv420p 30 fps, AAC 48 kHz, −16 LUFS, true peak ≤ −1.5),
<out>/music.mp3, and <out>/slides_music.json (durations, offsets, md5).
"""
import argparse, hashlib, json, os, subprocess, sys, urllib.request
from pathlib import Path


def run(*a):
    subprocess.run(a, check=True)


def gen_music(prompt, seconds, out):
    key = os.environ.get('Elevenlabs_API_KEY') or os.environ.get('ELEVENLABS_API_KEY')
    if not key:
        sys.exit('no ElevenLabs key in env')
    req = urllib.request.Request('https://api.elevenlabs.io/v1/music?output_format=mp3_44100_192', method='POST',
                                 headers={'xi-api-key': key, 'Content-Type': 'application/json'},
                                 data=json.dumps({'prompt': prompt, 'music_length_ms': int(seconds * 1000) + 2000,
                                                  'force_instrumental': True}).encode())
    with urllib.request.urlopen(req, timeout=240) as r:
        out.write_bytes(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--slides', nargs='+', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--music'); ap.add_argument('--prompt'); ap.add_argument('--seg', type=float, default=8.0)
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    n, seg = len(a.slides), a.seg
    music = out / 'music.mp3'
    if a.music:
        music.write_bytes(Path(a.music).read_bytes())
    elif not music.exists():
        if not a.prompt:
            sys.exit('give --music or --prompt')
        gen_music(a.prompt, n * seg, music)
    # one loudness-normalised master so every slide sounds the same
    master = out / 'music_master.wav'
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', str(music), '-af', 'loudnorm=I=-16:TP=-1.5:LRA=9', '-ar', '48000', '-ac', '2', str(master))
    report = {'segment_s': seg, 'slides': []}
    frames = int(seg * 30)
    for i, s in enumerate(a.slides):
        f = out / f'slide{i + 1}.mp4'
        # slow 3% push about the centre; first and last 0.25 s of audio fade to avoid clicks between slides
        vf = (f"scale=2160:2700,zoompan=z='1+0.03*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1350:fps=30,"
              "format=yuv420p")
        af = f"atrim=start={i * seg}:duration={seg},asetpts=PTS-STARTPTS,afade=t=in:d=0.25,afade=t=out:st={seg - 0.25}:d=0.25"
        run('ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', s, '-i', str(master), '-filter_complex',
            f'[0:v]{vf}[v];[1:a]{af}[a]', '-map', '[v]', '-map', '[a]', '-t', str(seg), '-c:v', 'libx264', '-preset', 'slow',
            '-crf', '18', '-r', '30', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-movflags', '+faststart', str(f))
        report['slides'].append({'file': f.name, 'from_s': i * seg, 'duration_s': seg, 'md5': hashlib.md5(f.read_bytes()).hexdigest()})
    (out / 'slides_music.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report))


if __name__ == '__main__':
    main()
