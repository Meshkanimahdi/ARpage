# meshkani.pro cloud publisher — runbook

This file is the operating procedure for the scheduled cloud runs that research,
design, store and publish one Persian AI-news package per slot for the
Instagram account `meshkani.pro`. Each scheduled run starts a fresh Claude
session and is told which phase to run: **PREPARE** or **PUBLISH** (posts, §1–§2) or
**REEL_PREPARE** / **REEL_PUBLISH** (the daily reel, §4–§5).

Daily schedule (Tehran, user rule 2026-10-24):

| time | what is published | prepared at (main, retry) |
|---|---|---|
| **06:00** | ANALYTICS: the daily review that starts the day (§6) | — |
| **09:00** | reel + its story | 06:30, 07:30 (the same morning, after ANALYTICS; never the night before) |
| **12:00** | post + 3 stories, **every other day** (§1 cadence, 2026-10-27) | 10:30, 11:05 |
| **15:00** | reel + its story | 12:45, 13:45 |
| ~~18:00~~ | disabled 2026-10-27 (carousels every other day) | — |
| **21:00** | reel + its story | 18:45, 19:45 |

Publish runs start at :57 the hour before. Each reel (one trending AI story, news-reel/STORY_SPEC.md) is
also shared to the Story. The comment and DM responder runs separately (responder/).

Source of the rules: `TASK_SPEC.md` (standing task + cloud overrides) and «دستور کار انتقال انتشار محتوای meshkani.pro» (20 Oct 2026).
Where this file and that brief disagree, the brief's safety rules win: never
publish twice, never publish late, never publish unverified content.

---

## 0. Ground rules (both phases)

- **Motion graphics (user rule 2026-10-23):** every reel's motion style comes from the skill
  **motion-graphy-2026** (`.claude/skills/motion-graphy-2026/SKILL.md`, 85 distinct tested prompts). Read
  it by path at the start of every REEL_PREPARE (a session started before the skill existed does not
  load it by itself). Pick the prompt that fits the news. Never change a prompt's structure; change only
  timing, size/aspect ratio, duration and the topic slots (SKILL.md, "What you may change").
- **Learn from the audience (user rule 2026-10-23):** a daily ANALYTICS phase (§6) measures every
  post, story and reel and writes `_automation/insights.json`. Every PREPARE and REEL_PREPARE reads it
  and lets it steer topic, angle, hook, format and motion style, inside the fixed rules (sector rotation,
  facts, caps). The goal: more reach, watch time, saves, shares and follows, and the best social-media
  content team there is.
- **Model (user rule 2026-10-23): all content is produced with Claude Opus 5.5 (`claude-opus-5-5`).**
  This covers posts, carousel slides, stories and reels: research, writing, narration scripts, image
  prompts, motion design and QC. A publisher session or scheduled task must run on this model; Sonnet,
  Haiku or older models are not allowed for content. If a run finds it is not on Opus 5.5 (it
  knows its model from its own system prompt), it still runs the phase, so no slot is missed, and
  writes a `MODEL_MISMATCH` row (`model=<actual>`) in the Automation Log so the session gets moved.
- Time zone is `Asia/Tehran` everywhere. Get times only from
  `python3 meshkani-pro/scripts/tehran.py`.
- Slots: `12:00` (post, every other day; `18:00` disabled 2026-10-27), `09:00`, `15:00` and `21:00` (reels). Slot key format `YYYY-MM-DD|HH:MM`.
- Per slot at most 1 post + 3 stories; per Tehran day at most 1 post (every other day) + 3 post stories + 3 reels + 3 reel stories.
- Publish window: from the slot time until slot time + 30 minutes. After that the
  slot is `SKIPPED_LATE`. A missed slot is never caught up later.
- Never print, log or write to the sheet: API keys, Drive upload-session URLs,
  public download links. The sheet gets only normal Drive view links.
- If anything is uncertain (identity, source, text accuracy, publish outcome),
  stop that slot, record why, and do not guess.
- Instagram account must read back as username `meshkani.pro`, id
  `17841471767180096`. The Composio account id `instagram_beath-billow` (alias `meshkani.pro`; always pass one) alone is not
  proof of identity.
- Text and research are done by you (Claude) in the session. Images are made only
  with OpenRouter (`OPENROUTER_API_KEY`), model from `config.json`.

### 0.1 Session setup

1. Code: if `meshkani-pro/` is not in the working directory, attach and clone
   the repo: `add_repo` owner `Meshkanimahdi`, repo `ARpage` (read), clone it,
   then `git fetch origin claude/ecstatic-davinci-1lqsug && git checkout FETCH_HEAD`.
   Work from the repo root. Read `meshkani-pro/config.json`.
2. Load deferred tools with ToolSearch. The Composio server prefix differs per
   session (`mcp__Composio__*` or `mcp__<uuid>__*`), so search by keyword:
   `COMPOSIO_SEARCH_TOOLS COMPOSIO_MULTI_EXECUTE_TOOL COMPOSIO_REMOTE_WORKBENCH COMPOSIO_GET_TOOL_SCHEMAS`
   (max_results 8), plus `Google Drive read_file_content`, `WebSearch`, `WebFetch`.
3. Call `COMPOSIO_SEARCH_TOOLS` once with `session: {generate_id: true}` and use
   cases "read and update google sheets values", "upload file to google drive",
   "publish instagram carousel and story". Keep the returned session id for
   every later Composio call.
4. Run the whole of `meshkani-pro/workbench/drive_bridge.py` in one
   `COMPOSIO_REMOTE_WORKBENCH` call (it prints `drive_bridge ready`). Workbench
   state persists between calls, so later cells can call its helpers.
   **The workbench sandbox is shared with the responder session (2026-10-27: its `rows` overwrote ours and 6
   comment-log rows landed in Stories).** Never pass data between cells in a plain global (`rows`, `data`,
   `values`, `res`…): build the payload and send it in the same cell, or use names prefixed `pub_<RUN_ID-hex>_`.
   Read back every sheet write.
5. `RUN_ID` = `<phase>-<UTC yyyymmddHHMMSS>-<4 random hex>`.
6. Slot: `python3 meshkani-pro/scripts/tehran.py slot <phase>`. If it returns no
   slot, write one log row (§3) "no slot window open" and stop.

### 0.2 Control switch

Read the sheet tab `Automation Control` (range `A1:C10`) with
`GOOGLESHEETS_VALUES_GET`.

- `Kill Switch` = `ON` → log `SKIPPED_KILL_SWITCH` and stop. Check it again right
  before every Instagram publish call.
- `Mode` = `DRY_RUN` → do everything except the Instagram container/publish
  calls; store files in the test folder (`google.test_folder_id`) and do not
  write `Carousel Posts` / `Stories` rows. `LIVE` → normal.
- Any other value or an unreadable tab → treat as `ON`.

### 0.3 State on Drive

- Machine state lives in Drive folder `_automation` (ids in `config.json`):
  `slots/slot_YYYY-MM-DD_HHMM.json` (one file per slot) and `locks/`.
  `packages/<date>_<HHMM>_<CONTENT-ID>/` keeps the research dossier and raw model
  images.
- The sheet is the human view; the slot JSON is the source of truth for what was
  actually published.
- Read a state file: workbench `print(read_text(file_id))`. Write it: keep the
  JSON locally in `work/state.json`, then workbench
  `print(open_update(file_id))` (or `open_upload(name, slots_folder_id,
  "application/json")` for the first write) and
  `bash meshkani-pro/scripts/drive_put.sh work/state.json '<session url>'`.
- Write the state file after every status change and **immediately** after
  every Instagram call that returns an id. Faster for JSON state: workbench
  `write_text(file_id, json_text)` (in-place PATCH).

Slot statuses: `RESEARCHING → DESIGNING → QA → READY → PUBLISHING → PUBLISHED`,
plus `SKIPPED_LATE`, `SKIPPED_NO_NEWS`, `SKIPPED_KILL_SWITCH`, `FAILED`,
`NEEDS_RECONCILIATION`. Each story has its own status
(`PENDING / CONTAINER_CREATED / PUBLISHED / FAILED / UNKNOWN`).

Slot JSON shape (keep keys stable):

```json
{
  "slot_key": "2026-10-20|12:00", "status": "READY", "mode": "LIVE",
  "content_id": "POST-012", "sector": "food and agriculture", "topic_fa": "...",
  "runs": {"prepare": "RUN_ID", "publish": null},
  "times": {"prepare_started": "...", "ready_at": "...", "publish_started": null, "published_at": null},
  "source": {"name": "...", "url": "...", "published": "YYYY-MM-DD", "event_date": "YYYY-MM-DD",
             "confirming": ["url", "..."], "dedupe_key": "org|product-or-study|event"},
  "caption": "...",
  "slides": [{"n": 1, "title": "...", "body": "...", "prompt": "...", "model": "...", "cost_usd": 0.0,
              "drive_file_id": "...", "md5": "...", "view_url": "...", "qa": {"ocr": "pass", "visual": "pass"}}],
  "stories": [{"n": 1, "title": "...", "body": "...", "prompt": "...", "drive_file_id": "...", "md5": "...",
               "view_url": "...", "status": "PENDING", "container_id": null, "media_id": null,
               "permalink": null, "published_at": null, "expires_at": null}],
  "post": {"child_container_ids": [], "carousel_container_id": null, "publish_requested_at": null,
           "media_id": null, "permalink": null},
  "folders": {"package": "...", "slides": "...", "stories": "..."},
  "sheet": {"post_row": null, "story_rows": []},
  "cost_usd": 0.0, "errors": []
}
```

### 0.4 Locks

Before doing any work in a phase, claim the phase lock in the workbench:
`won, winner = acquire_lock("<slot_file without .json>__<phase>", RUN_ID, locks_folder_id)`.
If `won` is False another run owns this phase: stop without writing anything
except one log row `DUPLICATE_RUN_STOPPED`.

---

## 1. PREPARE phase (main 10:30 / 16:30, retry 11:05 / 17:05 Tehran)

**Post cadence (user rule 2026-10-27): one carousel every other day, at 12:00 only.** Mahdi: «فعلا تو برنامه پست
اسلایدی بشه روز در میون یه دونه». The 18:00 PREPARE/PUBLISH tasks are disabled. A day is a post day when the
number of days since 2026-10-27 (Tehran date) is even (2026-10-29, 10-31, 11-02, …); on any other day the 12:00
PREPARE, retry and PUBLISH write one log row "off day (carousel every other day)" and stop. The DAY_SUMMARY row
(§2.6) is written by the 21:00 REEL_PUBLISH instead.

**Carousel format (user rule 2026-10-27, overrides §1.3–§1.5 where they differ).** Mahdi approved all five
fixes from the carousel analysis (26 carousels: median reach 38, about 3 % of followers; 1 save and 4 shares in
total; reels median 1,429): «پیشنهادات همش خوب بود، همه رو اعمال».
1. **Saveable, not news.** A carousel is a utility the viewer keeps: "5 prompts for …", a checklist, before/after,
   "if you are a [job], these 4 tools …", "never tell ChatGPT these 5 things", a step-by-step how-to, a
   comparison table. A real, sourced fact or recent news item may anchor it (one slide, with source), but the
   carousel is the practical value. Breaking news goes to the reels.
2. **Topics from the reel winners' family:** jobs, money, everyday life, a named group of people («اگه آشپزی…»,
   «آرایشگرها…», HEADLINES.md angle G). No corporate/B2B deal news (banks, defence, pharma partnerships, utilities)
   unless it changes the viewer's own job or money.
3. **Slide roles:** slide 1 is a big hook cover in the reel-cover style (one plain line, ≥ 4–7 words, a real face,
   product or object, strong contrast; the headline system and clear-before-clever apply); slide 2 delivers a
   useful item at once (no context or date slide); slides 3–8 one item each, readable without the caption;
   the last slide asks for the save or the send: «ذخیره کن تا یادت نره» / «برای یه [شغل/دوست] بفرست». The
   caption's first line is the same hook, never a news-wire opening («X روز ۲۱ اکتبر اعلام کرد…»).
4. **Push it to followers right after posting:** story 1 is the carousel's slide 1 with «پست جدید رو ببین 👆
   ورق بزن» and the first useful item as a teaser; stories 2–3 tease two more items. (The Graph API cannot add
   poll or link stickers, so the teaser has to make people open the post.)
5. **Review after two weeks (2026-11-10):** the ANALYTICS phase compares carousels from 2026-10-29 on with the
   old median (38 reach). If they do not reach ≥ 150 reach and several saves each, recommend cutting carousels
   to one a week in `insights.json`.

Goal: by publish time, a slot JSON with status `READY`, six QA-passed JPEGs in
Drive and `Ready` rows in the sheet. Keep going only while
`tehran.py check-deadline <slot_key>` exits 0; if the window closes, set
`SKIPPED_LATE`, log, stop.

### 1.1 Preconditions
1. Setup (§0.1), control (§0.2), lock `__prepare` (§0.4).
2. Look for the slot file in `slots/`:
   - none → continue.
   - `READY`, `PUBLISHING`, `PUBLISHED`, `SKIPPED_*`, `NEEDS_RECONCILIATION` → stop (already handled).
   - `FAILED`, or `RESEARCHING / DESIGNING / QA` whose Drive `modifiedTime` is more
     than 15 minutes old (the earlier run died, e.g. a worker restart) → take it over
     if no Instagram id was ever recorded in it: reuse anything already finished in
     it (dossier, QA-passed images), record the takeover in `errors`, continue.
   - `RESEARCHING / DESIGNING / QA` modified in the last 15 minutes → another run is
     alive; stop.
   The scheduled PREPARE runs twice per slot (main run ~1.5 h before publishing,
   RETRY run ~55 min before). The RETRY run uses lock name `__prepare_retry` and
   does nothing when the main run is alive or already finished.
3. Create the slot file with status `RESEARCHING` and `runs.prepare = RUN_ID`.

### 1.2 History and diversity
1. Read `Carousel Posts!A1:S200` and `Stories!A1:Q300`. The 14 most recent posts
   (by Content ID / dates) are the duplicate-check set; note their topics, source
   URLs, sectors (prefix of Post Topic, otherwise infer) and image prompts.
2. List `slots/` files of the last 7 Tehran days and read their `sector`,
   `source.url`, `source.dedupe_key`.
3. Read the last 20 feed posts of the account (`INSTAGRAM_GET_IG_USER_MEDIA`,
   fields `id,caption,permalink,timestamp`) as a live check.
4. Sector rule (user rule, 2026-10-20 — stricter than the original brief):
   - Every post must come from a **different field than the previous post**; two
     posts in a row from the same field are **never** allowed, with no exception.
     Example: two consecutive posts about AI models/releases are forbidden.
   - Fields are the list in `config.json → sectors` (food, sports, film, music,
     health, travel, …). "AI models and tools" (new LLMs, chatbots, model
     releases) is itself one field; use it rarely — the page's focus is AI's
     concrete effect in everyday fields.
   - No field more than twice in the last 7 Tehran days; prefer the field used
     least recently. If no credible current story exists in a fresh field, look
     in other fresh fields; if still none, skip the slot (`SKIPPED_NO_NEWS`)
     rather than repeat the previous field.
   - Write the chosen field at the start of Post Topic and in the bundle state.
5. Also read `_automation/history/publish-state.json` and `stories-state.json`
   (ids in config: the completed original batch). The never-republish list from the legacy state file (POST-001…POST-010,
   POST-011, the standalone test story) and everything in the sheet is history.
6. **Audience insights:** read `_automation/insights.json` (§6), if present. Among the fields the
   rule above still allows, prefer those with the best `leaders.field` ranking. Apply the `hooks`,
   `caption` and `design` lessons to this bundle, and record which insight you used in the slot file
   (`insight_used`). The sector rule and fact rules always win over insights.

### 1.3 Research (live)
Use WebSearch/WebFetch, English first, local language if needed:

> با ساعت فعلی تهران و جست‌وجوی زنده، خبرهای معتبر **هفت روز اخیر** را دربارهٔ اثر واقعی
> هوش مصنوعی در چند صنعت پیدا کن. قبل از انتخاب، ۱۴ پست اخیر و سابقهٔ هفت روز گذشته را بررسی
> کن. برای هر نامزد، منبع اصلی، تاریخ انتشار، تاریخ رخداد، ادعای دقیق و محدودیت آن را
> استخراج کن. موضوع‌های تکراری و شایعات را حذف کن. حوزهٔ کمتر پوشش‌داده‌شده را در صورت وجود
> خبر هم‌سطح ترجیح بده. اگر خبر مناسب نیست، خروجی را «خبر مناسب پیدا نشد» قرار بده؛ خبر یا
> آمار نساز.

- **Search window: the last 7 days** (user rule 2026-10-24; it was 24–48 h); when no story fits the day's brief (field rotation, audience, group) inside 7 days, widen to **the last 30 days** (user rule 2026-10-26) and log `window=30d`. The event or announcement must
  be inside the last 7 Tehran days; prefer the freshest of two equal stories, and never repeat a story
  already covered (check 14 posts and 14 reels).
- Aim for 15–30 candidates across many fields from `config.json → sectors`
  (search each fresh field explicitly, e.g. "AI in football", "AI film
  production", "AI restaurant"). Do not pad the list.
- Open the **primary source** for every finalist with WebFetch. If the network
  blocks it (proxy 403 / DNS error), fetch it through Drive instead (workbench
  `fetch_to_drive(url, <package folder id>, "src-<n>.html")` → download → read the
  HTML). Only if that fails too, confirm the facts in at least 3 independent reputable
  outlets via WebSearch, attribute to them, and drop any figure they disagree on.
- Open the **primary source** for every finalist (paper, university, hospital,
  regulator, company newsroom/docs, official report). Use independent reputable
  outlets only to confirm and to judge importance.
- Record: publish/update date, actual event date, country, organisation, exact
  claim, limits, primary link. An old study re-reported today is not new — say
  when it first appeared or drop it.
- Medical news: label the evidence level (lab, animal, human trial, cleared tool,
  commercial product). Never present early results as proven. No treatment advice.
- Company claims are attributed to the company. Drop rumours, unclear sources,
  denied stories and conclusions beyond the evidence.
- "Trend" only from observable signals (several independent outlets, real
  significance). Never invent views, ranks or virality.
- Duplicate check: same event/product/study/organisation as anything in the
  history set (by URL, product or study name, organisation + event) → drop, even
  with a new headline.
- Image rights: note whether an official photo exists and whether its licence
  allows reuse. Being visible on a news site is not permission. Default to a
  labelled concept image.
- If nothing passes: status `SKIPPED_NO_NEWS`, log the reason, stop.

Write the dossier to `work/dossier.json` with: `title_fa, sector, summary_fa,
source{name,url,published,event_date}, confirming[], allowed_claims[],
limits[], why_it_matters_fa, image_rights, dedupe_key, selection_reason,
candidates_considered` (short list with drop reasons). Upload it to the package
folder (`ensure_folder` under `packages`).

### 1.3b Nine-slide carousels from one storyboard image (user rule 2026-10-25; from the 2026-10-26 prepares)
Mahdi: one storyboard image, cut into slides, gives better quality, lower cost and more information per post.
- **A post has 9 slides** (was 3) **+ 3 stories**. The rest of §1 still applies; where it says 3 slides or
  six images, read 9 slides + 3 stories.
- **Pictures:** the 9 slide pictures come from ONE image: `gen_image.py --kind postboard` (2560x3200, a 3x3
  grid of 4:5 panels, thin black gutters, one prompt listing the 9 panels in reading order, one world, light
  and palette, real-product `--ref` photos per §1.5.1). Cut it with
  `python3 news-reel/storyboard_cut.py board.png --out work/final/slides --names p1,…,p9 --cols 3 --rows 3 --size 1080x1350`.
  The 3 story pictures come from ONE image: `gen_image.py --kind storyboard3` (3456x2048, 3 panels of 9:16),
  cut with `--cols 3 --rows 1 --size 1080x1920`. Two image calls per post (≈ $0.20) instead of six.
- **No text in the generated pictures.** The board prompt asks for pictures only (no letters, numbers,
  logos or UI text). All Persian text is typeset in code with `news-reel/slide.html`:
  `work/final/slides/slides.json` → `node news-reel/slide_render.mjs --dir=work/final/slides` (and the same for
  stories with `"format": "story"` and `--prefix=story`). This gives exact spelling, so the OCR/fix loop of
  §1.7 is replaced by reading `slide_sheet.jpg` / `story_sheet.jpg`; exit 5 = text does not fit → shorten.
  Footers (`@meshkani.pro`, «n از ۹», «تصویر مفهومی» when `concept: true`) are part of the render, so
  `footer_overlay.mjs` is not used for these posts.
- **Slide plan (kinds: hook, point, stat, quote, cta):** 1 hook (headline system, ≥ 104 px, a clear different
  look per §1.5), 2 what happened, 3 who and the evidence, 4–7 the detail: one idea per slide (a number as a
  `stat`, a real quote as `quote`, a step, a comparison, the limit), 8 what it means for the audience's work or
  business, 9 `cta`: one question + «ذخیره کن / برای یه نفر بفرست». Each slide ≤ 45 words; vary `pos` and kind
  so swiping feels designed. Every number, name and quote from `allowed_claims`.
- **Board QA:** Read the board before cutting (the 9 panels must be distinct compositions of one story, the
  real product must match its refs), then Read `slide_sheet.jpg`. At most one board regeneration; a single weak
  panel is replaced by reusing/cropping another panel, not by a new call.
- **Music (§1.7b):** `slides_music.py --slides` with the 9 slides → nine 8 s clips on one 72 s track.
- **Storage and sheet:** `POST-NNN-slide-1.jpg … -9.jpg` (+ `.mp4`), stories as before. The sheet keeps its
  columns: `Slide 1 Text` = slide 1, `Slide 2 Text` = slides 2–8 numbered one per line, `Slide 3 Text` = slide 9;
  `Image 1 Prompt` = slide board prompt, `Image 2 Prompt` = story board prompt, `Image 3 Prompt` =
  `slides.json` layout summary; `Image 1/2/3 Drive URL` = slide 1, the post folder, slide 9.
- **Publish (§2.3):** one carousel with 9 children (video children with music, image children as fallback).

### 1.4 Content (Persian)
**Concept gate first (user rule 2026-10-28, blocking).** Before any image call, write `work/concept.json`
(story, 3 headlines + chosen, `format`, the slide list from hook to the save/send ask, cover subject) and run
`python3 news-reel/concept_gate.py --dir work --kind post lint`, the independent critic, then `… check`.
   The critic is a fresh subagent (Agent tool, no shared context) that gets only `concept.json` and the previous
   3 covers' headlines; it answers JSON `{"scores": {…}, "paraphrase": "<what a newcomer thinks the headline
   means, one sentence>", "notes": {…}}` → `critic_concept.json`. Scores 1–10: `headline_clarity` (≥ 7, user rule 2026-10-29; ≤ 4 when
   the paraphrase does not match who did what to whom), `story_appeal` (would a Persian scroller who is not into
   tech care? jobs, money, everyday life win), `hook_plan` (is frame 0 a real, bright, big subject with the
   headline on screen and moving?), `cover_plan` (real face/product, big plain headline, clear at thumbnail size),
   and `save_value` (would someone save or send it?). Bars: all 7 (clarity lowered from 8 to 7 by Mahdi on 2026-10-29: «حد نصاب وضوح رو ۷ کن»; 18 rounds on 2026-10-29 stuck at 7 while critics asked for wordings that do not fit 7 words). Fix and repeat (text
   only, it costs nothing), at most 4 rounds; still failing → choose another story or angle.

Content ID: the next `POST-NNN` after the highest id in the sheet **and** in any
slot file. Stories are `POST-NNN-STORY-1..3`.

| Part | Role |
|---|---|
| Slide 1 | Short, accurate hook: what happened and why it matters |
| Slide 2 | Who made/reported what, and the evidence |
| Slide 3 | Practical effect or limit + one related question to the audience |
| Story 1 | A different hook that pulls the viewer into the topic |
| Story 2 | Context or one clarifying point — not a copy of the slides |
| Story 3 | Use or limit + a natural invitation to see the new post |

- Each image: one title line + one short body line (≤ ~12 words each).
- Persian public text; company/product names and URLs may stay in Latin.
- Caption (user rule, 2026-10-20):
  1. Open with a clear, accurate summary of the news in 3–5 short Persian
     sentences: what happened, who did it, what is actually new, and the key
     limit or condition. A reader must understand the news from the caption alone.
  2. Then one line of practical meaning for the audience and one natural related
     question or invitation.
  3. Source line with name and date only: `منبع: <name>، <YYYY-MM-DD>`.
     **No URLs in the caption** (links are not clickable on Instagram); the URL
     stays in the sheet and the bundle JSON.
  4. **No note about whether images are real or conceptual** at the end of the
     caption (no «طراحی و تصاویر مفهومی با کمک هوش مصنوعی.» or similar). For a
     licensed real photo, a short credit line `عکس: <owner>، <licence>` is the
     only image-related text allowed.
  5. Finish with 3–6 hashtags related to the story and sector. Do not guess
     hashtag popularity.
- Forbidden in images and caption: treatment claims, medical advice, growth
  guarantees, virality promises, fake links, fake polls, anything that looks like
  a tappable button or sticker.
- Every number, name and claim must be in `allowed_claims`.

### 1.5 Design brief
**Grid variety (user rule 2026-10-23).** Reel covers and post slide 1 are what the profile grid shows,
so the page must never look uniform. Before designing a cover or slide 1:
1. Look at the grid. Take the last 9 grid items (`INSTAGRAM_GET_IG_USER_MEDIA` with fields
   `id,media_product_type,thumbnail_url,media_url,timestamp`; covers via `thumbnail_url`, carousels via
   their first child, or the Drive files named in the slot files). Download them to `work/grid/`, then
   Read them as one contact sheet.
2. Pick a clearly different look from the last 3 grid items, and different from all of the last 9 in its
   combination of palette and layout type. The look covers palette (dominant hues), light key
   (dark ↔ light), layout type (big photo with a bottom headline, split screen, centred object on flat
   colour, typographic poster, collage, close-up face…), headline position and type style. Alternate the
   light key so the grid has rhythm. Record the choice in the slot file as
   `design_fingerprint {palette[hex], key, layout, headline_pos}`.
3. Check it: `python3 meshkani-pro/scripts/grid_check.py --new <cover.jpg or slide1.jpg> --prev work/grid/*.jpg --crop45`.
   Exit 3 means it is too similar: change the palette, key or layout, then regenerate or re-render (at
   most twice). Read the `_vs_grid.jpg` sheet before READY.

**Slide-1 headline:** use the headline system in `meshkani-pro/HEADLINES.md` (12 candidates,
`headline_score.py`, no «هوش مصنوعی» (AI) as the hook, stakes or names or tension, truth gate). Record
`slides[0].headline {text, angle, score}`. The caption's first line uses the same angle.

Before any image, write `work/brief.json`: sector, mood/tone, palette (hex),
image type (licensed real photo vs labelled concept image), Persian type style
and weights, title/body hierarchy, where image vs text sits, a distinct
composition for each of the six images, how the source is shown, content risks,
and **why this differs from the last 3 packages** (compare their prompts from the
sheet). One coherent package, six different compositions; across news change the
palette, imagery, light, texture, spacing and typography. Seriousness matches the
news (no celebration look for serious topics).

Real photos only with checked licence and attribution, never manipulated in a
way that changes the news content. Generated images of real events, patients,
cars or products are labelled «تصویر مفهومی» and never presented as evidence.

#### 1.5.1 Real-product look — reference photos are mandatory (user rule, 2026-10-20, strengthened)
When the news is about a **physical thing that exists and has been photographed** — a car or vehicle,
robot, device, gadget, product, building, place, or a public person — the images must show it **as it
really looks**: the audience has seen the real photos (often viral ones) and those photos are the
strongest hook. The NVIDIA post (real CEO likeness) is the model; the Tesla Roadster post (invented
red car instead of the real white Roadster seen in the viral launch photos) is the mistake not to
repeat. Abstract topics (a study, a policy, a model release) skip this step.

1. **Find the real photos yourself (3–6).** The run container cannot reach most sites or image hosts,
   but Google Drive can fetch any public URL for you (workbench `fetch_to_drive`):
   - WebSearch for the launch/news photos (official newsroom or press kit first, then reputable
     outlets covering the event; queries like "<product> unveiling photos", "<product> press kit").
   - For each promising page: workbench `fetch_to_drive(page_url, <package folder id>, "page-<n>.html")`,
     then `GOOGLEDRIVE_DOWNLOAD_FILE` → `curl` the `s3url` to `work/ref/page-<n>.html` →
     `python3 meshkani-pro/scripts/page_images.py work/ref/page-<n>.html --base <page_url>` lists the
     page's photos (share image first, with alt text).
   - Copy the chosen photo URLs into Drive: `refs_to_drive([urls], <package folder id>, "ref-<slug>")`,
     download each (`GOOGLEDRIVE_DOWNLOAD_FILE` + `curl`) to `work/ref/`, and **Read every one**. Keep
     only photos of the real object (drop renders by fans, look-alikes, other models); note each
     photo's page URL in the brief. Prefer frames without big captions or tickers; if a TV-style
     lower third is on the photo it is still fine as a generation reference.
2. **Describe the real look** in `work/brief.json → visual_reference`: silhouette and proportions,
   colour and finish, lights, wheels, doors/wings, distinctive parts (e.g. thrusters, rear wing), the
   setting of the viral images (e.g. night launch with smoke and light beams), and what must **not**
   appear (colours or parts it does not have).
3. **Generate with the references, always.** Every prompt that shows the object includes that
   description, and every such call passes the 1–2 clearest reference photos:
   `gen_image.py ... --ref work/ref/<a>.jpg --ref work/ref/<b>.jpg`. Ask for a *new* composition in the
   page's design (no copy of the photo's framing or text, no watermark or other page's logo), but the
   object itself must match the photos. Prefer recreating the famous moment (e.g. the car hovering on
   thrusters at the night launch) when it is the news.
4. **QA side by side (blocking):** make a contact sheet of the reference photos next to each final
   image (ffmpeg `hstack`) and Read it. The object must be recognisably the same product — shape,
   colour, key parts. Not matching → regenerate within the fix budget; still wrong → `FAILED`, never
   publish a look-alike.
5. Record `visual_reference` (sources + Drive ids of the refs) in the slot JSON and the image prompts in
   the sheet; mention the references in the Image Prompt cells («با تصاویر مرجع رسمی ...»).
6. Using a real photo **as-is** in the design still needs a licence that allows it and a credit line;
   as a generation reference it is fine.

### 1.6 Prompts and generation
Prompt engineering (user rule 2026-10-23). Every object and scene in an image is realistic, stylish and
professional, never flat clipart or simple icons. Each visual bracket below is written with the
checklist in STORY_SPEC §8.2 (subject, camera, lens and f-stop, angle, key + fill + rim light, 2–4
materials, background, composition, colour mood, exclusions), in concrete words, not adjectives.

Mother prompt (fill every bracket from the dossier and brief; record each final
prompt in the slot JSON and the sheet):

> یک تصویر نهایی حرفه‌ای برای صفحهٔ خبری فارسی meshkani.pro طراحی کن. این تصویر شمارهٔ
> `[n]` از `[پست سه‌اسلایدی / سه استوری]` دربارهٔ `[موضوع و حوزه]` است. حقیقت تأییدشده:
> `[خلاصهٔ تأییدشده]`. هدف این تصویر: `[قلاب / توضیح / اثر یا دعوت]`.
>
> جهت هنری این خبر: `[پالت]`، `[عکس واقعی مجاز یا تصویر مفهومی با برچسب]`، `[حس و ترکیب‌بندی
> همین تصویر]`، `[نوع فونت و سلسله‌مراتب]`. این جهت هنری باید با بریف همین خبر هماهنگ باشد و از
> طراحی خبرهای اخیر فاصله داشته باشد.
>
> متن دقیق فارسی زیر را با حروف درست، اتصال صحیح و خوانایی بالا در طراحی ادغام کن:
> «`[تیتر دقیق]`» و «`[متن کوتاه دقیق]`». هیچ امضا، آدرس صفحه، شماره یا برچسبی در تصویر ننویس.
> تیتر، تصویر و متن بخشی از یک صفحه‌آرایی واحد و متناسب با موضوع باشند. متن دیگری نساز.
> اعداد، نام محصول و ادعا را تغییر نده. ترکیب‌بندی این تصویر با دو تصویر دیگر متفاوت باشد.
>
> `[پست: نسبت ۴:۵؛ تصویر تا لبه‌ها پر باشد؛ تیتر و متن فقط در ستون وسط (حدود ۱۲٪ تا ۸۸٪ عرض) و دست‌کم ۱۰٪ از بالا؛ ۱۸٪ پایین تصویر کاملاً بدون متن بماند (فقط ادامهٔ تصویر).]`
> `[استوری: نسبت ۹:۱۶؛ تصویر تا لبه‌ها پر باشد؛ هیچ متنی در ۱۳٪ بالا نباشد؛ تیتر و متن در ستون وسط (۱۲٪ تا ۸۸٪ عرض) و بالاتر از ۷۷٪ ارتفاع تمام شوند؛ ۲۳٪ پایین تصویر کاملاً بدون متن بماند. هیچ آدرس صفحه، شماره یا برچسبی ننویس.]`
> از شبیه‌سازی دکمه یا استیکر تعاملی، نشان دادن صحنهٔ تولیدی به‌عنوان عکس واقعی و عناصر
> نامربوط به خبر خودداری کن.

Story layout rule (user, 2026-10-20): stories carry **no** sequence number and
**no** «تصویر مفهومی» label; the only footer is `@meshkani.pro`, small, exactly
centred, the lowest element of the image, sitting just above the 280 px bottom
safe line. QA checks this.

**Footers are always added in code, never by the image model** (user rule 2026-10-21 — the model
ignores coordinates for small footer text; POST-015 cost $2.20 / 42 images and POST-016 doubled its
stories because of this). After `finalize.py`, run `bash news-reel/setup.sh` once, then:
- posts: `node meshkani-pro/scripts/footer_overlay.mjs work/final/POST-NNN-slide-n.jpg work/final/POST-NNN-slide-n.jpg <n> pill '#<ink-hex>'`
  → `@meshkani.pro`, `n از ۳` and `تصویر مفهومی` (concept images) inside the 8% margins;
- stories: `node meshkani-pro/scripts/footer_overlay.mjs work/final/POST-NNN-STORY-k.jpg work/final/POST-NNN-STORY-k.jpg story <light|dark|pill> '#<ink-hex>'`
  → only `@meshkani.pro`, centred, bottom edge 12 px above the 280 px safe line (pick `light` text on
  dark images, `dark`/`pill` on light ones).
Then QA (§1.7). The image itself stays full-bleed.

**Image budget per bundle (user rule 2026-10-21):** exactly **one generation per image** (no
variants, no "generate two and pick"). Target ≤ **$0.45** per bundle (6 images + at most 3 fixes);
hard cap **$0.80** — when the next call would pass it, stop: status `FAILED`, log why, nothing is
published. Track `cost_usd` per image and the running total in the slot JSON.

Generate (the six can run in parallel as background jobs):

```
python3 meshkani-pro/scripts/gen_image.py --kind post  --prompt-file work/p/slide1.txt --out work/raw/slide1.png
...
python3 meshkani-pro/scripts/gen_image.py --kind story --prompt-file work/p/story1.txt --out work/raw/story1.png
```

Then finalize each:
`python3 meshkani-pro/scripts/finalize.py --kind post work/raw/slide1.png work/final/POST-NNN-slide-1.jpg`
(`--kind story` → `POST-NNN-STORY-k.jpg`). Add each `cost_usd` to the slot
JSON.

### 1.7 Quality control (all six, before READY)
1. Visual review: open every final JPEG with Read (stories: also the
   `.safezone.jpg`). Check: exact Persian text, correct letters and joining,
   RTL order, spacing, contrast, nothing cropped, text really inside the design
   (not an empty background), no extra/invented text, nothing important outside
   the story safe zone (230 px top / 280 px bottom), on posts no text (including small
   labels and the @meshkani.pro line) closer than 8% to any edge, fits the news and brief, not
   a near-copy of recent packages, no misleading fake elements, concept label
   present when needed (posts only; stories must have no number and no label, only the
   centred @meshkani.pro as the lowest element). For a physical product: the side-by-side
   reference check of §1.5.1 step 4 passes. The image fills the whole frame edge to edge: no
   blurred, mirrored or plain border around a smaller copy of the design (reject if present).
2. Upload the finals to Drive (§1.8 folders) so Drive can OCR them; read each back
   with `mcp__Google_Drive__read_file_content` and compare (Drive often does not
   OCR new files for minutes; if no text comes back after ~2 tries, record
   `ocr: not indexed` and rely on the visual review — never block on OCR):
   write the approved text (title + body) and the OCR text to files and run
   `python3 meshkani-pro/scripts/text_compare.py approved.txt ocr.txt`. OCR is a
   signal; the visual review decides.
3. Fix loop — cheapest fix first:
   - Footer, handle, number or label problems are never a reason to regenerate: re-run
     `footer_overlay.mjs` on the finalized image.
   - Only wrong/misspelled Persian text, broken joining, a wrong product look (§1.5.1) or text inside
     the unsafe zone justifies a new image: one `--ref` edit of the failing raw image with a precise
     correction prompt ("keep everything, only fix the word X to Y" / "keep the design and the
     full-bleed image, move the text block up so the bottom 18% has no text"). Max **1 fix per image**,
     a second only for a Persian-text error. Respect the bundle budget above.
   - Replace the Drive file content with `open_update(file_id, "image/jpeg")` so ids stay stable.
     Still failing → status `FAILED`, log which image and why, stop (do not publish a partial set).
   - A RETRY run that takes over a slot reuses every image that already passed QA (package folder /
     slot JSON) and regenerates only the failing ones — never a whole new set.
   **Never shrink the design into a frame, never add blurred/mirrored borders, never pad**
   (user rule, 2026-10-20 — the old `--inset 0.88` fallback made POST-012 and POST-013 slides and
   stories look unfitted with blurred edges; `finalize.py` now refuses `--inset`). Every final image
   is the model image itself, center-cropped and resized to the exact size, filling the frame
   edge to edge.
4. Re-check every claim against the primary source once more (look for
   corrections or denials since research).
5. File checks from the finalize reports: 3 × 1080×1350 JPEG, 3 × 1080×1920
   JPEG, each < 8 MB, Drive `md5Checksum` == local md5, correct order and names.
6. Write `qa` results into the slot JSON. Never pass QA just because files exist.

### 1.7b Music under the carousel (user rule 2026-10-23)
Every carousel post carries music. The Instagram API cannot attach library music to a carousel, so after
QA each approved slide becomes a short video item, and one continuous track plays across them: slide k
plays the track from k × 8 s. The image stays exactly the approved slide, with only a slow 3% push.
1. Write `music_prompt` for this post: instrumental, matched to the news mood and sector, different from
   the last 3 posts (tempo, instruments, energy). Examples: "calm hopeful felt piano and warm pads,
   92 bpm"; "confident modern electronic pulse, light percussion, 110 bpm". No vocals and no famous
   melodies. Record it in the slot file as `music {prompt, cost}`.
2. `python3 meshkani-pro/scripts/slides_music.py --slides work/final/slide1.jpg work/final/slide2.jpg work/final/slide3.jpg --out work/final/music --prompt "<music_prompt>"`
   This uses ElevenLabs `/v1/music`, audio only, with the key from env. It writes `slide1.mp4 … slide3.mp4`
   (1080x1350, 8 s each, −16 LUFS) and `music.mp3`.
3. Check one clip: extract its first and last frame and Read them; they match the approved slide. Listen
   through the numbers in `slides_music.json`.
4. Store `POST-NNN-slide-1.mp4 … -3.mp4` next to the JPEGs (§1.8). Record the Drive ids and md5 in the
   slot file under `slides[].video`. The JPEGs stay the source of truth for QA and the sheet.

### 1.8 Storage (Drive + sheet)
- Folder names: `YYYY-MM-DD_POST-NNN_<short-english-slug>` under
  `Images` (`post_images_folder_id`) for slides and under `استوری`
  (`story_images_folder_id`) for stories (`ensure_folder`). Raw model images and
  the dossier go to `_automation/packages/...`.
- Files: `POST-NNN-slide-1.jpg … -3.jpg`, `POST-NNN-slide-1.mp4 … -3.mp4` (music versions, §1.7b),
  `POST-NNN-STORY-1.jpg … -3.jpg`.
- Sheet (`LIVE` only), value input `USER_ENTERED`, times `YYYY-MM-DD HH:MM:SS`:
  - `Carousel Posts`: find the row whose column A equals the Content ID, else
    the first row after the last non-empty column A. Write A–S (Content ID,
    Post Topic, Status=`Ready`, Production time, Scheduled publish time, blank,
    Source URL, News Text, Slide 1–3 Text as `title\nbody`, Image 1–3 Prompt,
    Image 1–3 Drive view URL, Final Caption, blank). Post Topic starts with the
    sector: `<sector> | <topic in Persian>`. Do not add columns.
  - `Stories`: three rows, same find-or-append rule on column A (Story ID): Story
    ID, Parent Content ID, Story Topic, Sequence, Status=`Ready`, Production,
    Scheduled, blank, Source URL, Story Text, Image Prompt, Image Drive URL,
    blank, blank, blank, blank, Notes (diversity exceptions go here).
  - Read the rows back and confirm. Never touch other tabs (the reel phases own `Reels`), formulas,
    formatting or validation; never insert duplicate rows for the same id.
- Slot JSON → `READY` with every id, md5 and URL. Log row (§3).

---

## 2. PUBLISH phase (starts 12:00 Tehran, post days only)

### 2.1 Preconditions
1. Setup (§0.1), control (§0.2), lock `__publish` (§0.4).
2. Read the slot file. Behaviour by status:
   - `READY` → continue.
   - `RESEARCHING / DESIGNING / QA` → re-check every ~2 minutes (use
     `tehran.py wait-until` in ≤ 9-minute steps) until `READY` or until 3
     minutes before the deadline; then mark `SKIPPED_LATE`, log, stop.
   - `PUBLISHING / NEEDS_RECONCILIATION` → do §2.5 reconciliation only.
   - `PUBLISHED` → if any story is not `PUBLISHED`, go to §2.4 for those only;
     otherwise stop.
   - missing file, `FAILED`, `SKIPPED_*` → log and stop.
3. Daily caps: count `PUBLISHED` posts/stories in today's slot files (+ live
   media of today). Over the cap → stop.
4. Identity: `INSTAGRAM_GET_USER_INFO` (`account: instagram_beath-billow`, pass
   `fields: "id,user_id,username,account_type"` — without `fields` the
   `user_id` is missing) must return username `meshkani.pro`, user_id
   `17841471767180096`, type `MEDIA_CREATOR`; `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT` must leave at
   least 4 publishes. Otherwise `FAILED`, log, stop.
5. Duplicate guard: list the last 10 feed posts; if one has this slot's caption
   (or was published since `times.ready_at` with the same source URL in the
   caption), record it as the post, set `PUBLISHED`, and skip to stories.
6. `tehran.py wait-until <slot>` so nothing is published before the slot time.
   Then `tehran.py check-deadline` must exit 0.
7. `Mode` = `DRY_RUN` → stop here; log "dry run: all publish preconditions passed".

### 2.2 Make the six files fetchable
Workbench: `share_public(file_id)` for each file. Instagram fetches
`public_image_url(file_id)` (`drive.usercontent.google.com/download?...`). These
links are never written to the sheet or logs. Remove sharing in §2.6.

### 2.3 Carousel
Re-check Kill Switch first. Then, using `account: instagram_beath-billow`,
`ig_user_id: 17841471767180096`:
1. For slides 1→3 in order: `INSTAGRAM_POST_IG_USER_MEDIA` with `video_url: public_image_url(<slide-k.mp4>)`
   and `is_carousel_item: true` (the music versions, §1.7b; `share_public` them in §2.2). Save each id to
   `post.child_container_ids` immediately (write the state file). Poll `INSTAGRAM_GET_POST_STATUS` for each
   child until `FINISHED` (about 20 s apart, at most about 6 min in total, inside the window) before step 2.
   If a child ends in `ERROR`, recreate that one child once. If it fails again, fall back to the image
   children (`image_url` of the JPEGs) for the whole carousel, publish without music, and log
   `music_fallback`. A post is never skipped because of music.
2. `INSTAGRAM_POST_IG_USER_MEDIA` with `media_type: CAROUSEL`, `children` = the
   three ids in order, `caption` = the exact caption (raw `#`, not `%23`). Save
   `post.carousel_container_id`, set status `PUBLISHING`, set
   `post.publish_requested_at`, write the state file.
3. `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` with `creation_id` = carousel container
   id (`max_wait_seconds` 60). Do not use `INSTAGRAM_CREATE_CAROUSEL_CONTAINER`.
4. On success: save `post.media_id` immediately. On an error or unclear response:
   go to §2.5 — never call publish again before reconciliation says it is safe.
5. Verify with `INSTAGRAM_GET_IG_MEDIA` (fields
   `id,caption,permalink,timestamp,username,media_type,children{media_url,media_type}`):
   username, `CAROUSEL_ALBUM`, caption equals the approved caption, three children
   in order (`VIDEO` children when the music versions were used). Save permalink and `published_at`; status `PUBLISHED`.
6. Update the `Carousel Posts` row: Status `Published`, Actual Publish time,
   Published Post URL. Read back to confirm. If the sheet
   write fails, keep the state file as truth and retry only the sheet write.

### 2.4 Stories (right after the post, in order 1→3)
For each story not yet `PUBLISHED`:
1. Re-check Kill Switch and `check-deadline`. Window closed → mark remaining
   stories `FAILED` (reason: late), log, go to §2.6.
2. If it has a `container_id` but no `media_id`, reconcile it first (§2.5).
3. `INSTAGRAM_POST_IG_USER_MEDIA` with `image_url`, `media_type: STORIES` → save
   `container_id` (status `CONTAINER_CREATED`, write state).
4. `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` → save `media_id`.
5. Verify with `INSTAGRAM_GET_IG_MEDIA` (`id,permalink,timestamp,media_product_type,username`):
   `STORY`, right username; and/or `INSTAGRAM_GET_IG_USER_STORIES` (ig_user_id
   `17841471767180096`). Save permalink, `published_at`, `expires_at` (+24 h),
   status `PUBLISHED`, write state.
6. Update the story row: Status `Published`, Actual time, Published Story URL,
   Instagram Media ID, Parent Post URL, Expires At, Notes.
A failed story never causes the post to be published again.

### 2.5 Reconciliation (ambiguous outcomes)
Before any retry of a publish call:
- `INSTAGRAM_GET_POST_STATUS` on the container id (`PUBLISHED` / `FINISHED` /
  `ERROR` / `EXPIRED`), and list the latest feed posts (and the media id if one
  was returned).
- If the media is live: record it and continue as success.
- If the container is `FINISHED` and nothing new is live after a second check
  1 minute later: one retry of `..._MEDIA_PUBLISH` on the **same** container is
  allowed, still inside the window.
- Otherwise (unclear, `ERROR`, window closing): status `NEEDS_RECONCILIATION`,
  log exactly what is known, stop. Never create a new carousel for the same slot
  after a publish request was sent.

### 2.6 Finish
- `unshare_public` on all six files.
- Slot JSON final status; log row (§3) with links to the post and stories.
- The `DAY_SUMMARY` log row (the day's post and reel links, story statuses, total image cost) is written by
  the 21:00 REEL_PUBLISH (moved 2026-10-27).

---

## 4. REEL_PREPARE phase — daily story reels (09:00: main 06:30, retry 07:30 · 15:00: main 12:45, retry 13:45 · 21:00: main 18:45, retry 19:45; all the same day)

> **Outdated wording in scheduled prompts:** if the PHASE message still says "from
> today's two published news (12:00 then 21:00)", "a different narrator per news" or "only the posts'
> own images", that text is from the retired two-news format and cannot be edited from outside this
> session. The user decided on 2026-10-21 that this section and STORY_SPEC.md win: one trending AI
> story, one narrator chosen per story, elements from ≤ 3 generated sheets, Story cut included.

Goal: before the reel's time, slot file `slot_<date>_<HHMM>.json` (`"kind": "reel"`; `tehran.py reel prepare` gives it) with status `READY`, a
QA-passed 40–55 s story reel MP4 + cover in Drive and a `Ready` row in the `Reels` tab.
Format (user decision 2026-10-21): **one trending AI story per reel**, told as a story with strong
hooks for watch time; the on-screen text is the narration word by word; angle, story shape, look,
voice and rhythm change every day — read `news-reel/STORY_SPEC.md` fully before starting. (The
two-news reel in REEL_SPEC.md is retired.)

### 4.0 Reel visual rules (user rule 2026-10-24, after REEL-007; these override any older rule below)
Mahdi on REEL-007: «سبک بد، قلاب افتضاح، صدا با تصاویر همخوانی نداره، همش صفحه خالیه و راوی حرف می‌زنه، بدون هیچ
جذابیتی در تصویر» ("bad style, terrible hook, the audio doesn't match the pictures, the screen is always empty while the
narrator talks, nothing attractive in the picture").
1. **Shot list with the script.** Write narration and pictures together in `story.json`: every sentence
   (beat) has its own `shot` saying exactly what the viewer sees while that sentence is spoken. The picture
   shows the real thing being said: the person, product, place, logo, or the event itself. Never a pun on a
   Persian word (REEL-007 showed a gold wedding ring for «حلقه» meaning "loop"), never a decorative object.
2. **A designed, filled frame, always — not always a full-screen photo** (user rule 2026-10-24, second
   review). Never an empty or beige canvas with small cut-outs while the narrator talks; the main subject is
   at least 40% of the frame width. The look follows the chosen motion prompt: full-bleed photos, kinetic
   typography, real UI, framed photos on a designed ground, split screens, editorial layouts, 3D. Do not make
   every reel a full-screen photo slideshow. Nothing is cut by the frame edge unless it is a full-bleed
   background, and no text is truncated.
2b. **Professional motion graphics, never a photo slideshow (user rule 2026-10-27, blocking).** Mahdi, watching
   REEL-014 being built: «داره خیلی مسخره اینکارو میکنه، فقط بازی با تصویر و اسلاید کردنشون داره میشه مثل ریلز
   جزیره، من میخوام یه موشن گرافی حرفه ای داشته باشیم با کلی المان و عدد و رقم و نمودار و درخشش و… گفتم نمونه
   والمارت بهترین بوده». The Walmart reel (089) is the **quality bar**, not a template to copy. Every scene is a built
   motion-graphics composition, drawn in code, with at least 4 animated layers from this list:
   - numbers that count up (money, %, users, dates) and stat cards;
   - charts that draw on (bar, line, area, donut, progress ring) with axis labels and a highlighted point;
   - real UI rebuilt as vectors (cards, chat bubbles, dashboards, app screens) with a cursor or taps;
   - light and depth: glow, light sweeps over glass cards, soft shadows, parallax layers, a camera move in
     depth;
   - real logos on chips, icons, kinetic type, arrows, connectors and highlights;
   - particles or shapes only where the chosen prompt allows them.
   Photos are one layer inside a designed frame (a card, a mask, a device), never a whole scene that just pans,
   zooms or slides; at most 2 such photo-led shots per reel. A reel built from generated plates with Ken Burns
   moves (REEL-007R/«جزیره» look) is a failure. The critic scores this as `motion_richness` (≥ 7 on the scene stills
   in preflight and in the final gate).
3. **Rhythm and sync.** (User rule 2026-10-27, after REEL-014 failed visual_match on late numbers:) every number, name or
   result appears on screen within 0.3 s of the word that says it (time it from the voice word timings, never by scene
   order), and no frame between shots is empty or near-empty. A new shot or a clear camera change every 1.5–3 s; no still picture longer than 1.5 s,
   except a final CTA of at most 2 s. Cut on action. Length 40–55 s (the 60–92 s ranges below are replaced).
4. **Hook in 2 seconds.** (User rule 2026-10-26, after REEL-013 failed the critic's hook score twice:) from frame 0 a huge,
   readable Persian hook line (≥ 120 px, ≤ 2 short lines, never clipped, inside the safe area) over a bright, large
   subject (≥ 60 % of the frame); never a tight dark crop, small buttons or tiny card words as the opening.
   The first frame is the strongest picture of the reel, already moving, and the first
   spoken line is the cover headline's angle (HEADLINES.md), never a slow lead-in like «یه آزمایش واقعی از…»
   ("a real experiment from…").
5. **Motion prompt fit and variety.** One-diagram/zoom-map prompts (for example pm/168, 194) are only for list
   or how-to topics, never for a news story. **Every reel uses a different motion prompt** (user rule
   2026-10-24): never one used in the last 10 reels (check `news-reel/pm/README.md` "used in" and the Reels
   sheet), and rotate the category (UI, kinetic type, editorial, 3D, story, explainer…) so consecutive reels
   look clearly different. Reusing a built engine is fine only after 10 other reels.
7. **Pre-production plan before building (user rule 2026-10-24).** Write `work/story/production_plan.md`
   before any image or render:
   - the chosen prompt and why it fits; the shot list with times;
   - for each shot, how it is made, cheapest first: code/typography/UI (free) → real photos and logos (free)
     → a frame of a storyboard sheet → a single generated image (only when a sheet cannot work);
   - the number of storyboard sheets, the image budget (target ≤ $0.25 per reel, never more than $0.50
     without a logged reason) and the main quality risks.
8. **Storyboard sheets, never one image per shot (user rule 2026-10-24).** When the prompt needs generated
   pictures, generate them as storyboard sheets: up to 12 vertical 9:16 panels in one wide image
   (`gen_image.py --kind board`, 3840x2160, 6 columns x 2 rows, thin black gutters, one prompt listing the
   panels in reading order, same world/light/character, `--ref` for a recurring character). Cut them with
   `python3 news-reel/storyboard_cut.py board.png --out work/story/raw --names s01,…,s12` (finds the gutters,
   upscales each panel to 1080x1920). Use each panel as a shot, and reuse a panel with a different camera
   move or crop where it fits. One sheet ≈ $0.11 for 12 shots instead of ≈ $0.60. Regenerate a whole sheet
   at most once; a single bad panel is replaced by reusing another panel, not by a new call. Read the sheet
   before cutting.
6. **Gate (blocking).** After `reel_assemble.py`, run `python3 news-reel/reel_qa.py work/story/reel.mp4`
   (add `--layout designed` for typography/UI/editorial looks on plain grounds: it relaxes only the flat-area
   limits; holds, rhythm, hook and length stay strict).
   Exit 3 is a FAIL: fix and re-render, never publish. Then Read `qa/contact.jpg` (1 frame per second) and
   check each second against the narration for cropped elements, cut-off text, and a picture that does not
   match its sentence. Record `qa.attention` (the qa.json numbers) in the slot file.
9. **Dynamic rotation list (user rule 2026-10-26).** Mahdi: «سبک والمارت نمیخوام باز بعدی ها دقیقا همون
   پرامپت رو کپی کنه… بهترینهاشن که پویا هستند رو انتخاب کن برای ریلز ها» ("I don't want the next reels to copy
   the Walmart prompt; pick the best dynamic ones"). Walmart (089) was only an example of good energy, not a
   template: never rebuild 089 or copy its glass look. The skill catalog was deduplicated on 2026-10-27 (Mahdi):
   230 entries were only 85 different prompts, and the 145 copies were removed (`references/duplicates.json`
   maps an old id to the kept one, e.g. 019 → 211, 105 → 001). The gate treats a removed id as its kept prompt
   (`news-reel/pm/families.json`), so a prompt used in the last 10 reels cannot come back under another name.
   Choose each reel's prompt from this list, in order, skipping one whose family or category is blocked,
   or whose look does not fit the story. Each one gets its own engine built from its own prompt text:
   | # | prompt | category | why it is dynamic / when to use it |
   |---|---|---|---|
   | 1 | `181-sahi-trading-terminal-reveal` | MUSIC/UI | data-rich: real-looking charts, windows, zooms across scales. Money, markets, company numbers |
   | 2 | `155-photo-print-app-launch-film` | UI | Apple-keynote continuous take: springs, bars drawing, black shape floods into the next scene |
   | 3 | `207-taxtello-bookkeeping-app-film` | UI | premium Apple-level product film with dashboards and numbers. Business/finance tools |
   | 4 | `112-lightspark-social-promo-video` | UI | punchy social promo of real capabilities with UI and stats |
   | 5 | `117-matra-caption-app-promo` | UI | white space, one idea per shot, the device as the hero; glass cards and glow |
   | 6 | `120-morphing-ui-states-loop` | UI | one shape morphing through UI states with a blur; feature lists |
   | 7 | `225-what-happens-in-one-second` | TOPIC | scale and big numbers, type and shapes morphing |
   | 8 | `095-gravitydex-anime-hype-edit` | UI/ANIME | fast cuts on the beat, impact frames, big type, real UI |
   | 9 | `219-uk-dubstep-track-with-ascii-visuals` | MUSIC | bold two-colour geometry and numbers hit on the beat |
   | 10 | `228-white-ball-ui-motion-loop` | TOPIC/UI | UI motion on a near-black dot grid: slider, notifications, typing |
   | 11 | `032-chaotic-claude-pov-video` | EDIT | 140 BPM chaotic POV with stacked captions; only for funny/viral stories, still with UI and numbers |
   | 12 | `089-frame-by-frame-launch-video` (Walmart) | UI | the quality bar; allowed again once 10 other reels have run, never copied into another prompt's engine |
   Story/character prompts (074, 191, 020, 079, 160, 086, 184, 211…) are used only when the story itself is a
   character story, and they must still meet rule 2b.
   Already used (blocked until 10 other reels): 089, 168, 211 (019), 001 (105), 149, 178, 074 (REEL-014).
   The 40–55 s, hook, storyboard and gate rules above stay; a 15–30 s prompt is stretched by
   giving each voiced beat its own section in that prompt's look, not by repeating sections.

### 4.1 Preconditions
1. Setup (§0.1), control (§0.2). Slot: `python3 meshkani-pro/scripts/tehran.py reel prepare`; none →
   log, stop. Lock `<slot_file without .json>__reel_prepare` (retry: `__reel_prepare_retry`).
2. Reel slot file: same rules as §1.1 (missing → create `RESEARCHING`; finished → stop; stale >15 min
   → take over; fresh → stop).
3. `bash news-reel/setup.sh`.

### 4.2 Story research (trending)
00. **Real famous faces and trending people (user rule 2026-10-31).** Mahdi: «یه پستی ما گذاشتیم از انویدیا که عکس خود
   صاحب انویدیا رو گذاشتیم، اون خیلی خوب بود… عکس آدمای واقعی باید بیاد… مثلاً ترامپ… ایلان ماسک… کاور خیلی مهمه یا
   قسمت اول ویدئو… مخصوصاً ترامپ که الان خودش واقعاً ترند دنیاست و ما هم باید روی این موج سواری بکنیم».
   - Prefer stories in which a famous, trending person acts or speaks (Trump, Elon Musk, Jensen Huang, Sam Altman,
     Mark Zuckerberg, Sundar Pichai…); when two stories are equal, the one with the more famous face wins. Search
     "Trump AI", "Musk AI" etc. in the 7-day window every day.
   - When the story has such a person, the **cover and frame 0 show their real photo**, face large (≥ 40 % of the
     frame), cut out or framed, bright, with the plain headline. Sources: Wikimedia Commons, official/government
     or company press photos (White House, company newsroom), credited in the caption («عکس: …»).
   - Never a generated or altered likeness, never a fake quote: the words on screen are what the person really
     said or did, from the source. A real statement may be paraphrased in Persian, not invented or sharpened.
0. **Viral radar first (user rule 2026-10-31).** Mahdi: «بریم تو پیجای هوش مصنوعی دیگه و نگاه کنیم ببینیم کدوم ریلز ها
   ریچ خوبی گرفته… مثل همون رو بسازیم». Once per day (the 09:00 REEL_PREPARE; the others reuse the file), read
   the last 7 days of reels from the Persian AI pages in `config.json → radar.pages` (start: mohamadesfehaniyan,
   radin_trade, mehdi.naddaf; add any page whose reel beats us) with `SCRAPECREATORS_LIST_INSTAGRAM_USER_REELS`
   (1 credit a page), plus one `SCRAPECREATORS_SEARCH_INSTAGRAM_REELS` for «هوش مصنوعی» this week. Rank by plays and
   by plays ÷ the page's usual plays (an outlier beats a big page's average). Write `_automation/radar.json`:
   top 10 with link, page, plays, likes, comments, the topic, the hook line, the format (talking head, motion,
   POV, list, debate) and the CTA trick (e.g. "comment «آموزش»"). At least one reel a day is **our own remake of a
   radar winner**: the same topic and angle, told with our headline system, our voice and our motion-graphics
   look, with newer or better facts, never their footage, audio or script text. Copy techniques freely (hook
   structure, keyword-comment CTA, debate question); credit the page in the caption when the idea is clearly
   theirs («ایده از @page»).
   **Never download and repost another page's reel** without written permission from its owner: it is their
   copyright, a report can remove it and strike the account, and Instagram's originality ranking gives reposts
   less reach in recommendations. With permission, post it as an Instagram Collab or with the owner credited and
   tagged, and log the permission in the Reels row.
00. Read `meshkani-pro/REQUESTS.md` first. A request for this slot overrides the rotation choices below
    (topic area, angle, look, shape) but none of the safety / fact / budget rules.
0. Three reels a day (09:00, 15:00, 21:00): each must differ from the day's earlier reels and the 21:00 reel from the next morning's; the 15:00 reel must differ from the same day's 09:00 reel (read its slot file
   `creative` + topic) in story, angle, shape, look preset and voice (prefer the other gender), and the
   09:00 reel from the previous day's 21:00 reel; the 21:00 reel differs from both of that day's earlier reels. Never the same story twice in a day.
   Shape 9 «Look-alikes, decoded» (STORY_SPEC §2, look `soft-ui`, user rule 2026-10-22): when 3–5
   similar AI products / models / agents are in the news (launches in the same week, a viral "which one"
   debate), make one of the week's reels in this format — about 1–2 a week, never two days running.
1. History: `Reels` tab (last 14 rows: topic, and angle/shape/preset/voice in Notes), the last 7 days
   of posts, and the previous reel's slot file `creative`.
2. Find 8–15 candidates trending in AI in the **last 7 days** (user rule 2026-10-24; widen to 30 days when nothing fits, 2026-10-26). **Topic cooldown (user rule 2026-10-26):** the field/topic family (robots, work automation, beauty, health, money…) must differ from the last 4 reels and from the last 2 days of posts; robots/automation two days running is a failure. Record `field` and `recent_fields` in story.json; reel_gate.py checks it (WebSearch across outlets, launches, viral
   demos, agent case studies, studies, statements; primary sources through Drive when WebFetch is
   blocked, §1.3). Drop rumours and anything you cannot attribute.
3. Read `_automation/insights.json` (§6). Score each candidate for hook strength, broad appeal for a
   Persian audience, a concrete everyday image, novelty vs. the last 14 reels, and fit with what the
   insights say this audience watches, saves and shares (`leaders.topic`, `leaders.angle`, `hooks`).
   Keep 1 reel in 4 as an exploration pick (an untried angle, topic type or motion category). Pick one. Then choose today's **angle** (STORY_SPEC §1, 17 angles — search at least 5 of them), **shape**
   (§2), **look preset** (§4), **voice** (§5) and **tempo** (§6) — each different from yesterday's.
3b. **Profession and life-group reels (user rule 2026-10-24).** At least 1 reel a day (and up to 2) is
   an AI story tied to a specific job or everyday group, framed as a call-out to that group: chefs and home
   cooks, hairdressers and beauticians, taxi and delivery drivers, teachers, students, doctors and nurses,
   shopkeepers, farmers, tailors, real-estate agents, parents, people trying to lose weight, gamers…
   Search for it explicitly: "AI cooking/recipe", "AI salon/hair", "AI weight loss", "AI taxi"… within
   the 7-day window. The cover and first line name the group with a provocative but true promise or
   warning: «اگه آشپزی، این به دردت می‌خوره», «آرایشگرها منتظر باشن», «اونایی که می‌خوان لاغر شن خوشحال
   باشن» (HEADLINES.md angle G). Rotate groups; never the same group twice in 7 days. Never insult or
   shame a group (weight, looks, class, ethnicity): speak to its goal or stake, not its body.
4. Write `work/story/dossier.json`: idea, who/where/when, primary URL + confirming URLs, exact quote
   (only if confirmed) or paraphrase, allowed claims, field, selection reason.

### 4.3 Script, voice, elements
-1. **Concept gate, before anything is produced (user rule 2026-10-28, blocking).** Mahdi: «یه کاری کن قبل از
   تولید همه چیز کنترل کیفیت بشه مخصوصا هوک کاور و تیترش». Before any image, voice, engine or render, write
   `work/story/concept.json` (format in `news-reel/concept_gate.py`): the story, 3 headlines and the chosen one,
   the first spoken line, the hook plan (frame 0, motion, on-screen line), the cover plan (real subject, position,
   kicker, sub, logo) and the motion plan (prompt + at least 6 scenes with ≥ 4 animated layers each). Run
   `python3 news-reel/concept_gate.py --dir work/story --kind reel --history motion_history.json lint` (exit 3 →
   fix: word count, AI words, cover position, prompt family, thin scenes, field cooldown), then the critic, then
   `concept_gate.py … check` (exit 0 = go). The production must then follow the approved concept; the preflight
   (§4.4 step 0) and the gate check the built version.
   The critic is a fresh subagent (Agent tool, no shared context) that gets only `concept.json` and the previous
   3 covers' headlines; it answers JSON `{"scores": {…}, "paraphrase": "<what a newcomer thinks the headline
   means, one sentence>", "notes": {…}}` → `critic_concept.json`. Scores 1–10: `headline_clarity` (≥ 7, user rule 2026-10-29; ≤ 4 when
   the paraphrase does not match who did what to whom), `story_appeal` (would a Persian scroller who is not into
   tech care? jobs, money, everyday life win), `hook_plan` (is frame 0 a real, bright, big subject with the
   headline on screen and moving?), `cover_plan` (real face/product, big plain headline, clear at thumbnail size),
   and for reels `motion_plan` (every scene ≥ 4 animated layers: numbers, charts, UI, glow; not photos sliding)
   or for posts `save_value` (would someone save or send it?). Bars: all 7 (clarity lowered from 8 to 7 by Mahdi on 2026-10-29: «حد نصاب وضوح رو ۷ کن»; 18 rounds on 2026-10-29 stuck at 7 while critics asked for wordings that do not fit 7 words). Fix and repeat (text
   only, it costs nothing), at most 4 rounds; still failing → choose another story or angle.
0. **Motion style first (mandatory).** Follow the workflow in `.claude/skills/motion-graphy-2026/SKILL.md`:
   - read `references/index.md` and shortlist 3 prompts for this story;
   - choose one, using the category table, `insights.json → leaders.motion_category` and the skill's
     rotation rules;
   - save the adapted prompt to `work/story/motion_prompt.md`, with only the allowed edits listed;
   - build it as `news-reel/pm/<id>.html`, or reuse the file if it exists (`news-reel/pm/README.md` lists
     the built prompts; prompt `089` is `news-reel/glass.html`).

   §4.0 applies: never a one-diagram/zoom-map prompt for a news story.
   **A new prompt gets its own engine built from that prompt's look** (user rule 2026-10-25): never copy
   another engine and rename it (REEL-010 used prompt 019 on a 92 % copy of the 211 engine and looked like the
   reels before it; the gate now rejects that). Full-bleed photo slideshows are at most 1 reel in 3.
   Write the script so it fits the prompt's structure: one narration beat per section or shot, with
   `beats[].shot` naming that section. A newly built engine file is committed and pushed to branch
   `claude/ecstatic-davinci-1lqsug`, with a line added to `news-reel/pm/README.md`, so the next reel can
   reuse it. If the push fails, log it. Fallback: if the built page still fails QC after 3 rounds and
   the deadline is close, use one of our own engines (STORY_SPEC §8.0) and log `motion_fallback`.
1. `work/story/story.json` per STORY_SPEC: `voice` + `voice_name` (fits the story; female for
   women-focused stories; not yesterday's), `theme` (preset + overrides), `tempo`, `stability`,
   `date`, `field`, `end_text`, `music_prompt`, `credits`, 18–34 `beats` (id, bg, text, visual).
   Hook in beat 1, open loop, re-hooks, payoff, closing question (STORY_SPEC §3). Every script carries
   English v4 audio tags where the tone turns, numbers/dates via `{shown|spoken}`; brand,
   startup, product and people names, and misread loanwords (`code`, `prompt`, `AI`), written in
   English in the spoken text (STORY_SPEC §5). Only allowed claims.
   Every element and scene image is realistic and premium, never a simple icon as the lead visual.
   Each prompt follows the 12-point prompt-engineering checklist in STORY_SPEC §8.2.
2. Line engine: real photos of people/products → `python3 news-reel/lineart.py` into `work/story/el/*.svg`;
   no image generation is needed. Realistic elements and real logos (user rule 2026-10-23,
   skill "Priority rule"):
   - **The real logo of the news subject is mandatory** (user rule 2026-10-23). A startup, company,
     product, app or lab in the news appears with its own official logo or app icon: on the cover, and
     wherever the story names it in the reel.
     - Sources, in this order: the official brand or press-kit page; the logo file (SVG/PNG) or
       `apple-touch-icon` on the company's own site; the company's official social avatar; Google's
       favicon service `https://www.google.com/s2/favicons?domain=<domain>&sz=256` (app icons only).
       Fetch them through Drive (`GOOGLEDRIVE_UPLOAD_FROM_URL`) when WebFetch is blocked. Wikimedia
       blocks the Drive fetcher.
     - Never generate, redraw, recolour, crop into or distort a logo, and never ask an image model to draw
       one. Place the real file as it is, on a clean white or brand-colour chip.
     - Save the source URL in `elements.json → logos[]` and in the slot file. If no official file can be
       found, use the company name in Latin type instead, never a fake mark.
   For story.html looks:
   `work/story/elements.json`: every object the beats need, in **≤ 3 sheets of ≤ 9 items** (user rule —
   no per-element image calls). `python3 news-reel/sprite_sheet.py --dir work/story`; Read the sheet
   previews; regenerate a sheet at most twice. Real products: refs per §1.5.1. Real people: real photos
   (Wikimedia Commons first, `fetch_to_drive` + download), credited.
3b. **Voices, music and sound effects from the library first (user rule 2026-10-31).** Mahdi: «ساوند افکت‌ها رو حتماً
   عوض کن، ما کلی ساوند افکت آماده هم داریم… نیازی نیست دائم تولید کنی یا از کردیت کم کنی… موزیک آماده هم زیاده… ما
   کلی صدای خوب داریم… بسیار هاسکی و از ته حلق، برای خبر عالی‌ان، صدای خانم‌های خیلی خوب. همه رو صداهای مشابه هم
   انتخاب نکن».
   - `news-reel/audio_library.json` lists what the ElevenLabs account already has: `voices` (from `GET /v1/voices`,
     with a one-line character note: deep husky male news voice, warm female, young energetic, …), `music`
     (ready tracks: news-reel/sfx music files, ElevenLabs history/library tracks, licensed Drive music) and `sfx`
     (news-reel/sfx/*.mp3 plus ready library effects). Build it once from the account (list, do not generate),
     commit it, and refresh it weekly.
   - **Voice:** pick by the story's mood from the library; never the voice of either of the last 2 reels (the gate
     checks `story.json → voice` against motion_history), and alternate male/female across the day. Deep, husky
     voices for serious news; bright female voices for everyday/beauty/lifestyle.
   - **Music and sound effects:** choose from the library; generate a new one only when nothing fits, at most one
     new file a day. Rotate music tracks: not the track of the last 3 reels.
3a. **English names (user rule 2026-10-29):** `node news-reel/pron_test.mjs --dir=work/story` (STORY_SPEC "English
   names must SOUND English"); commit `news-reel/pron_cache.json`; Read the scores, exit 4 → respell/rephrase.
3. `node news-reel/story_voice.mjs --dir=work/story --tempo=<tempo>` (eleven_v4; exit 3 → shorten,
   exit 4 → respell/rephrase the flagged beats). 40–55 s (§4.0).

### 4.4 Render and QC
0. **Pass the critic before rendering (user rule 2026-10-27, blocking).** Mahdi: «چرا هی میره تو گیت رد میشه…
   پرامپتش رو سفت و سفت‌تر کن که رد نشه، چون هر دفعه باید بره ری‌جنریت کنه و کلی هزینه داره». REEL-011 to 014
   failed the critic on cover, headline or hook only after a full render and new images. So the cover and the first
   2 s are built to this spec and judged on stills **before** the video render:
   - **Headline (cover and first spoken line, same words):** 4–7 plain Persian words with a verb; names the real
     subject (brand or person in Latin, or a plain noun); one number or stake when the facts have one; no metaphor,
     pun, nickname or riddle; a newcomer can repeat it in one sentence. Write 12 candidates (HEADLINES.md), then
     test the top 3 by asking yourself "what is this about?" and drop any that need the news to understand.
   - **Headline test first, text only (2026-10-28, after REEL-016 failed on clarity 6 with everything else
     7–8):** before any image, voice or engine work, give the independent critic only the top 3 headline
     candidates and a one-line story summary, and ask for `headline_clarity` (1–10) and the one-sentence
     paraphrase a newcomer would give. Keep only a headline scoring ≥ 7 whose paraphrase matches the story (who
     did what, to whom). None reaches 7 → rewrite and test again (it costs nothing), or pick another story.
     The voice's first line uses that exact headline.
   - **Cover:** a real photo of the main subject (a person's face, the product, or the place), big (≥ 50 % of the
     frame), bright, high contrast, warm or saturated colour; the headline at 120–150 px in the calm area; the real
     logo chip only for the main subject; no illustration, no UI screenshot as the whole cover, nothing dark or
     muddy.
   - **Hook (0–2 s):** frame 0 is a real photo or video of the same subject, full-bleed and bright, already moving
     (push-in, whip or slam); the headline line is on screen from frame 0, ≥ 120 px, inside the safe area and never
     clipped, for at least 1.5 s; one big number or result card may slam in by 1.2 s with ≥ 64 px text. Banned in
     0–2 s: an illustrated or drawn opening, a tight dark crop, small buttons or UI text, an empty or transition
     frame, a logo alone, a slow fade.
   - **Check on stills:** render `cover.jpg` (§4.4 step 3b) and
     `node news-reel/reel_render.mjs --dir=work/story --page=<engine> --mode=stills --t=0,0.5,1,1.9`, then
     `python3 news-reel/preflight.py --dir work/story sheet`. Give `preflight.jpg`, the headline and a 2-line
     summary to the independent critic (same rules as step 5, fresh subagent) and ask only for
     `cover_stop_power`, `headline_clarity`, `hook` and, on `out/sheet*.jpg` from `--mode=check` (stills of every
     scene), `motion_richness` (rule 2b) (1–10, one-line reasons) → `work/story/critic_preflight.json`.
     `python3 news-reel/preflight.py --dir work/story check`: every score must be **≥ 7** (the gate's bar; 8 was
     tried on 2026-10-27 and stopped every reel), else fix and repeat, at most 3 rounds.
   - **Cost rule:** fixes in preflight and after it are made in code, typography, headline and crop. Never call the
     image model again for a fix, except one new cover background in total. Never re-render the full video for a
     cover/headline/hook problem; those are caught here. A reel that cannot pass preflight in 3 rounds is `FAILED`
     before any video render.
1. `node news-reel/reel_render.mjs --dir=work/story --page=<pm/<id>.html | glass.html | fallback engine> --mode=check`
   (the prompt chosen in §4.3 step 0; §4.0 rules apply). Also render the stills the prompt's own `<start>`/`<build>` asks for,
   and review them yourself; Read every
   `out/sheet*.jpg`. Fix ISSUES (word mismatch), text overflow, wrong/ugly cut-outs, a visual that does
   not match its sentence, distorted people/products. Max 3 rounds.
1b. **Sound design (user rule 2026-10-29):** the engine's `SCENES[].sfx` cues follow STORY_SPEC "Sound design"
   (a sound that matches each motion, never a whoosh on every cut); run `node news-reel/sfx/generate.mjs` once if a
   library file is missing. After assembly, `reel.json → sfx` must show ≤ 2 whooshes and no sound over 40 %.
2. `--mode=video` in the background (run it with a timeout of at least 60 min), then `python3 news-reel/reel_assemble.py --dir work/story`:
   `reel.json` must show 40–55 s (§4.0), −15.5…−12 LUFS, true peak ≤ −1 dBFS; H.264 1080×1920 30 fps + AAC.
3. **Attention gate (§4.0 rule 6, blocking):** `python3 news-reel/reel_qa.py work/story/reel.mp4`; exit 3 → fix
   and re-render. Read `work/story/qa/contact.jpg` second by second against the narration.
3b. **Designed cover (user rule 2026-10-23).** Every reel gets its own cover, not a video frame. It works
   like a YouTube thumbnail: very eye-catching and on trend, with a headline that makes the viewer stop.
   - Background: one `python3 meshkani-pro/scripts/gen_image.py --kind story` image (≈ $0.05), written
     with the §8.2 prompt-engineering checklist. It shows one strong focal subject in the upper 60% with
     dramatic light and a clear emotion; the lower 40% stays dark or calm for the headline. No text,
     letters, numbers or logos in the image. Pass the real product photo as `--ref` when there is one.
   - `work/story/cover.json`:
     - `bg`
     - `logo`: the real logo, §4.3 step 2 — only of the story's main subject (the company, lab or product the
       news is about). A technology merely used inside the story (e.g. the model an experiment ran on) is
       named in the reel, not put on the cover (user question 2026-10-24 on REEL-007's Claude chip).
     - `logo_label`: the brand name, if the logo is an icon only
     - `kicker`: 1–3 words, such as «فوری», «مطالعه‌ی Science», «بی‌سابقه»
     - `title`: 3–7 words in Persian; one or two `*accent*` words; at most one `|` line break
     - `sub`: optional, ≤ 6 words
     - `accent` / `ink`: colours
   - **Headline position varies (user rule 2026-10-24):** `cover.json → pos` is `top`, `middle` or `bottom`
     (optionally `align: right`). Never the same position as the previous reel cover; plan it before the
     background, and write the background prompt so the calm area sits where the headline goes. Record `pos`
     in the slot file.
   - **Clear before clever (user rule 2026-10-24):** a viewer who has not seen the news must understand the
     headline at once. No unexplained nicknames or riddles («اردک‌ها» for robots, «۳۰ ساعت تنها چی‌کار
     می‌کنه؟» without a subject); speak to the viewer («اگه تو… چی‌کار می‌کنی؟») or name the real thing.
   - **The cover is its own design, never the video's look (user rule 2026-10-26).** It is the first hook, so it is
     always a premium photoreal thumbnail aimed at the reel's audience (for a female audience: a real, attractive,
     on-topic person or product, warm rich colour, beauty-campaign light), with a big plain headline and the real
     logo. Even when the reel is riso, paper, clay, kinetic type or UI, the cover is not drawn in that style.
     One `gen_image.py --kind story` background (≈ $0.05).
   - **Big headline (user rule 2026-10-25):** the headline is rendered at 120–150 px (raised 2026-10-27) and has at most 9 words
     (4–7 read best); `cover_render.mjs` exits 5 when it cannot fit, so shorten it. It writes
     `cover_report.json` (font, words, position, md5) which the gate checks.
   - Render with `node news-reel/cover_render.mjs --dir=work/story`, which writes `cover.jpg` and the 4:5
     preview `cover_grid.jpg`. Exit 5 means a missing image or a headline that is too long; shorten it.
   - **Headline system (user rule 2026-10-24, mandatory):** follow `meshkani-pro/HEADLINES.md`.
     - Write 12 candidates across 6 angles and score them with `scripts/headline_score.py`.
     - No «هوش مصنوعی» (AI) or similar AI words on the cover. Use personal stakes, power names,
       conflict, commands and questions, always true to `allowed_claims`.
     - Record `cover.headline {text, angle, score, runner_up}`. The caption's first line and the reel's
       first spoken line use the same angle.
     - The same system applies to post slide 1 (§1.5).
   - Headline formula: curiosity gap + concrete stakes. Use a number, a contrast, a "you" or a question,
     for example «هوش مصنوعی *۲ برابر* پزشک‌ها؟» ("AI *twice* as good as doctors?") or
     «Walmart درش رو باز کرد، *Amazon* بست» ("Walmart opened its door, *Amazon* closed it"). Every word
     must be true to `allowed_claims`: a question for anything uncertain, never a false promise.
   - **Grid variety:** apply the rule in §1.5 (last 9 grid items, `grid_check.py`, `design_fingerprint`).
     The cover must differ clearly in colour and design type from the previous covers and slides.
   - Read both `cover.jpg` and `cover_grid.jpg`:
     - the headline is readable at phone-thumbnail size and the logo is crisp;
     - nothing important falls outside the 4:5 grid crop;
     - the cover differs from the last 3 covers (layout, colour, kicker).

     Regenerate the background at most twice. Record `cover` {prompt, title, kicker, logo source} in
     the slot file and the Reels Notes column. Insights (§6) track whether a cover's headline type wins
     reach.
4. `python3 news-reel/story_cut.py --dir work/story` → `story.mp4` (≤ 60 s) for the Story share.
5. **Independent critic (user rule 2026-10-25, blocking).** You never grade your own reel. Launch a fresh
   subagent (Agent tool, general-purpose, no shared context) and give it only: `cover.jpg`, `cover_grid.jpg`,
   `qa/contact.jpg`, the contact sheets of the previous 3 reels (download them from their packages), the
   headline and a 2-line story summary. Ask for five 1–10 scores with one-line reasons, as JSON:
   `cover_stop_power` (would a Persian scroller stop for this thumbnail in Explore?), `headline_clarity`
   (understood at once by someone who has not seen the news; big and readable at thumbnail size; **≤ 4 when such a person cannot say in one plain sentence what it means**, e.g. metaphors like «دستور آرایشگاه» or «اردک‌ها» for robots, user rule 2026-10-26),
   `hook` (first 2 s), `visual_match` (each second shows what is said), `style_distinct` (clearly a different
   look from the previous 3 reels), `motion_richness` (professional motion graphics with numbers, charts, UI, glow
   and layered elements, not photos sliding or zooming; rule 2b). Save it as `work/story/critic.json` `{"scores":{…},"notes":{…}}`.
6. **Gate (user rule 2026-10-25, blocking):** `story.json` must carry `content_id`, `motion_prompt`
   (catalog id), `engine` (the page you rendered with), `motion_category` and `layout`. Download
   `_automation/motion_history.json` (`config.json → google.motion_history_id`) and run
   `python3 news-reel/reel_gate.py --dir work/story --history motion_history.json`. It re-checks attention
   (reel_qa), that `cover.jpg` is the rendered designed cover (md5 vs `cover_report.json`, never a video
   frame), headline ≥ 120 px and ≤ 9 words, cover position ≠ previous reel, prompt and engine not in the last
   10 reels, engine not a renamed copy of a recent engine (> 60 % same code), category ≠ previous reel, and
   critic scores all ≥ 7, and a passing `preflight.json` (step 0). Exit 3 → fix in code/typography only (no new
   images, step 0 cost rule) and re-run the critic and the gate; at most 1 re-render. Still failing → status `FAILED` with the gate reasons: a weak reel is
   skipped, never published. Save `gate.json` to the package and `gate.history_entry` to the slot file.

### 4.5 Storage, caption, sheet
1. Content ID `REEL-NNN`. Drive: `YYYY-MM-DD_REEL-NNN` under `ریلز` (`google.reels_folder_id`) with
   `REEL-NNN.mp4`, `REEL-NNN-cover.jpg`, `REEL-NNN-story.mp4` (the reel cut to ≤ 60 s at a sentence
   boundary + 1.7 s of the end card, for the Story share in §5 step 10; `story` block in the slot file); `story.json`, `elements.json`, `el/_sheet-*.jpg`,
   `timeline.json`, `dossier.json` to `_automation/packages/<date>_<HHMM>_REEL-NNN/`.
2. Caption like the reference: hook question line (+ one emoji at most); 2–4 short sentences that
   tell the idea with attribution; the closing question + «👇»; `منبع: <name>، <date>`; photo credit
   line if a real photo is used; 4–6 hashtags. No URLs.
3. `Reels` row (find-or-append, `USER_ENTERED`), A–T: Content ID · Reel Topic (`<field> | <idea>`) ·
   `Ready` · Production · Scheduled `<date> <09:00|15:00>:00` · blank · Source URLs · News Text (the idea, 2–3
   sentences) · **Reel Script** (all beats' text, numbered) · **Motion Graphics Prompt** (per beat: bg +
   visual type + elements) · Duration · Video Drive URL · Final Caption · blank · Source Post IDs
   («—» unless based on a post) · Voices · **Music Prompt** · **Image Edit Prompts** (the element-sheet
   prompts `el/_sheet-*.txt`) · blank · Notes (credits). Read back.
4. Reel slot file → `READY` (`kind`, `format: story`, `content_id`, `idea`, `sources`, `voices`, `video`,
   `cover`, `story` {drive_file_id, md5, duration, status PENDING, ids null}, `caption`, `script`,
   `creative` {angle, shape, preset, voice, tempo, motion_prompt {id, title, link}, motion_category,
   insight_used}, `cost_usd`, `sheet.reel_row`, `reel` ids null). The **Motion Graphics Prompt** column
   gets the adapted prompt from `motion_prompt.md`.
   Notes column: `angle=… shape=… preset=… voice=… tempo=… motion=<id>`. Log row (§3).

## 5. REEL_PUBLISH phase (starts 08:57 → 09:00, and 14:57 → 15:00 Tehran)

1. Setup (§0.1), control (§0.2), slot `tehran.py reel publish`, lock `__reel_publish`.
2. Reel slot file by status: `READY` → continue; `RESEARCHING…QA` → wait like §2.1; `PUBLISHING` /
   `NEEDS_RECONCILIATION` → reconcile only (§2.5 rules, container status + latest media); `PUBLISHED`
   → stop; missing / `FAILED` / `SKIPPED_*` → log, stop.
3. Cap: at most 3 reels a day and never two for the same slot (slot files + live media). Identity and publishing limit as §2.1
   (limit ≥ 1). Duplicate guard: last 10 media — a REELS item with this caption → record it, done.
3b. **Publish-time gate (user rule 2026-10-25, blocking).** Download the reel MP4 and the cover JPG from Drive
   (the exact files you will publish), the package's `story.json`, `cover_report.json` and `critic.json`, and
   `_automation/motion_history.json` (`config.json → google.motion_history_id`); run `python3 news-reel/reel_gate.py --dir <pkg> --history
   motion_history.json --reel <reel.mp4> --cover <cover.jpg>`. Exit 3 → status `SKIPPED_QA`, log the reasons,
   do not publish. After a verified publish, append `gate.history_entry` to `motion_history.json` on Drive.
4. `tehran.py wait-until <slot>` (09:00 or 15:00); `check-deadline <slot_key>` must exit 0. `DRY_RUN` → stop here.
5. `share_public` the MP4 and the cover. Re-check Kill Switch. `INSTAGRAM_POST_IG_USER_MEDIA` with
   `ig_user_id`, `media_type: REELS`, `video_url: public_image_url(video_id)`, `cover_url:
   public_image_url(cover_id)`, `caption` (raw `#`), `share_to_feed: true` → save `reel.container_id`,
   status `PUBLISHING`, write state.
6. Poll `INSTAGRAM_GET_POST_STATUS` every ~20 s (max ~10 min, inside the window) until `FINISHED`.
   `ERROR`/`EXPIRED` before any publish call → one new container is allowed; a second failure → `FAILED`.
7. `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` (`creation_id` = container, `max_wait_seconds` 60) → save
   `reel.media_id`. Unclear result → §2.5, never a second publish call before reconciliation.
8. Verify `INSTAGRAM_GET_IG_MEDIA` (`id,permalink,timestamp,media_product_type,media_type,username,caption`):
   `REELS`, right username, caption matches. Save permalink/time → `PUBLISHED`.
9. `Reels` row: Status `Published`, Actual Publish time, Published Post URL, Instagram Media ID.
10. **Reel as a Story** (when the slot file has `story.drive_file_id`; user rule 2026-10-21: every reel is
    also shared to the Story). Right after the reel is verified: re-check Kill Switch; `share_public`
    the story MP4; `INSTAGRAM_POST_IG_USER_MEDIA` with `media_type: STORIES`, `video_url:
    public_image_url(story_id)` → save `story.container_id` (`CONTAINER_CREATED`); poll
    `INSTAGRAM_GET_POST_STATUS` until `FINISHED` (max ~8 min); `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`
    → `story.media_id`; verify `INSTAGRAM_GET_IG_MEDIA` (`media_product_type` `STORY`, username);
    save permalink, published_at, expires_at (+24 h), `PUBLISHED`. Stories accept 3–60 s video: the
    story file is the reel cut to ≤ 60 s at a sentence boundary + the end card (REEL_PREPARE makes it:
    `REEL-NNN-story.mp4`). A failed story never re-publishes the reel. Add a `Stories` row (Story ID
    `REEL-NNN-STORY`, Parent `REEL-NNN`, Sequence 1, Published, times, Media ID, Parent Post URL =
    the reel permalink, Expires At).
11. `unshare_public` every shared file. Log row.

---

## 6. ANALYTICS phase — daily performance review (06:00 Tehran, before the day's first prepare; Fridays also weekly)

Goal: measure what the audience really does with every post, story and reel, then turn it into
`_automation/insights.json`, which steers the next PREPARE and REEL_PREPARE runs. Read-only on Instagram.
No publishing, no comments, no DMs, no account changes.

1. Setup (§0.1) and control (§0.2). The Kill Switch stops this phase too. Lock `analytics_<date>__analytics`.
2. **Inventory.**
   - List the last 30 days of media with `INSTAGRAM_GET_IG_USER_MEDIA` (`ig_user_id: me`, account
     `instagram_beath-billow`, fields `id,media_type,media_product_type,timestamp,permalink,caption,
     like_count,comments_count`), paging by `paging.cursors.after`.
   - Stories are not in that list: take their `media_id` from the slot files (posts' `stories[]`, reels'
     `story`).
   - Join every media id to its slot file to get content id, field, topic, slot time, format and `creative`
     (angle, shape, look, voice, tempo, motion_prompt, motion_category), plus the caption's first line as
     `hook`. Media that is not in any slot file (a manual repost) is tagged `manual`.
3. **Metrics** (`INSTAGRAM_GET_IG_MEDIA_INSIGHTS`, metric list by type; on a 400, retry once with fewer
   metrics, then mark the item unavailable):
   - reels: `views, reach, likes, comments, shares, saved, total_interactions, ig_reels_avg_watch_time,
     ig_reels_video_view_total_time`. Retention = avg watch time ÷ the reel's duration (from `reel.json`).
   - carousels: `views, reach, likes, comments, shares, saved, total_interactions`.
   - stories, while they are under 24 h old: `views, reach, replies, shares, navigation, follows,
     profile_visits, total_interactions`. A 06:00 run catches every story posted since yesterday 06:00.

   Measure each item at its 24 h mark, then again at 72 h and 7 days. Keep the latest value and the age it
   was measured at.
4. **Account.** `INSTAGRAM_GET_USER_INFO` (`followers_count`) and `INSTAGRAM_GET_USER_INSIGHTS` (`period:
   day`, `metric_type: total_value`, yesterday 00:00–24:00 Tehran, as Unix times): `reach, views,
   accounts_engaged, total_interactions, profile_views, follows_and_unfollows`. Empty metrics are valid.
5. **Sheet.**
   - Tab `Performance` (create it with this header if it is missing): one row per media id, updated in
     place (find by Media ID). Columns A–Y: Media ID · Content ID · Type · Published (Tehran) · Permalink ·
     Field · Topic · Format/Shape · Angle · Look · Motion Prompt · Voice · Hook · Age (h) · Views · Reach ·
     Likes · Comments · Shares · Saves · Interactions · Avg Watch (s) · Retention % · Follows/Profile Visits ·
     Score.
   - Tab `Insights` (create it if missing): one row per day. Columns: Date · Followers · Δ Followers ·
     Account Reach · Views · Accounts Engaged · Profile Views · Best item · Worst item · Top 3 lessons
     (Persian) · Changes applied for the next days.
6. **Score and learn.**
   - Score each item against the median of its own type over the last 14 days. Weights:
     - reels: 0.35 retention, 0.25 reach, 0.25 (shares + saves) ÷ reach, 0.15 follows/profile visits;
     - carousels: 0.4 reach, 0.4 (saves + shares) ÷ reach, 0.2 likes/comments;
     - stories: 0.5 reach ÷ followers, 0.3 navigation (forward taps or exits lower is better), 0.2 replies
       and shares.
   - Rank by field, topic type, format, angle, shape, look, motion prompt and category, voice gender, hook
     type (question / number / shock / "how-to" / name-led), publish slot, and reel length. A dimension
     value needs ≥ 3 items before it counts as a leader or a laggard. Until then it is `exploring`.
   - Write `_automation/insights.json` (create it the first time, then update it in place):
     `{updated, window_days, account{followers, delta_7d, reach_7d, engaged_7d}, leaders{field, topic,
     format, angle, shape, look, motion_category, motion_prompt, voice, hook, slot, length} (each a ranked
     list with median score and n), laggards{…}, hooks[lessons], caption[lessons], design[lessons],
     explore[next untried options], recommendations[3–5 concrete instructions for the next 48 h]}`.
   - Recommendations are concrete, for example «ریلزهای ۴۰–۵۵ ثانیه با قلاب سؤالی، retention بالاتری
     داشتند → ریلز بعدی ≤ ۵۵ ثانیه و قلاب سؤالی» ("40–55 s reels with a question hook had higher retention
     → next reel ≤ 55 s with a question hook"). Never write a recommendation that breaks the sector,
     fact, cap or style-rotation rules.
6b. **Headline learning** (HEADLINES.md step 4): join reach and the 3 s hold with
    `cover.headline.angle` / `slides[0].headline.angle` and its features (AI word, stake, name, tension,
    command, question, number, length). Keep `leaders.headline_angle` and `headline_lessons` in
    insights.json. When a word or pattern wins clearly (≥ 3 items, ≥ 2× the median reach), add it to
    `meshkani-pro/headline_lexicon.json → learned` with a bonus (commit and push).
7. **Fridays: weekly review.**
   - In the Insights row, compare the last 7 days with the 7 days before: followers, reach, average
     retention, saves + shares per reach.
   - Name the 3 strongest and 3 weakest patterns, and update `explore` with 3 new experiments for next
     week (a new motion category, angle or posting-hook type).
8. Log row (§3, Phase `ANALYTICS`): items measured, best item, the top recommendation.

Every PREPARE (§1.2 step 6) and REEL_PREPARE (§4.2 step 3, §4.3 step 0) reads `insights.json`. The
insights steer choices; they never override facts, rotation or the user's rules.

## 3. Reporting — sheet tab `Automation Log`

Append one row per phase end and per error (reel phases: Slot `YYYY-MM-DD|09:00` or `|15:00`, Phase `REEL_PREPARE`/`REEL_PUBLISH`, cost column = clean-plate cost), columns A–H:
`Logged At (Tehran) | Slot | Phase | Status | Content ID | Details | Image Cost (USD) | Run ID`.
Details are short, plain Persian or English, no secrets or temporary links.
The `Performance` and `Insights` tabs (§6) are the analytics view. No other notification channel is used.
