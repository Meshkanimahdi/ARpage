#!/usr/bin/env python3
"""Join the logo intro with the rendered reel and mix narration, music and effects.

  python3 news-reel/reel_assemble.py --dir work/reel-2026-10-20   ->  <dir>/reel.mp4 (+ <dir>/frame_cover.jpg, a video frame; never the designed cover.jpg)

Needs <dir>/timeline.json (reel_voice.mjs), <dir>/out/news.mp4 and <dir>/out/scenes.json (reel_render.mjs).
Music: library only (news-reel/music/*.mp3 via story.json "music" or picked by content id); never generated (Mahdi 2026-11-13).
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
    """Library music only (Mahdi 2026-11-13: «به هیچ عنوان از ای پی ای الونلبز برای ساخت موسیقی و افکت استفاده نکن،
    فقط از کتابخونش»). Never calls a music/SFX generation API. Order: <dir>/music.mp3 (copied from the library),
    story.json "music" (a file under news-reel/music/), else a library track picked from the content id."""
    f = d / 'music.mp3'
    if f.exists():
        return f
    lib = sorted((HERE / 'music').glob('*.mp3'))
    want = spec.get('music')
    src = None
    if want:
        c = Path(want) if Path(want).is_absolute() else (HERE.parent / want)
        if c.exists() and c.resolve().parent == (HERE / 'music').resolve():
            src = c
        else:
            print('music: story.json music is not a library file, picking from the library:', want)
    if src is None and lib:
        n = sum(map(ord, str(spec.get('content_id', '')))) % len(lib)
        src = lib[n]
    shutil.copy(src or (SFX / 'music60.mp3'), f)
    print('music: library', (src or SFX / 'music60.mp3').name)
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
        '-map', '[v]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '17', '-maxrate', '12M', '-bufsize', '24M', '-pix_fmt', 'yuv420p', str(out / 'video.mp4'))
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
    # sound design (user rule 2026-10-29: «همشون دارند از یه ساند افکت برای تغییر تصاویر استفاده میکنند… فیش،فیش… اعصاب
    # همه رو بهم ریخته»): no automatic whoosh on every cut. Engine cues first; scenes without a cue get a varied,
    # motion-matched sound on every other cut; the same sound never twice in a row; whoosh at most 2 per reel,
    # 6 s apart; at most one effect per 1.2 s. Missing library files are skipped (news-reel/sfx/generate.mjs).
    by_type = {'counter': 'counter_tick', 'stat': 'counter_tick', 'chart': 'sweep_soft', 'bars': 'sweep_soft', 'grid': 'pop',
               'points': 'pop', 'steps': 'pop', 'icon_grid': 'pop', 'ui': 'tap', 'chat': 'notify', 'network': 'glass_ping',
               'logo': 'shimmer', 'divider': 'riser', 'end': 'hit'}
    palette = spec.get('sfx_palette') or ['pop', 'tap', 'glass_ping', 'shimmer', 'click', 'sweep_soft']   # story.json may set its own (SFX-set variety, §00.22)
    cues = []
    for i, s in enumerate(scenes):
        mine = [(at, name, vol) for at, name, vol in s.get('sfx', [])]
        if mine: cues += mine
        elif i == 0 or i % 2 == 0:
            cues.append((s['t0'] - 0.03, by_type.get(s.get('type'), palette[i % len(palette)]), 0.32))
        if s.get('type') == 'divider': cues.append((s['t0'] - 1.4, 'riser', 0.3))
    cues.sort()
    kept, last_t, last_name, whooshes = [], -9, None, []
    for at, name, vol in cues:
        if name == 'whoosh':
            if len(whooshes) >= 2 or (whooshes and at - whooshes[-1] < 6): name = palette[-1]
            else: whooshes.append(at)
        if name == last_name:
            name = next(p for p in palette if p != last_name and p != name)
        if at - last_t < 1.2 or not (SFX / f'{name}.mp3').exists(): continue
        kept.append((at, name, min(vol, 0.45))); last_t, last_name = at, name
    for at, name, vol in kept:
        fx.append(add(SFX / f'{name}.mp3', at, vol))
    sfx_counts = {}
    for _, name, _ in kept: sfx_counts[name] = sfx_counts.get(name, 0) + 1
    # mix & master (user rule 2026-11-02: «صداهای تولید شده خیلی خشک و بی‌روحه… میکس و مسترینگ صدا خیلی مهمه»).
    # Voice bus: clean lows, cut mud, presence and air, de-ess, gentle compression, a short room so it is not dry.
    VOICE_FX = ("highpass=f=80,lowpass=f=15000,equalizer=f=250:t=q:w=1.2:g=-2.5,equalizer=f=3200:t=q:w=1.4:g=3,"
                "equalizer=f=9000:t=h:w=3000:g=2,deesser=i=0.35,"
                "acompressor=threshold=-20dB:ratio=3:attack=6:release=140:makeup=3,"
                "aecho=0.85:0.6:23|41:0.07|0.04")
    f.append(f"{''.join(voice)}amix=inputs={len(voice)}:normalize=0,{VOICE_FX},apad=whole_dur={END},asplit=2[voice][key]")
    # Music bus: carve room for the voice (2–4 kHz), keep the lows warm, duck smoothly under speech.
    f.append(f"{mus}highpass=f=35,equalizer=f=2800:t=q:w=1.3:g=-4[mbus]")
    f.append("[mbus][key]sidechaincompress=threshold=0.04:ratio=6:attack=25:release=450[duck]")
    # Master: glue compression, then loudness for Instagram (≈ -14 LUFS, true peak -1.5).
    f.append(f"[voice][duck]{''.join(fx)}amix=inputs={2 + len(fx)}:normalize=0,atrim=0:{END},"
             f"acompressor=threshold=-14dB:ratio=2:attack=20:release=250,loudnorm=I=-14:TP=-1.5:LRA=9[out]")
    run('ffmpeg', '-y', '-loglevel', 'error', *ins, '-filter_complex', ';'.join(f), '-map', '[out]', '-ar', '48000', str(out / 'mix.wav'))
    run('ffmpeg', '-y', '-loglevel', 'error', '-i', str(out / 'video.mp4'), '-i', str(out / 'mix.wav'), '-c:v', 'copy',
        '-af', 'alimiter=limit=0.8:level=false', '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-shortest', '-movflags', '+faststart', str(d / 'reel.mp4'))
    # cover: a frame from the first news hook (after the logo)
    ct = spec.get('cover_t', START + 1.6)
    run('ffmpeg', '-y', '-loglevel', 'error', '-ss', str(ct), '-i', str(d / 'reel.mp4'), '-frames:v', '1', '-q:v', '2', str(d / 'frame_cover.jpg'))   # never cover.jpg: that is the designed cover (cover_render.mjs)
    st = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(d / 'reel.mp4'), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    lufs = [l.split()[1] for l in st.splitlines() if l.strip().startswith('I:')][-1]
    peak = [l.split()[1] for l in st.splitlines() if l.strip().startswith('Peak:')][-1]
    report = {'file': str(d / 'reel.mp4'), 'duration': round(probe(d / 'reel.mp4'), 2), 'lufs': float(lufs), 'true_peak_dbfs': float(peak),
              'bytes': (d / 'reel.mp4').stat().st_size, 'frame_cover': str(d / 'frame_cover.jpg'), 'sfx': sfx_counts}
    (d / 'reel.json').write_text(json.dumps(report, indent=1))
    print(json.dumps(report))
    if report['duration'] > 152 or report['lufs'] > -12 or report['lufs'] < -15.5 or report['true_peak_dbfs'] > -1.0:
        print('QC FAILED: duration/loudness out of range'); sys.exit(6)


if __name__ == '__main__':
    main()
