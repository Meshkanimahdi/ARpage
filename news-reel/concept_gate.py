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
BARS = {'reel': {'headline_clarity': 6, 'hook_plan': 6, 'cover_plan': 6, 'story_appeal': 6, 'motion_plan': 6, 'share_value': 6},
        'post': {'headline_clarity': 6, 'cover_plan': 6, 'story_appeal': 6, 'save_value': 6, 'share_value': 6}}


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
    # north star (RUNBOOK §00, 2026-11-01): everyday life of Iranians; 2 of every 3 reels must be "life" stories
    st = c.get('story') or {}
    if st.get('life') is None or not st.get('life_impact'):
        f.append('story.life (true/false) and story.life_impact ("whose money/job/safety/health/family/daily life, and how") are required')
    if kind == 'reel' and not st.get('life') and hist_path and Path(hist_path).exists():
        prev = json.loads(Path(hist_path).read_text())[-2:]
        if len(prev) == 2 and not any(x.get('life') for x in prev):
            f.append('the last 2 reels were not "life" stories: this one must be (RUNBOOK §00)')
    cv = c.get('cover') or {}
    # user rule 2026-11-03 (RUNBOOK §00.20): no AI word or «از دید…» label anywhere on the cover, no repeated label
    cov_txt = ' '.join(str(cv.get(k) or '') for k in ('kicker', 'sub', 'twist', 'logo_label')) + ' ' + h
    if re.search(r'هوش[\s\u200c]*مصنوعی|از دید', cov_txt): f.append('cover uses «هوش مصنوعی» or an «از دید…» label (banned, RUNBOOK §00.20)')
    if re.search(r'[\U0001F300-\U0001FAFF]', cov_txt): f.append('no emoji on the cover (RUNBOOK §00.20)')
    if (c.get('series') or {}).get('name') and re.search(r'هوش[\s\u200c]*مصنوعی|از دید', c['series']['name']):
        f.append('series.name may not contain «هوش مصنوعی» or «از دید» (RUNBOOK §00.20)')
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
        # series decision cliffhanger (RUNBOOK §00.11a, 2026-11-03): every part but the last ends on a two-option vote
        se = c.get('series')
        if se:
            for k in ('name', 'part', 'of'):
                if not se.get(k): f.append(f'series.{k} missing')
            if se.get('part') and se.get('of') and se['part'] < se['of']:
                ch = se.get('choice') or {}
                if not ch.get('question') or len(ch.get('options') or []) != 2:
                    f.append('series.choice needs a question and exactly 2 options (decision cliffhanger, RUNBOOK §00.11a)')
                if not ch.get('ai_pick'): f.append('series.choice.ai_pick missing: what the AI recommends and why')
            if se.get('part', 1) > 1 and not se.get('vote'):
                f.append('series.vote missing: the real comment count of the previous part ({"1": n, "2": n}), RUNBOOK §00.11a')
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
