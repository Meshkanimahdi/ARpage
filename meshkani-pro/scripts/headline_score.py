#!/usr/bin/env python3
"""Score cover / hook headline candidates (meshkani-pro/HEADLINES.md, user rule 2026-10-24).

  python3 meshkani-pro/scripts/headline_score.py --facts work/story/dossier.json --cands work/story/headlines.txt \
      [--recent recent_headlines.txt] [--lexicon meshkani-pro/headline_lexicon.json]

headlines.txt: one candidate per line, optionally prefixed with its angle letter: "A: شغلت امنه؟ لوله‌کش شو".
Prints a ranked JSON list. A candidate failing the truth gate (a number or Latin name absent from the facts)
is ranked last and marked "truth_fail". The score guides the choice; the agent still decides (top 3).
"""
import argparse, json, re
from pathlib import Path

FA = str.maketrans('۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩', '01234567890123456789')
norm = lambda s: s.translate(FA).replace('ي', 'ی').replace('ك', 'ک').replace('‌', ' ').lower()


def flatten(x):
    if isinstance(x, dict): return ' '.join(flatten(v) for v in x.values())
    if isinstance(x, list): return ' '.join(flatten(v) for v in x)
    return str(x)


def has(text, words):
    t = ' ' + norm(text) + ' '
    return [w for w in words if (' ' + norm(w) + ' ') in t or (len(norm(w)) > 3 and norm(w) in t)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--facts', required=True); ap.add_argument('--cands', required=True)
    ap.add_argument('--recent'); ap.add_argument('--lexicon', default=str(Path(__file__).resolve().parent.parent / 'headline_lexicon.json'))
    a = ap.parse_args()
    L = json.loads(Path(a.lexicon).read_text())
    fp = Path(a.facts); facts = norm(flatten(json.loads(fp.read_text())) if fp.suffix == '.json' else fp.read_text())
    recent = [set(norm(x).split()) for x in Path(a.recent).read_text().splitlines() if x.strip()] if a.recent else []
    out = []
    for line in Path(a.cands).read_text().splitlines():
        line = line.strip()
        if not line: continue
        m = re.match(r'^([A-G])\s*[:|]\s*(.+)$', line); angle, text = (m.group(1), m.group(2)) if m else ('?', line)
        words = [w for w in re.split(r'\s+', text.replace('|', ' ')) if w]
        n, s, why, fail = len(words), 0.0, [], []
        s += 2 if 2 <= n <= 6 else (0 if n <= 8 else -3); why.append(f'{n} words')
        ai = has(text, L['ai_fatigue'])
        if ai:
            s -= 8 if norm(words[0]) in [norm(x) for x in L['ai_fatigue']] or norm(' '.join(words[:2])) in [norm(x) for x in L['ai_fatigue']] else 6
            why.append('AI-fatigue: ' + ','.join(ai))
        for key, pts in (('stake', 3), ('tension', 3), ('command', 2), ('you', 2), ('groups', 3)):   # groups: job/life-group call-out (angle G)
            hit = has(text, L[key])
            if hit: s += pts; why.append(f'{key}: ' + ','.join(hit[:3]))
        if not has(text, L['you']) and re.search(r'(^|\s)(ن?می[\u200c ]?\S+ی|\S+ت)(؟|\s|$)', text):   # 2nd-person verb or "your …" suffix
            s += 2; why.append('you: 2nd person')
        if '؟' in text or '?' in text: s += 1.5; why.append('question')
        nums = re.findall(r'\d+(?:[.,/]\d+)?', text.translate(FA))
        if nums:
            s += 1; why.append('number')
            for x in nums:
                if x not in facts: fail.append(f'number {x} not in facts')
        latin = re.findall(r'[A-Za-z][A-Za-z0-9\-\.]+', text)
        for w in latin:
            if norm(w) in facts: s += 3; why.append('name: ' + w)
            elif norm(w) not in [norm(x) for x in L['ai_fatigue']]: fail.append(f'{w} not in facts')
        for item in L.get('learned', []):
            if norm(item['word']) in norm(text): s += item.get('bonus', 1); why.append('learned: ' + item['word'])
        if recent:
            ws = set(norm(text).split()); sim = max((len(ws & r) / max(1, len(ws | r)) for r in recent), default=0)
            if sim > .5: s -= 3; why.append(f'similar to a recent cover ({sim:.2f})')
        out.append({'angle': angle, 'text': text, 'score': round(s, 1), 'why': why, 'truth_fail': fail})
    out.sort(key=lambda r: (bool(r['truth_fail']), -r['score']))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
