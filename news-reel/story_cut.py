#!/usr/bin/env python3
"""Make the Story version of a story reel (Instagram Stories take 3–60 s of video).

  python3 news-reel/story_cut.py --dir work/story   ->  <dir>/story.mp4

If the reel is ≤ 59.8 s it is copied. Otherwise it is cut at the end of the last beat that finishes
by 58.2 s and 1.7 s of the reel's end card (logo + question) is joined with a short crossfade.
"""
import argparse, json, shutil, subprocess
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument('--dir', required=True); a = ap.parse_args()
d = Path(a.dir).resolve(); tl = json.loads((d / 'timeline.json').read_text()); reel = d / 'reel.mp4'; out = d / 'story.mp4'
if tl['total'] <= 59.8:
    shutil.copy(reel, out)
else:
    cut = max(v['end'] for v in tl['lines'].values() if v['end'] <= 58.2) + 0.15
    e0 = tl['end_start'] + 0.1
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(reel), '-filter_complex',
        f"[0:v]trim=0:{cut},setpts=PTS-STARTPTS[a];[0:v]trim={e0}:{e0 + 1.7},setpts=PTS-STARTPTS[b];[a][b]xfade=transition=fade:duration=0.3:offset={cut - 0.3}[v];"
        f"[0:a]atrim=0:{cut},asetpts=PTS-STARTPTS[x];[0:a]atrim={e0}:{e0 + 1.7},asetpts=PTS-STARTPTS[y];[x][y]acrossfade=d=0.3[au]",
        '-map', '[v]', '-map', '[au]', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '256k',
        '-ar', '48000', '-movflags', '+faststart', str(out)], check=True)
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(out)], capture_output=True, text=True).stdout)
print(json.dumps({'story': str(out), 'duration': round(dur, 2)}))
if dur > 60: raise SystemExit('story too long')
