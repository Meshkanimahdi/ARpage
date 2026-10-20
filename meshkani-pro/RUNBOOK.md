# meshkani.pro cloud publisher — runbook

This file is the operating procedure for the scheduled cloud runs that research,
design, store and publish one Persian AI-news package per slot for the
Instagram account `meshkani.pro`. Each scheduled run starts a fresh Claude
session and is told which phase to run: **PREPARE** or **PUBLISH**.

Source of the rules: `TASK_SPEC.md` (standing task + cloud overrides) and «دستور کار انتقال انتشار محتوای meshkani.pro» (20 Oct 2026).
Where this file and that brief disagree, the brief's safety rules win: never
publish twice, never publish late, never publish unverified content.

---

## 0. Ground rules (both phases)

- Time zone is `Asia/Tehran` everywhere. Get times only from
  `python3 meshkani-pro/scripts/tehran.py`.
- Slots: `12:00` and `21:00`. Slot key format `YYYY-MM-DD|HH:MM`.
- Per slot at most 1 post + 3 stories; per Tehran day at most 2 posts + 6 stories.
- Publish window: from the slot time until slot time + 30 minutes. After that the
  slot is `SKIPPED_LATE`. A missed slot is never caught up later.
- Never print, log or write to the sheet: API keys, Drive upload-session URLs,
  public download links. The sheet gets only normal Drive view links.
- If anything is uncertain (identity, source, text accuracy, publish outcome),
  stop that slot, record why, and do not guess.
- Instagram account must read back as username `meshkani.pro`, id
  `17841471767180096`. The Composio alias `instagram_beath-billow` alone is not
  proof of identity.
- Text and research are done by you (Claude) in the session. Images are made only
  with OpenRouter (`OPENROUTER_API_KEY`), model from `config.json`.

### 0.1 Session setup

1. Code: if `meshkani-pro/` is not in the working directory, attach and clone
   the repo: `add_repo` owner `Meshkanimahdi`, repo `ARpage` (read), clone it,
   then `git fetch origin claude/ecstatic-davinci-1lqsug && git checkout FETCH_HEAD`.
   Work from the repo root. Read `meshkani-pro/config.json`.
2. Load deferred tools with ToolSearch:
   `select:mcp__Composio__COMPOSIO_SEARCH_TOOLS,mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL,mcp__Composio__COMPOSIO_REMOTE_WORKBENCH,mcp__Composio__COMPOSIO_GET_TOOL_SCHEMAS,mcp__Google_Drive__read_file_content,WebSearch,WebFetch`.
3. Call `COMPOSIO_SEARCH_TOOLS` once with `session: {generate_id: true}` and use
   cases "read and update google sheets values", "upload file to google drive",
   "publish instagram carousel and story". Keep the returned session id for
   every later Composio call.
4. Run the whole of `meshkani-pro/workbench/drive_bridge.py` in one
   `COMPOSIO_REMOTE_WORKBENCH` call (it prints `drive_bridge ready`). Workbench
   state persists between calls, so later cells can call its helpers.
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
  every Instagram call that returns an id.

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

## 1. PREPARE phase (starts 11:00 / 20:00 Tehran)

Goal: by publish time, a slot JSON with status `READY`, six QA-passed JPEGs in
Drive and `Ready` rows in the sheet. Keep going only while
`tehran.py check-deadline <slot_key>` exits 0; if the window closes, set
`SKIPPED_LATE`, log, stop.

### 1.1 Preconditions
1. Setup (§0.1), control (§0.2), lock `__prepare` (§0.4).
2. Look for the slot file in `slots/`. If it exists with any status other than
   `FAILED`, stop (already handled). If `FAILED`, you may start over only if
   no Instagram id was ever recorded in it.
3. Create the slot file with status `RESEARCHING` and `runs.prepare = RUN_ID`.

### 1.2 History and diversity
1. Read `Carousel Posts!A1:S200` and `Stories!A1:Q300`. The 14 most recent posts
   (by Content ID / dates) are the duplicate-check set; note their topics, source
   URLs, sectors (prefix of Post Topic, otherwise infer) and image prompts.
2. List `slots/` files of the last 7 Tehran days and read their `sector`,
   `source.url`, `source.dedupe_key`.
3. Read the last 20 feed posts of the account (`INSTAGRAM_GET_IG_USER_MEDIA`,
   fields `id,caption,permalink,timestamp`) as a live check.
4. Allowed sectors: not the sector of the previous package; no sector already
   used twice in the last 7 days — unless no other credible news exists (then
   record the reason in `errors` and later in the story Notes).
5. Also read `_automation/history/publish-state.json` and `stories-state.json`
   (ids in config: the completed original batch). The never-republish list from the legacy state file (POST-001…POST-010,
   POST-011, the standalone test story) and everything in the sheet is history.

### 1.3 Research (live)
Use WebSearch/WebFetch, English first, local language if needed:

> با ساعت فعلی تهران و جست‌وجوی زنده، خبرهای معتبر ۲۴ تا ۴۸ ساعت اخیر را دربارهٔ اثر واقعی
> هوش مصنوعی در چند صنعت پیدا کن. قبل از انتخاب، ۱۴ پست اخیر و سابقهٔ هفت روز گذشته را بررسی
> کن. برای هر نامزد، منبع اصلی، تاریخ انتشار، تاریخ رخداد، ادعای دقیق و محدودیت آن را
> استخراج کن. موضوع‌های تکراری و شایعات را حذف کن. حوزهٔ کمتر پوشش‌داده‌شده را در صورت وجود
> خبر هم‌سطح ترجیح بده. اگر خبر مناسب نیست، خروجی را «خبر مناسب پیدا نشد» قرار بده؛ خبر یا
> آمار نساز.

- Aim for 15–30 candidates across sectors (medicine/health, automotive/transport,
  food/agriculture, education, science, energy/climate, robotics/manufacturing,
  business, art/media, everyday services, public policy). Do not pad the list.
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

### 1.4 Content (Persian)
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

### 1.6 Prompts and generation
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
> «`[تیتر دقیق]`» و «`[متن کوتاه دقیق]`». پایین تصویر کوچک: «@meshkani.pro» و «`[n] از ۳`».
> تیتر، تصویر و متن بخشی از یک صفحه‌آرایی واحد و متناسب با موضوع باشند. متن دیگری نساز.
> اعداد، نام محصول و ادعا را تغییر نده. ترکیب‌بندی این تصویر با دو تصویر دیگر متفاوت باشد.
>
> `[پست: نسبت ۴:۵؛ همهٔ متن‌ها، حتی برچسب‌ها و امضای پایین، دست‌کم ۸٪ از هر چهار لبه فاصله داشته باشند.]`
> `[استوری: نسبت ۹:۱۶؛ هیچ متنی در ۱۲٪ بالای تصویر و ۱۵٪ پایین تصویر نباشد.]`
> از شبیه‌سازی دکمه یا استیکر تعاملی، نشان دادن صحنهٔ تولیدی به‌عنوان عکس واقعی و عناصر
> نامربوط به خبر خودداری کن. `[اگر مفهومی است: برچسب کوچک و خوانای «تصویر مفهومی» را در طراحی
> در نظر بگیر.]`

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
   labels and the @meshkani.pro line) closer than ~6% to any edge, fits the news and brief, not
   a near-copy of recent packages, no misleading fake elements, concept label
   present when needed.
2. Upload the finals to Drive (§1.8 folders) so Drive can OCR them; read each back
   with `mcp__Google_Drive__read_file_content` and compare:
   write the approved text (title + body) and the OCR text to files and run
   `python3 meshkani-pro/scripts/text_compare.py approved.txt ocr.txt`. OCR is a
   signal; the visual review decides.
3. Fix loop (max 2 attempts per image): regenerate with `--ref` the failing raw
   image plus a precise correction prompt ("keep everything, only fix the word X
   to Y"), or regenerate from the prompt. Replace the Drive file content with
   `open_update(file_id, "image/jpeg")` so ids stay stable. Still failing →
   status `FAILED`, log which image and why, stop (do not publish a partial set).
4. Re-check every claim against the primary source once more (look for
   corrections or denials since research).
5. File checks from the finalize reports: 3 × 1080×1350 JPEG, 3 × 1080×1920
   JPEG, each < 8 MB, Drive `md5Checksum` == local md5, correct order and names.
6. Write `qa` results into the slot JSON. Never pass QA just because files exist.

### 1.8 Storage (Drive + sheet)
- Folder names: `YYYY-MM-DD_POST-NNN_<short-english-slug>` under
  `Images` (`post_images_folder_id`) for slides and under `استوری`
  (`story_images_folder_id`) for stories (`ensure_folder`). Raw model images and
  the dossier go to `_automation/packages/...`.
- Files: `POST-NNN-slide-1.jpg … -3.jpg`, `POST-NNN-STORY-1.jpg … -3.jpg`.
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
  - Read the rows back and confirm. Never touch other tabs (Reels), formulas,
    formatting or validation; never insert duplicate rows for the same id.
- Slot JSON → `READY` with every id, md5 and URL. Log row (§3).

---

## 2. PUBLISH phase (starts 12:00 / 21:00 Tehran)

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
4. Identity: `INSTAGRAM_GET_USER_INFO` (`account: instagram_beath-billow`) must
   return username `meshkani.pro`, user_id `17841471767180096`, type
   `MEDIA_CREATOR`; `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT` must leave at
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
1. For slides 1→3 in order: `INSTAGRAM_POST_IG_USER_MEDIA` with `image_url`,
   `is_carousel_item: true`. Save each id to `post.child_container_ids`
   immediately (write the state file).
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
   in order. Save permalink and `published_at`; status `PUBLISHED`.
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
- The evening (21:00) publish run also writes a `DAY_SUMMARY` log row: both post
  links, story statuses, total image cost of the day.

---

## 3. Reporting — sheet tab `Automation Log`

Append one row per phase end and per error, columns A–H:
`Logged At (Tehran) | Slot | Phase | Status | Content ID | Details | Image Cost (USD) | Run ID`.
Details are short, plain Persian or English, no secrets or temporary links.
No other notification channel is used.
