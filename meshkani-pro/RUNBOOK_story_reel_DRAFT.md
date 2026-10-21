# DRAFT — replaces RUNBOOK §4 after the user approves the story-reel test (not active yet)

## 4. REEL_PREPARE phase (main 21:45, retry 23:15 Tehran) — daily story reel

Goal: by the next morning, slot file `slot_<D+1>_0900.json` (`"kind": "reel"`) with status `READY`, a
QA-passed 60–70 s story reel MP4 + cover in Drive and a `Ready` row in the `Reels` tab.
Format (user decision 2026-10-21): **one idea per reel** in the style of the reference reel, the
on-screen text is the narration word by word — read `news-reel/STORY_SPEC.md` fully. (The two-news
reel in REEL_SPEC.md is retired.)

### 4.1 Preconditions
1. Setup (§0.1), control (§0.2). Slot: `python3 meshkani-pro/scripts/tehran.py reel prepare`; none →
   log, stop. Lock `<slot_file without .json>__reel_prepare` (retry: `__reel_prepare_retry`).
2. Reel slot file: same rules as §1.1 (missing → create `RESEARCHING`; finished → stop; stale >15 min
   → take over; fresh → stop).
3. `bash news-reel/setup.sh`.

### 4.2 Idea research
1. History: `Reels` tab (last 14 rows: topics, people, fields) and the last 7 days of posts.
2. Find 5–10 candidate ideas (WebSearch, primary sources through Drive when WebFetch is blocked, §1.3):
   statements, interviews, talks, books, reports or surveys about AI's concrete effect on everyday
   life, work, money, health, learning or society, by known people/institutions; prefer the last 14
   days. Drop rumours and anything you cannot attribute.
3. Pick the one with the strongest hook for a general Persian audience and a clear everyday metaphor.
   Not the same idea/person as the last 14 reels, not the same field as the previous reel.
4. Write `work/story/dossier.json`: idea, who/where/when, primary URL + confirming URLs, exact quote
   (only if confirmed) or paraphrase, allowed claims, field, selection reason.

### 4.3 Script, voice, elements
1. `work/story/story.json` per STORY_SPEC: `voice` (one narrator; alternate gender from the previous
   reel slot file `voices`; fits the topic), `end_text`, `music_prompt`, `credits`, 18–26 `beats`
   (id, bg, text, visual). Only allowed claims.
2. `work/story/elements.json`: every object the beats need, in **≤ 3 sheets of ≤ 9 items** (user rule —
   no per-element image calls). `python3 news-reel/sprite_sheet.py --dir work/story`; Read the sheet
   previews; regenerate a sheet at most twice. Real products: refs per §1.5.1. Real people: real photos
   (Wikimedia Commons first, `fetch_to_drive` + download), credited.
3. `node news-reel/story_voice.mjs --dir=work/story` (exit 3 → shorten). 60–70 s.

### 4.4 Render and QC
1. `node news-reel/reel_render.mjs --dir=work/story --page=story.html --mode=check`; Read every
   `out/sheet*.jpg`. Fix ISSUES (word mismatch), text overflow, wrong/ugly cut-outs, a visual that does
   not match its sentence, distorted people/products. Max 3 rounds.
2. `--mode=video` in the background (~15 min), then `python3 news-reel/reel_assemble.py --dir work/story`:
   `reel.json` must show 55–72 s, −15.5…−12 LUFS, true peak ≤ −1 dBFS; H.264 1080×1920 30 fps + AAC.
3. Extract frames at 1 s, the middle and the end card and Read them; Read `cover.jpg`.

### 4.5 Storage, caption, sheet
1. Content ID `REEL-NNN`. Drive: `YYYY-MM-DD_REEL-NNN` under `ریلز` (`google.reels_folder_id`) with
   `REEL-NNN.mp4`, `REEL-NNN-cover.jpg`; `story.json`, `elements.json`, `el/_sheet-*.jpg`,
   `timeline.json`, `dossier.json` to `_automation/packages/<D+1>_0900_REEL-NNN/`.
2. Caption like the reference: hook question line (+ one emoji at most); 2–4 short sentences that
   tell the idea with attribution; the closing question + «👇»; `منبع: <name>، <date>`; photo credit
   line if a real photo is used; 4–6 hashtags. No URLs.
3. `Reels` row (find-or-append, `USER_ENTERED`), A–T: Content ID · Reel Topic (`<field> | <idea>`) ·
   `Ready` · Production · Scheduled `<D+1> 09:00:00` · blank · Source URLs · News Text (the idea, 2–3
   sentences) · **Reel Script** (all beats' text, numbered) · **Motion Graphics Prompt** (per beat: bg +
   visual type + elements) · Duration · Video Drive URL · Final Caption · blank · Source Post IDs
   («—» unless based on a post) · Voices · **Music Prompt** · **Image Edit Prompts** (the element-sheet
   prompts `el/_sheet-*.txt`) · blank · Notes (credits). Read back.
4. Reel slot file → `READY` (`kind`, `content_id`, `idea`, `sources`, `voices`, `video`, `cover`,
   `caption`, `cost_usd` = sheets + any plates, `sheet.reel_row`, `reel` ids null). Log row (§3).

