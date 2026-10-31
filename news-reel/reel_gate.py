#!/usr/bin/env python3
"""Hard gate before a reel may become READY, and again at publish time (user rule 2026-10-25).

Mahdi: «ریلز بدون اینکه مؤلفه‌های کافی رو داشته باشه داره منتشر می‌شه… کاور… تیتر بسیار کوچیکه…
چرا همه ریلزا داره با یه سبک پرامپت درست می‌شه». Instructions alone were not enough: REEL-010 went out with a
video frame as its cover (reel_assemble.py used to overwrite cover.jpg) and with prompt 019 built on the 211
engine, so it looked like the reels before it. This script checks the real files, not the run's own notes.

  python3 news-reel/reel_gate.py --dir work/story --history motion_history.json \
      [--reel R.mp4 --cover C.jpg]        # publish time: the files downloaded from Drive

Checks (any failure = exit 3, reasons in <dir>/gate.json):
  1. attention: reel_qa.py passes (empty screen, holds, rhythm, hook, 40–55 s);
  2. cover is the designed one: cover_report.json exists, has no issues, font ≥ 120 px, ≤ 9 words, and the
     cover file's md5 equals the report's md5; the cover is not a frame of the reel;
  3. cover position differs from the previous reel's (history);
  4. motion variety: story.json `motion_prompt` (catalog id) and `engine` (news-reel/pm/<file>.html) are set;
     its prompt family (pm/families.json: renamed twins of one prompt) was not used in the last 10 reels;
     the engine file name starts with that id (a prompt may not borrow another prompt's engine); neither the
     id nor the engine was used in the last 10 reels of the history; the category differs from the previous reel;
  5. critic: <dir>/critic.json from an independent reviewer (RUNBOOK §4.4) with every score ≥ 7.
On success it prints the history entry to append after publishing.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

from PIL import Image, ImageChops, ImageStat

HERE = Path(__file__).resolve().parent


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def is_frame_of(cover, reel, tmp):
    """True when the cover looks like a frame of the reel (mean abs diff to the closest sampled frame)."""
    tmp.mkdir(parents=True, exist_ok=True)
    for f in tmp.glob('g_*.png'):
        f.unlink()
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', str(reel), '-vf', 'fps=2,scale=108:192', str(tmp / 'g_%04d.png')], check=True)
    c = Image.open(cover).convert('L').resize((108, 192))
    best = min(ImageStat.Stat(ImageChops.difference(c, Image.open(f).convert('L'))).mean[0] for f in tmp.glob('g_*.png'))
    return best < 15, round(best, 2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--history', required=True, help='motion_history.json: [{"reel","date","prompt","engine","category","cover_pos"}…], newest last')
    ap.add_argument('--reel'); ap.add_argument('--cover')
    ap.add_argument('--layout', choices=['photo', 'designed'], default=None)
    a = ap.parse_args()
    d = Path(a.dir)
    reel = Path(a.reel) if a.reel else d / 'reel.mp4'
    cover = Path(a.cover) if a.cover else d / 'cover.jpg'
    fails, info = [], {}
    story = json.loads((d / 'story.json').read_text())
    hist = json.loads(Path(a.history).read_text()) if Path(a.history).exists() else []
    last10 = hist[-10:]

    # 1. attention
    layout = a.layout or story.get('layout', 'photo')
    q = subprocess.run([sys.executable, str(HERE / 'reel_qa.py'), str(reel), '--out', str(d / 'qa'), '--layout', layout], capture_output=True, text=True)
    info['reel_qa'] = q.stdout.splitlines()[0] if q.stdout else q.stderr[-300:]
    if q.returncode != 0:
        fails.append('attention gate (reel_qa.py) failed')

    # 2. cover
    rep_p = d / 'cover_report.json'
    if not rep_p.exists():
        fails.append('no cover_report.json: the cover was not rendered with cover_render.mjs')
    else:
        rep = json.loads(rep_p.read_text()); info['cover'] = {k: rep.get(k) for k in ('font_px', 'words', 'pos', 'title')}
        if rep.get('issues'): fails.append('cover issues: ' + '; '.join(rep['issues']))
        if (rep.get("font_px") or 0) < 120: fails.append(f"cover headline too small ({rep.get('font_px')} px < 120)")
        if (rep.get('words') or 99) > 9: fails.append(f"cover headline too long ({rep.get('words')} words > 9)")
        if not cover.exists(): fails.append('cover file missing')
        elif md5(cover) != rep.get('md5'): fails.append('cover file is not the rendered designed cover (md5 mismatch): a frame or an old file')
        if hist and rep.get('pos') and hist[-1].get('cover_pos') == rep.get('pos'):
            fails.append(f"cover headline position '{rep.get('pos')}' repeats the previous reel's")
    if cover.exists() and reel.exists():
        fr, diff = is_frame_of(cover, reel, d / 'qa' / 'gate')
        info['cover_vs_frames'] = diff
        if fr: fails.append(f'cover is a frame of the video (diff {diff})')

    # 4. motion variety
    pid, eng, cat = story.get('motion_prompt', ''), story.get('engine', ''), story.get('motion_category', '')
    pid_num = pid.split('-')[0] if pid else ''
    info['motion'] = {'prompt': pid, 'engine': eng, 'category': cat}
    if not pid or not eng:
        fails.append('story.json must name motion_prompt (catalog id) and engine (news-reel/pm/<file>.html or glass.html)')
    else:
        base = Path(eng).name
        if not (base.startswith(pid_num + '-') or (pid_num == '089' and base == 'glass.html')):
            fails.append(f'engine {base} is not the engine of prompt {pid} (a prompt may not borrow another engine)')
        used_p = [h.get('prompt', '').split('-')[0] for h in last10]
        used_e = [Path(h.get('engine', '')).name for h in last10]
        if pid_num in used_p: fails.append(f'prompt {pid_num} was used in the last 10 reels')
        # many catalog prompts are the same text under another name (pm/families.json): block the family too
        fp = HERE / 'pm' / 'families.json'
        fam = json.loads(fp.read_text())['family'] if fp.exists() else {}
        mine_f = fam.get(pid_num, pid_num)
        twins = [p for p in used_p if p and fam.get(p, p) == mine_f and p != pid_num]
        if twins: fails.append(f'prompt {pid_num} is the same prompt family ({mine_f}) as {twins[0]}, used in the last 10 reels')
        if base in used_e: fails.append(f'engine {base} was used in the last 10 reels')
        # a new engine must really be new: not a renamed copy of an engine used in the last 10 reels
        ep = (HERE.parent / eng) if not Path(eng).is_absolute() else Path(eng)
        if ep.exists():
            import difflib
            mine = ep.read_text().splitlines()
            for h in last10:
                op = HERE.parent / h.get('engine', '')
                if h.get('engine') and op.exists() and op.name != ep.name:
                    r = difflib.SequenceMatcher(None, mine, op.read_text().splitlines()).ratio()
                    if r > 0.6: fails.append(f'engine {ep.name} is {r:.0%} the same code as {op.name} (used by {h.get("reel")}): build the prompt\'s own look')
        if not cat: fails.append('story.json must name motion_category (UI, TYPE, EDIT, STORY, 3D, EXPL, …)')
        elif hist and hist[-1].get('category') == cat: fails.append(f'category {cat} repeats the previous reel')

    # 4b. topic cooldown (user rule 2026-10-26: robots/workers two days running): the field must differ from the
    # last 4 reels (≈ 36 h), and from the posts of the last 2 days when the run passes them in story.json → recent_fields
    fld = story.get('field', '')
    recent = [h.get('field', '') for h in hist[-4:]] + list(story.get('recent_fields', []))
    if not fld: fails.append('story.json must name field (topic family, e.g. beauty, robotics, health, money)')
    elif fld in recent: fails.append(f'field {fld} repeats a recent reel/post ({recent})')

    # 4b2. concept gate (user rule 2026-10-28): the concept was approved before any production
    cg = d / 'concept_gate.json'
    if not cg.exists() or not json.loads(cg.read_text()).get('pass'):
        fails.append('no passing concept_gate.json: approve headline, hook, cover and motion plan before production (concept_gate.py)')

    # 4b3. sound design (user rule 2026-10-29): no repeated whoosh, varied effects
    rj = d / 'reel.json'
    if rj.exists():
        sx = json.loads(rj.read_text()).get('sfx')
        if sx is None: fails.append('reel.json has no sfx report: re-assemble with the current reel_assemble.py')
        else:
            tot = sum(sx.values())
            if sx.get('whoosh', 0) > 2: fails.append(f"{sx['whoosh']} whooshes (max 2)")
            if tot >= 5 and max(sx.values()) > 0.4 * tot: fails.append(f'one sound effect is over 40% of all effects {sx}')

    # 4b4. voice rotation (user rule 2026-10-31): not the same narrator as the last 2 reels
    vc = story.get('voice', '')
    if not vc: fails.append('story.json must name voice')
    elif vc in [h.get('voice') for h in hist[-2:]]: fails.append(f'voice {vc} was used in one of the last 2 reels: pick another from audio_library.json')

    # 4c. preflight (user rule 2026-10-27): cover, headline and hook were judged on stills before the full render
    pf = d / 'preflight.json'
    if not pf.exists() or not json.loads(pf.read_text()).get('pass'):
        fails.append('no passing preflight.json: judge the cover and the first 2 s on stills before rendering (preflight.py)')

    # 5. independent critic
    cp = d / 'critic.json'
    if not cp.exists():
        fails.append('no critic.json (independent review, RUNBOOK §4.4)')
    else:
        cr = json.loads(cp.read_text()); sc = cr.get('scores', {}); info['critic'] = sc
        low = {k: v for k, v in sc.items() if (v or 0) < 7}
        need = ('cover_stop_power', 'headline_clarity', 'hook', 'visual_match', 'style_distinct', 'motion_richness')
        miss = [k for k in need if k not in sc]
        if miss: fails.append(f'critic.json is missing scores {miss} (RUNBOOK §4.4 step 5; motion_richness = rule 2b)')
        if low: fails.append(f'critic scores below 7: {low}')

    out = {'pass': not fails, 'fails': fails, 'info': info,
           'history_entry': {'reel': story.get('content_id', ''), 'date': story.get('date', ''), 'prompt': pid, 'engine': eng,
                             'category': cat, 'field': story.get('field', ''), 'voice': story.get('voice', ''), 'cover_pos': (json.loads(rep_p.read_text()).get('pos') if rep_p.exists() else '')}}
    (d / 'gate.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False))
    sys.exit(0 if not fails else 3)


if __name__ == '__main__':
    main()
