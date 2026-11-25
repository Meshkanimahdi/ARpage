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
   "cover": {"subject": "<real face/product/place>", "image": "real|generated", "pos": "(ignored: centred stack, §00.20)",
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
    # page purpose (user rule 2026-11-18, RUNBOOK §00.0, replaces the 2026-11-01 "2 of 3 life reels" rule):
    # «قرار بود اطلاع‌رسانی اخبار هوش مصنوعی باشه، یعنی نقش هوش مصنوعی در زندگی انسان‌ها، ولی الان همش توصیه‌های
    # تکراری…». Every reel stands on a real, recent AI development; the life impact is the angle, never the topic.
    st = c.get('story') or {}
    an = st.get('ai_anchor') or {}
    miss = [k for k in ('what', 'who', 'date', 'url') if not an.get(k)]
    if miss: f.append(f'story.ai_anchor {miss} missing: name the real AI development this stands on (what happened, who, date, source URL) — RUNBOOK §00.0')
    mix = st.get('mix')
    if mix not in ('news', 'practice', 'story'): f.append('story.mix must be news | practice | story (RUNBOOK §00.0)')
    import datetime as _dt
    try:
        age = (_dt.date.fromisoformat(str(st.get('date', ''))[:10]) - _dt.date.fromisoformat(str(an.get('date', ''))[:10])).days
        lim = 14 if mix in ('news', 'practice') else 30
        if age > lim: f.append(f'ai_anchor is {age} days old (max {lim} for mix={mix}): find a newer AI development')
    except ValueError:
        if an.get('date'): f.append('ai_anchor.date / story.date must be YYYY-MM-DD')
    # user rule 2026-11-25 (RUNBOOK §000): cover what everyone is talking about NOW, never repeat a story, teach fresh
    # things but not back to back. «تو داغ‌ترین خبرها رو اصلاً پوشش نمی‌دی… هیچ خبری نباید دوبار تکرار بشه مگر اینکه
    # آپدیت جدید ازش اومده باشه… آموزش موارد به‌روز، ولی نه پشت سر هم».
    _h = json.loads(Path(hist_path).read_text()) if hist_path and Path(hist_path).exists() else []
    th = str(st.get('theme') or '').strip().lower()
    if not th: f.append('story.theme missing: a short slug of the story family (e.g. ai-layoffs, gta6-launch) — §000 no-repeat rule')
    else:
        rep = [x for x in _h[-45:] if str(x.get('theme') or '').lower() == th]
        if rep and not st.get('update'):
            f.append(f"theme «{th}» was already covered in {rep[-1].get('reel')}: no story twice unless there is a real update (then say what is new in story.update) — §000")
    heat = st.get('heat')
    if heat not in ('hot', 'fresh'): f.append('story.heat must be hot (everyone is talking about it now, anchor ≤ 3 days) or fresh (anchor ≤ 7 days) — §000')
    try:
        _age = (_dt.date.fromisoformat(str(st.get('date', ''))[:10]) - _dt.date.fromisoformat(str(an.get('date', ''))[:10])).days
        if heat == 'hot' and _age > 3: f.append(f'heat=hot but the anchor is {_age} days old (max 3)')
        if heat == 'fresh' and _age > 7: f.append(f'heat=fresh but the anchor is {_age} days old (max 7)')
    except ValueError: pass
    if heat == 'hot' and len(st.get('trend_evidence') or []) < 2:
        f.append('heat=hot needs story.trend_evidence: at least 2 URLs from the live trend scan showing it is widely discussed in the last 72 h — §000')
    if kind == 'reel' and heat == 'fresh' and _h and _h[-1].get('heat') != 'hot':
        f.append('the previous reel was not a hot story: this one must be heat=hot (at most every second reel may be merely fresh) — §000')
    if kind == 'reel' and mix == 'practice' and _h and _h[-1].get('mix') == 'practice':
        f.append('two teaching (practice) reels in a row: the page must not turn into a tutorial page — §000')
    if not st.get('life_impact'): f.append('story.life_impact missing: what this AI development changes for the viewer (the angle, not the topic)')
    # household/safety advice drift (REEL-050…059: gas, heating, freezer food, antibiotics, scams, fake photos, blackouts)
    ADVICE = r'scam|fraud|phish|otp|verification code|voice clon|deepfake|fake (photo|shop|cure)|safety|readiness|emergenc|gas|heating|blackout|power cut|water shortage|food safety|freezer|antibiotic|medicine|health myth'
    blob = ' '.join(str(st.get(k, '')) for k in ('field', 'summary', 'life_impact')).lower()
    if kind == 'reel' and re.search(ADVICE, blob):
        hist_ = json.loads(Path(hist_path).read_text()) if hist_path and Path(hist_path).exists() else []
        recent = [x for x in hist_[-14:] if re.search(ADVICE, (str(x.get('field', '')) + ' ' + str(x.get('life', ''))).lower())]
        if recent: f.append(f'safety/scam/household-advice topic: at most 1 in 14 reels, last was {recent[-1].get("reel")} (RUNBOOK §00.0)')
        if mix != 'news': f.append('a safety/scam topic is allowed only as mix=news, built on a new AI development (a new scam technique, a new detection tool), never generic advice')
    # the mix: at least 4 of every 7 reels are mix=news
    if kind == 'reel' and mix and mix != 'news' and hist_path and Path(hist_path).exists():
        last6 = [x.get('mix') for x in json.loads(Path(hist_path).read_text())[-6:]]
        if len(last6) == 6 and last6.count('news') < 4: f.append(f'only {last6.count("news")} of the last 6 reels were AI news: this one must be mix=news (RUNBOOK §00.0)')
    cv = c.get('cover') or {}
    # user rule 2026-11-03 (RUNBOOK §00.20): no AI word or «از دید…» label anywhere on the cover, no repeated label
    cov_txt = ' '.join(str(cv.get(k) or '') for k in ('kicker', 'sub', 'twist', 'logo_label')) + ' ' + h
    if re.search(r'هوش[\s\u200c]*مصنوعی|از دید', cov_txt): f.append('cover uses «هوش مصنوعی» or an «از دید…» label (banned, RUNBOOK §00.20)')
    if re.search(r'[\U0001F300-\U0001FAFF]', cov_txt): f.append('no emoji on the cover (RUNBOOK §00.20)')
    if (c.get('series') or {}).get('name') and re.search(r'هوش[\s\u200c]*مصنوعی|از دید', c['series']['name']):
        f.append('series.name may not contain «هوش مصنوعی» or «از دید» (RUNBOOK §00.20)')
    if not cv.get('subject'): f.append('cover.subject missing (a real face, product or place)')
    if kind == 'reel' and not (hist_path and Path(hist_path).exists()):
        f.append('--history motion_history.json is required for a reel (the prompt-family, category, field and voice blocks need it)')
    hist = json.loads(Path(hist_path).read_text()) if hist_path and Path(hist_path).exists() else []
    if kind == 'reel':
        if h and h.replace('*', '').replace('|', ' ').split()[0] not in (c.get('first_line') or ''):
            f.append('first_line must speak the chosen headline')
        hk = c.get('hook') or {}
        for k in ('frame0', 'motion', 'overlay'):
            if not hk.get(k): f.append(f'hook.{k} missing')
        if hk.get('overlay') and words(hk['overlay']) > 7: f.append('hook.overlay over 7 words')
        # 2026-11-03 (RUNBOOK §00.20): all cover text in one centred stack; position no longer varies or is checked
        m = c.get('motion') or {}
        pid = (m.get('prompt') or '').split('-')[0]
        if not pid: f.append('motion.prompt missing')
        else:
            fam = json.loads((HERE / 'pm' / 'families.json').read_text())['family']
            mine = fam.get(pid, pid)
            used = [fam.get(x.get('prompt', '').split('-')[0], x.get('prompt', '').split('-')[0]) for x in hist[-14:]]
            if mine in used: f.append(f'motion prompt {pid} (family {mine}) was used in the last 14 reels')
            # user rule 2026-11-18 (RUNBOOK §00.24): plate-led looks (hand-made, story, editorial) at most 1 reel in 4;
            # and 1 reel in 4 runs on a newly built engine from an unused catalog prompt, until 40 engines exist
            PLATE = ('HAND', 'STORY', 'EDIT')
            if (m.get('category') or '').upper() in PLATE and any((x.get('category') or '').upper() in PLATE for x in hist[-3:]):
                f.append(f"motion.category {m.get('category')} is a picture-led look and one was used in the last 3 reels: pick a data/UI/type/3D/explainer prompt")
            built = len([x for x in (HERE / 'pm').glob('[0-9]*.html') if 'cover-bg' not in x.name])
            if built < 40 and len(hist) >= 3 and not m.get('engine_new') and not any(x.get('engine_new') for x in hist[-3:]):
                f.append(f'only {built} of 85 motion prompts have an engine and the last 3 reels reused old ones: this reel builds a NEW engine from an unused prompt (motion.engine_new: true) — RUNBOOK §00.24')
            leads = [str(sc_.get('lead', '')).lower() for sc_ in (m.get('scenes') or [])]
            if leads and any(not l for l in leads): f.append('every motion scene needs `lead`: data | chart | ui | type | 3d | diagram | photo')
            if leads and leads.count('photo') > (int(len(leads) * .6) if st.get('heat') == 'hot' and m.get('real_footage') else max(1, len(leads) // 4)): f.append(f"{leads.count('photo')} of {len(leads)} scenes are photo-led (max a quarter): redesign them as data, chart, UI or type scenes")
            # user rule 2026-11-25 (RUNBOOK §000.6): real pictures are welcome, a slideshow is not. «استفاده از تصاویر
            # واقعی خوبه اما به شرطی که با ادیت‌های موشن‌گرافی خوب همراه باشه، نه فقط با یه ساند افکت ساده و اسلاید شدن»
            if m.get('real_footage'):
                TREAT = ('cutout', 'parallax', 'tracked', 'callout', 'mask', 'kinetic', 'data', 'chart', 'counter', 'ui', 'split', 'annotation', 'morph', '3d', 'compare', 'zoom-to-detail', 'outline', 'timeline')
                scs = m.get('scenes') or []
                for i, sc_ in enumerate(scs):
                    if str(sc_.get('lead', '')).lower() != 'photo': continue
                    tr = [str(t_).lower() for t_ in (sc_.get('treatment') or [])]
                    good = {k for k in TREAT for t_ in tr if k in t_}
                    if len(good) < 2: f.append(f"scene {i + 1} shows a real picture without a motion-graphics treatment: give `treatment` with at least 2 of {', '.join(TREAT[:10])}… (a push-in, slide or zoom alone is a slideshow) — §000.6")
                run = 0
                for sc_ in scs:
                    run = run + 1 if str(sc_.get('lead', '')).lower() == 'photo' else 0
                    if run > 2: f.append('more than 2 picture-led scenes in a row: put a data, chart, UI or type scene between them — §000.6'); break
            if hist and (m.get('category') or '') == hist[-1].get('category'): f.append(f"motion.category {m.get('category')} repeats the previous reel")
        sc = m.get('scenes') or []
        if len(sc) < 6: f.append('plan at least 6 scenes')
        thin = [i + 1 for i, s in enumerate(sc) if len(s.get('layers') or []) < 4]
        if thin: f.append(f'scenes {thin} have fewer than 4 animated layers (RUNBOOK §4.0 rule 2b)')
        # character casting (RUNBOOK §00.21, 2026-11-03): who speaks or is shown, with gender and age
        cast = c.get('cast') or {}
        if not cast: f.append('cast missing: list every character who speaks or is shown (gender, age, role, voice) — RUNBOOK §00.21')
        for nm, cc in cast.items():
            miss = [k for k in ('gender', 'age', 'role') if not cc.get(k)]
            if miss: f.append(f'cast «{nm}» missing {miss}')
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
            # one week between parts (RUNBOOK §00.11b, 2026-11-04)
            if se.get('part', 1) > 1 and se.get('name'):
                import datetime as _dt
                prev = [x for x in hist if x.get('series') == se['name'] and x.get('series_part') == se['part'] - 1]
                d0 = (c.get('story') or {}).get('date', '')
                if prev and d0:
                    try:
                        gap = (_dt.date.fromisoformat(d0[:10]) - _dt.date.fromisoformat(prev[-1]['date'][:10])).days
                        if gap < 7: f.append(f"series part {se['part']} is {gap} days after part {se['part'] - 1}: wait 7 days, same weekday and slot (RUNBOOK §00.11b)")
                    except ValueError: pass
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
