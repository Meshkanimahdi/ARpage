# meshkani.pro cloud publisher — runbook

This file is the operating procedure for the scheduled cloud runs that research,
design, store and publish one Persian AI-news package per slot for the
Instagram account `meshkani.pro`. Each scheduled run starts a fresh Claude
session and is told which phase to run: **PREPARE** or **PUBLISH** (posts, §1–§2) or
**REEL_PREPARE** / **REEL_PUBLISH** (the daily reel, §4–§5).

Daily schedule (Tehran): **09:00** reel of the previous day's two news · **12:00** post + 3 stories ·
**21:00** post + 3 stories. The reel is prepared the evening before (21:45, retry 23:15).

Source of the rules: `TASK_SPEC.md` (standing task + cloud overrides) and «دستور کار انتقال انتشار محتوای meshkani.pro» (20 Oct 2026).
Where this file and that brief disagree, the brief's safety rules win: never
publish twice, never publish late, never publish unverified content.

---

## 0. Ground rules (both phases)

- Time zone is `Asia/Tehran` everywhere. Get times only from
  `python3 meshkani-pro/scripts/tehran.py`.
- Slots: `12:00` and `21:00` (posts), `09:00` (reel). Slot key format `YYYY-MM-DD|HH:MM`.
- Per slot at most 1 post + 3 stories; per Tehran day at most 2 posts + 6 stories + 1 reel.
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

## 1. PREPARE phase (main 10:30 / 19:30, retry 11:05 / 20:05 Tehran)

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

### 1.3 Research (live)
Use WebSearch/WebFetch, English first, local language if needed:

> با ساعت فعلی تهران و جست‌وجوی زنده، خبرهای معتبر ۲۴ تا ۴۸ ساعت اخیر را دربارهٔ اثر واقعی
> هوش مصنوعی در چند صنعت پیدا کن. قبل از انتخاب، ۱۴ پست اخیر و سابقهٔ هفت روز گذشته را بررسی
> کن. برای هر نامزد، منبع اصلی، تاریخ انتشار، تاریخ رخداد، ادعای دقیق و محدودیت آن را
> استخراج کن. موضوع‌های تکراری و شایعات را حذف کن. حوزهٔ کمتر پوشش‌داده‌شده را در صورت وجود
> خبر هم‌سطح ترجیح بده. اگر خبر مناسب نیست، خروجی را «خبر مناسب پیدا نشد» قرار بده؛ خبر یا
> آمار نساز.

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
> «`[تیتر دقیق]`» و «`[متن کوتاه دقیق]`». `[پست: پایین تصویر کوچک «@meshkani.pro» و «[n] از ۳»]`
> تیتر، تصویر و متن بخشی از یک صفحه‌آرایی واحد و متناسب با موضوع باشند. متن دیگری نساز.
> اعداد، نام محصول و ادعا را تغییر نده. ترکیب‌بندی این تصویر با دو تصویر دیگر متفاوت باشد.
>
> `[پست: نسبت ۴:۵؛ همهٔ متن‌ها، حتی برچسب‌ها و امضای پایین، دست‌کم ۸٪ از هر چهار لبه فاصله داشته باشند.]`
> `[استوری: نسبت ۹:۱۶؛ هیچ متنی در ۱۲٪ بالای تصویر نباشد. پایین‌ترین عنصر تصویر فقط «@meshkani.pro» است، کوچک و دقیقاً وسط‌چین، درست بالای ۱۵٪ پایینی تصویر؛ هیچ متن دیگری پایین‌تر از آن نیاید. شماره‌گذاری (مثل «۱ از ۳») و برچسب «تصویر مفهومی» در استوری نیاید.]`
> از شبیه‌سازی دکمه یا استیکر تعاملی، نشان دادن صحنهٔ تولیدی به‌عنوان عکس واقعی و عناصر
> نامربوط به خبر خودداری کن. `[فقط برای پست، اگر مفهومی است: برچسب کوچک و خوانای «تصویر مفهومی» را
> در طراحی در نظر بگیر.]`

Story layout rule (user, 2026-10-20): stories carry **no** sequence number and
**no** «تصویر مفهومی» label; the only footer is `@meshkani.pro`, small, exactly
centred, the lowest element of the image, sitting just above the 280 px bottom
safe line. QA checks this.

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
   reference check of §1.5.1 step 4 passes.
2. Upload the finals to Drive (§1.8 folders) so Drive can OCR them; read each back
   with `mcp__Google_Drive__read_file_content` and compare (Drive often does not
   OCR new files for minutes; if no text comes back after ~2 tries, record
   `ocr: not indexed` and rely on the visual review — never block on OCR):
   write the approved text (title + body) and the OCR text to files and run
   `python3 meshkani-pro/scripts/text_compare.py approved.txt ocr.txt`. OCR is a
   signal; the visual review decides.
3. Fix loop (max 2 attempts per image). Margin-only failures (text too close to an
   edge or inside the story unsafe zone) may instead be fixed with
   `finalize.py --inset 0.88`, then re-checked visually. regenerate with `--ref` the failing raw
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
  - Read the rows back and confirm. Never touch other tabs (the reel phases own `Reels`), formulas,
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

## 4. REEL_PREPARE phase (main 21:45, retry 23:15 Tehran)

Goal: by the next morning, slot file `slot_<D+1>_0900.json` (`"kind": "reel"`) with status `READY`, a
QA-passed ≈60 s reel MP4 + cover in Drive and a `Ready` row in the `Reels` tab. The reel tells the two
news that were **published** in day D's 12:00 and 21:00 slots, in that order. Tools and format:
`news-reel/REEL_SPEC.md` (read it fully), voices `news-reel/VOICES.md`, style rules there too.

### 4.1 Preconditions
1. Setup (§0.1), control (§0.2). Slot: `python3 meshkani-pro/scripts/tehran.py reel prepare` (gives
   `slot_key`, `slot_file`, `source_day`, `source_slot_files`); none → log, stop. Lock
   `<slot_file without .json>__reel_prepare` (retry run: `__reel_prepare_retry`).
2. Reel slot file: same rules as §1.1 (missing → create `RESEARCHING`; finished → stop; stale >15 min
   → take over; fresh → stop). The retry run stops quietly if the main run is alive or finished.
3. If the evening post is still `PUBLISHING`/not final, wait (≤ 9-minute `wait-until` steps) until
   22:45 at most. Then read both source slot files. Use every source whose post is `PUBLISHED`
   (with `post.permalink`):
   - two → normal two-news reel;
   - one → a one-news reel (≈32 s, same template with one entry in `news`, end line «جزئیات کامل، توی پست دیروز.»);
   - none → status `SKIPPED_NO_NEWS`, log, stop.
4. `npm`/fonts: `bash news-reel/setup.sh`.

### 4.2 Material
1. For each source: the six final JPEGs (`slides[].drive_file_id`, `stories[].drive_file_id`) →
   `GOOGLEDRIVE_DOWNLOAD_FILE` (`fileId`) → `curl` the returned `s3url` into `work/reel/A/` (news 1) and
   `work/reel/B/` (news 2) as `slide-1..3.jpg`, `story-1..3.jpg`. Read its dossier
   (`folders.package` → `dossier.json`) for `allowed_claims`, `limits`, `source`, and the caption.
2. Re-check each news once with WebSearch for corrections/denials since it was posted. A news that has
   been corrected or denied is dropped from the reel (log why).
3. Look at all 12 images (make contact sheets with ffmpeg `hstack` and Read them) and pick the crops.

### 4.3 Script, voices, spec
1. Write `work/reel/spec.json` per REEL_SPEC.md: fresh narration (never the on-image text), only
   allowed claims, 4–6 lines per news, scenes per news (hook first), `tag` = the field in Persian,
   `music_prompt` that fits both news.
2. Voices: two different narrators, one female and one male, each fitting its news; the opening gender
   alternates day to day (previous reel slot file → `voices`). The closing line uses news 2's voice.
3. Clean plates only if needed (REEL_SPEC → Visuals), ≤ 2 per news; record prompt + cost.
4. `node news-reel/reel_voice.mjs --dir=work/reel`. Exit 3 → shorten lines; exit 4 → respell/rephrase
   the flagged lines (speech-to-text must hear the right words); max 3 rounds, else `FAILED`.

### 4.4 Render and QC
1. `node news-reel/reel_render.mjs --dir=work/reel --mode=check`; Read every `out/sheet*.jpg`. Check:
   Persian text correct and fully inside the frame, nothing overlapping, crops free of baked-in text,
   each scene matches its line, 3D/glow/particles present, no distorted product/person. Fix the spec and
   repeat (max 3 rounds).
2. `node news-reel/reel_render.mjs --dir=work/reel --mode=video` (run in the background, ~15 min), then
   `python3 news-reel/reel_assemble.py --dir work/reel`. `reel.json` must show duration ≤ 61 s,
   −15.5…−12 LUFS, true peak ≤ −1 dBFS; `ffprobe` must show H.264 1080×1920 30 fps + AAC 48 kHz.
3. Extract frames at 2 s, the divider and the last second (`ffmpeg -ss`) and Read them (logo intro, divider,
   end card present). Read `cover.jpg`.

### 4.5 Storage, caption, sheet
1. Content ID `REEL-NNN` (next after the highest in the `Reels` tab and reel slot files).
   Drive: folder `YYYY-MM-DD_REEL-NNN` under `ریلز` (`google.reels_folder_id`) with `REEL-NNN.mp4` and
   `REEL-NNN-cover.jpg` (resumable upload as in §0.3; md5 must match). `spec.json`, `timeline.json`,
   `voice/qc.json` go to `_automation/packages/<D+1>_0900_REEL-NNN/`.
2. Caption (Persian, user caption rules of §1.4 apply): one hook line; per news 1–2 sentences that
   summarise it; one question; source line `منبع: <name>، <date> · <name>، <date>`; no URLs; no
   real/concept note; 4–6 hashtags.
3. `Reels` row (find-or-append on column A, `USER_ENTERED`), columns A–T: Content ID · Reel Topic
   (`<field 1> + <field 2> | <topic 1> / <topic 2>`) · Status `Ready` · Production time · Scheduled
   `<D+1> 09:00:00` · blank · Source URLs (one per line) · News Text (the two summaries) · **Reel Script**
   (every line with its id and narrator) · **Motion Graphics Prompt** (the scene list: per scene type,
   line, on-screen texts and image crops — compact text) · Duration (s) · Video Drive view URL · Final
   Caption · blank · Source Post IDs · Voices · **Music Prompt** · **Image Edit Prompts** (clean-plate
   prompts or «—») · blank · Notes. Read back to confirm.
4. Reel slot file → `READY` with: `kind`, `content_id`, `sources` [{slot_key, content_id, permalink}],
   `voices` [{news, name, id, gender}], `video` {drive_file_id, md5, bytes, duration, lufs, view_url},
   `cover` {drive_file_id}, `caption`, `script`, `cost_usd` (clean plates), `sheet.reel_row`,
   `reel` {container_id, media_id, permalink, published_at} all null. Log row (§3).

## 5. REEL_PUBLISH phase (starts 08:57 → publish 09:00 Tehran)

1. Setup (§0.1), control (§0.2), slot `tehran.py reel publish`, lock `__reel_publish`.
2. Reel slot file by status: `READY` → continue; `RESEARCHING…QA` → wait like §2.1; `PUBLISHING` /
   `NEEDS_RECONCILIATION` → reconcile only (§2.5 rules, container status + latest media); `PUBLISHED`
   → stop; missing / `FAILED` / `SKIPPED_*` → log, stop.
3. Cap: no other reel published today (slot files + live media). Identity and publishing limit as §2.1
   (limit ≥ 1). Duplicate guard: last 10 media — a REELS item with this caption → record it, done.
4. `tehran.py wait-until 09:00`; `check-deadline <slot_key>` must exit 0. `DRY_RUN` → stop here.
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
   `unshare_public` both files. Log row.

---

## 3. Reporting — sheet tab `Automation Log`

Append one row per phase end and per error (reel phases: Slot `YYYY-MM-DD|09:00`, Phase `REEL_PREPARE`/`REEL_PUBLISH`, cost column = clean-plate cost), columns A–H:
`Logged At (Tehran) | Slot | Phase | Status | Content ID | Details | Image Cost (USD) | Run ID`.
Details are short, plain Persian or English, no secrets or temporary links.
No other notification channel is used.
