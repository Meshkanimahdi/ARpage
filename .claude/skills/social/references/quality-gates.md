# Quality gates

Three gates, cheapest first, each judged by an **independent critic** (a fresh subagent with no shared
context: you never grade your own work). Every gate writes a JSON result that the next step and the publish
run check. A rule that is only in prose gets skipped under deadline pressure; put it in a gate.

## 1. Concept gate (text only, before anything is generated)
**Lint (automatic):**
- 3+ headline candidates; chosen headline 4–7 words; no category-fatigue word; first spoken line contains it
- story fields present incl. `life` and `life_impact`; at most 2 non-life reels in a row
- hook plan (frame 0, motion, overlay ≤ 7 words); cover subject; 4 headline variants for the 8 candidates;
  no fatigue word, `from the view of…`-style label or emoji anywhere on the cover; series name is a story name
- motion prompt family not in the last 10 reels; category ≠ previous reel; ≥ 6 scenes, each ≥ 4 animated layers
- field differs from the last 4 reels; cast present (gender, age, role for each character)
- series part: name/part/of; two-option choice + AI pick unless last part; real vote and ≥ 7 days since the
  previous part for part > 1
- the history file is mandatory for reels (the repeat checks are useless without it)

**Critic** gets only the concept and the previous 3 covers' headlines; returns
`{"scores": {…}, "paraphrase": "<what a newcomer thinks the headline means>", "notes": {…}}`. Scores 1–10:
`headline_clarity` (≤ 4 if the paraphrase is wrong), `hook_plan`, `cover_plan`, `story_appeal`,
`share_value`, and `motion_plan` (reels) or `save_value` (posts). Fixes are text-only and free; max 3–4 rounds,
then change the angle or the story.

## 2. Preflight (stills, before the full render)
Render the cover and stills at t = 0, 0.5, 1, 1.9 s plus one still per scene; build one strip. Critic scores
`cover_stop_power`, `headline_clarity`, `hook` and `motion_richness`. Fixes in code, typography, headline and
crop only — never a new image call except one new cover background in total; max 3 rounds. A reel that cannot
pass preflight is stopped before the expensive render.

## 3. Final gate (after assembly, and again at publish time on the exact files)
**Hard checks (any failure = never publish):**
- attention QA passes (no empty-screen stretches, average shot ≤ ~4 s, no hold > 2.5 s, hook motion, length)
- the cover file is the rendered designed cover (md5 matches its render report), not a video frame; headline
  ≥ 120 px, ≤ 9 words; no kicker/sub repeated from the last 5 covers
- motion prompt, its family and its engine not in the last 10 reels; the engine starts with the prompt's own
  id and is not > 60 % the same code as a recent engine; category ≠ previous reel; field cooldown
- concept gate and preflight passed
- narrator not used in the last 12 reels; narrator gender ≠ previous reel; casting rules (voice script)
- SFX: ≤ 2 whooshes, no sound > 40 % of effects, effect set Jaccard < 0.75 vs each of the last 3 reels
- loudness and file format

**Critic scores** (on the cover, the 4:5 grid crop, a 1-fps contact sheet, the previous 3 reels' contact
sheets, the headline and a 2-line summary): `cover_stop_power`, `headline_clarity`, `hook`, `visual_match`,
`style_distinct`, `motion_richness`, and `casting` when a beat has a speaker.

**Result:** `gate.json = {pass, fails, hard_fails, score_fails, low_score_publish_allowed, info,
history_entry}`. Only `score_fails` may publish (with a `low_score` note) — and only when `hard_fails` is empty.
After a verified publish, append `history_entry` to the history file: reel, date, prompt, engine, category,
field, voice, voice gender, sfx set, series, series part, life flag, cover kicker/sub.

## 4. Bars and rounds
- Bars 6/10 while a page is young (an 8 bar stopped every reel; raise later deliberately, never mid-run).
- Max 3 fix rounds per stage; then take the best version.
- Never re-render a full video for a problem a cheaper gate should have caught; fix the gate instead.

## 5. Gate hygiene
- When the owner changes a rule, update the gate in the same change; remove old checks that now contradict it
  (a leftover "headline position must vary" check would have failed every reel after "always centre").
- Show the owner the gate result when they question a published item: which checks failed, and whether it went
  out on a score fail or slipped through a hole. Then close the hole.
