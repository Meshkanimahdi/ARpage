#!/usr/bin/env python3
"""Concept gate: quality control BEFORE any production spend (user rule 2026-10-28).

Mahdi: «یه کاری کن قبل از تولید همه چیز کنترل کیفیت بشه مخصوصا هوک کاور و تیترش». The headline, the hook, the
cover and the motion plan are written as text in <dir>/concept.json and judged by the independent critic before
any image, voice, engine or render. Nothing is generated until this passes.

  python3 news-reel/concept_gate.py --dir work/story --kind reel --history motion_history.json lint
  (independent critic reads concept.json → <dir>/critic_concept.json {"scores":{…}, "paraphrase": "…", "notes":{…}})
  python3 news-reel/concept_gate.py --dir work/story --kind reel check     # exit 0 pass, 3 fix and repeat

concept.json (reel):
  {"story": {"summary", "source", "date", "field"},
   "headlines": [{"text"}, {"text"}, {"text"}], "chosen": 0,
   "first_line": "<spoken line 1, must contain the chosen headline>",
   "hook": {"frame0": "<real photo/video of what, how big>", "motion": "push-in|whip|slam|…",
            "overlay": "<on-screen line from frame 0 = chosen headline>", "card": "<optional number/result card>"},
   "cover": {"subject": "<real face/product/place>", "image": "real|generated", "pos": "top|middle|bottom",
             "kicker": "", "sub": "", "logo": "<main subject only, or empty>"},
   "motion": {"prompt": "<catalog id>", "category": "", "scenes": [{"say": "", "layers": ["…", "…", "…", "…"]}]}}
concept.json (post): story, headlines, chosen, "format": "<prompts|checklist|before/after|…>",
   "slides": ["<slide 1 hook>", "<slide 2 useful item>", …, "<last: save/send ask>"], "cover": {subject, image}.
"""
import argparse, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
AI_WORDS = ('هوش مصنوعی', 'هوش‌مصنوعی')
BARS = {'reel': {'headline_clarity': 8, 'hook_plan': 7, 'cover_plan': 7, 'story_appeal': 7, 'motion_plan': 7},
        'post': {'headline_clarity': 8, 'cover_plan': 7, 'story_appeal': 7, 'save_value': 7}}


def words(s):
    return len(re.sub(r'[*|]', ' ', s or '').split())


def lint(d, kind, hist_path):
    c = json.loads((d / 'concept.json').read_text())
    f = []
    hs = c.get('headlines') or []
    if len(hs) < 3: f.append('give 3 headline candidates')
    try: h = hs[c.get('chosen', 0)]['text']
    except Exception: h = ''; f.append('chosen headline missing')
    n = words(h)
    if not 4 <= n <= 7: f.append(f'headline has {n} words (4–7)')
    if any(w in h for w in AI_WORDS): f.append('no «هوش مصنوعی» on the cover (HEADLINES.md)')
    for k in ('summary', 'source', 'date', 'field'):
        if not (c.get('story') or {}).get(k): f.append(f'story.{k} missing')
    cv = c.get('cover') or {}
    if not cv.get('subject'): f.append('cover.subject missing (a real face, product or place)')
    hist = json.loads(Path(hist_path).read_text()) if hist_path and Path(hist_path).exists() else []
    if kind == 'reel':
        if h and h.replace('*', '').replace('|', ' ').split()[0] not in (c.get('first_line') or ''):
            f.append('first_line must speak the chosen headline')
        hk = c.get('hook') or {}
        for k in ('frame0', 'motion', 'overlay'):
            if not hk.get(k): f.append(f'hook.{k} missing')
        if hk.get('overlay') and words(hk['overlay']) > 7: f.append('hook.overlay over 7 words')
        if cv.get('pos') not in ('top', 'middle', 'bottom'): f.append('cover.pos must be top|middle|bottom')
        elif hist and hist[-1].get('cover_pos') == cv.get('pos'): f.append(f"cover.pos {cv['pos']} repeats the previous reel")
        m = c.get('motion') or {}
        pid = (m.get('prompt') or '').split('-')[0]
        if not pid: f.append('motion.prompt missing')
        else:
            fam = json.loads((HERE / 'pm' / 'families.json').read_text())['family']
            mine = fam.get(pid, pid)
            used = [fam.get(x.get('prompt', '').split('-')[0], x.get('prompt', '').split('-')[0]) for x in hist[-10:]]
            if mine in used: f.append(f'motion prompt {pid} (family {mine}) was used in the last 10 reels')
        sc = m.get('scenes') or []
        if len(sc) < 6: f.append('plan at least 6 scenes')
        thin = [i + 1 for i, s in enumerate(sc) if len(s.get('layers') or []) < 4]
        if thin: f.append(f'scenes {thin} have fewer than 4 animated layers (RUNBOOK §4.0 rule 2b)')
        if hist and (c.get('story') or {}).get('field') in [x.get('field') for x in hist[-4:]]:
            f.append('story.field repeats one of the last 4 reels')
    else:
        sl = c.get('slides') or []
        if not c.get('format'): f.append('format missing (prompts, checklist, before/after, how-to, tools…)')
        if len(sl) < 5: f.append('plan the slides (at least 5)')
        elif not re.search(r'ذخیره|بفرست|سیو', sl[-1]): f.append('last slide must ask for the save or the send')
    out = {'lint_pass': not f, 'lint_fails': f}
    (d / 'concept_gate.json').write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False))
    return not f


def check(d, kind):
    g = json.loads((d / 'concept_gate.json').read_text()) if (d / 'concept_gate.json').exists() else {}
    if not g.get('lint_pass'): sys.exit('run lint first and fix its fails')
    p = d / 'critic_concept.json'
    if not p.exists(): sys.exit('no critic_concept.json: give concept.json to the independent critic')
    cr = json.loads(p.read_text()); sc = cr.get('scores', {})
    low = {k: sc.get(k) for k, bar in BARS[kind].items() if (sc.get(k) or 0) < bar}
    if not (cr.get('paraphrase') or '').strip(): low['paraphrase'] = 'missing'
    g.update({'pass': not low, 'scores': sc, 'low': low, 'rounds': g.get('rounds', 0) + 1})
    (d / 'concept_gate.json').write_text(json.dumps(g, ensure_ascii=False, indent=1))
    print(json.dumps(g, ensure_ascii=False))
    sys.exit(0 if not low else 3)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True); ap.add_argument('--kind', choices=['reel', 'post'], default='reel')
    ap.add_argument('--history'); ap.add_argument('cmd', choices=['lint', 'check'])
    a = ap.parse_args(); d = Path(a.dir)
    if a.cmd == 'lint': sys.exit(0 if lint(d, a.kind, a.history) else 3)
    check(d, a.kind)
