# Daily story reel — creative and production spec (user decisions, 2026-10-21)

**Goal:** two reels every day, at 09:00 and 15:00 Tehran (user 2026-10-21), each grabbing attention in the first second, keeps people
watching to the end (watch time, completion, rewatches) and makes them comment — built from a
**trending, verified AI story** and told as a short story. 60–90 s, one narrator, **the on-screen text
is the narration, word by word**. Approved reference: REEL-002 (Hinton, «لوله‌کش شو»), inspired by
@mgh.mobin «انسان‌ها، گاوهای آینده‌ان؟». The old two-news reel (REEL_SPEC.md) is retired; the
neon/particles/3D rule of VOICES.md is no longer mandatory — it is one of the looks below.

**Never the same reel twice:** every reel varies its *angle*, *story shape*, *look*, *voice* and
*rhythm* — also between the two reels of the same day. Before writing, read the last 7 rows of the `Reels` tab (columns B, P, Notes) and the
previous reel's `story.json`; record today's choices in the slot file → `creative` and in Notes.

---

## 1. Angle (what the story is about) — rotate
Pick today's story from what is trending in AI in the last 24–72 h (several independent outlets,
platform buzz, big launches, viral demos, notable statements, new studies). Verify it like news
(RUNBOOK §1.3). Search the angles below widely — run a few searches in at least 5 different angles
every day (e.g. "AI <angle keyword> this week", "AI startup shut down", "AI game viral") before
choosing. Never the same angle two days in a row, and no angle more than twice in 7 days.

| # | Angle | What to look for | Example hook |
|---|---|---|---|
| A | Work and jobs | jobs that change or disappear, new skills, hiring, layoffs | «اگه می‌خوای شغلت امن بمونه…» |
| B | **Agents doing real work** | an AI agent that ran a task, a team, a shop, research, code | «یه ایجنت، کار یه تیم پنج‌نفره رو تو یه شب انجام داد.» |
| C | Launches and viral demos | the new model/app/gadget everyone shares — what it really can and cannot do | «همه دارن این ویدیو رو دست‌به‌دست می‌کنن…» |
| D | Entertainment and games | AI in games, NPCs, game studios, streaming, music charts, film, celebrities, deepfake trends | «این شخصیت بازی، دیالوگش رو خودش می‌سازه.» |
| E | Creative work | AI art, design, music, writing, photography, advertising — and the artists' reaction | «این آهنگ رو هیچ آدمی نساخته…» |
| F | Food and nutrition | recipes, restaurants, food apps, farming-to-plate, food waste | «آشپز این رستوران… یه الگوریتمه.» |
| G | Health and diet | AI in diet planning, fitness, sleep, diagnosis, wearables — reported results only, with limits; **never medical or diet advice** | «یه اپ گفت چی بخوری… و نتیجه‌اش این شد.» |
| H | Failed and struggling startups | big AI startups that shut down, burned money, pivoted or overpromised — what went wrong | «یه میلیارد دلار جمع کردن… و تعطیل شدن.» |
| I | Money and business | who wins, who loses, big deals, prices, investments | «این شرکت با یه تصمیم…» |
| J | Science and space | discoveries, research speed, materials, climate, space | «یه هوش مصنوعی تو چند ساعت چیزی پیدا کرد که…» |
| K | Everyday life and home | phones, cars, shopping, travel, dating, kids, education, smart home | «گوشیت از امروز این کار رو بدون تو می‌کنه.» |
| L | Society, law, risk, ethics, safety | rules, lawsuits, scams, privacy, misinformation — without fear-mongering | «مشکل ربات قاتل نیست…» |
| M | Women and AI | women founders and creators, women's health tech, safety, work | «اونی که این ابزار رو ساخت…» |
| N | Sports | training, referees, scouting, injuries, fan experience | «داور این بازی… دوربین بود.» |
| O | Useful today | one thing the viewer can do with AI today (only real, available tools) | «این کار رو امروز امتحان کن…» |
| P | Myth vs. fact | a popular belief about AI, and what is actually true | «همه فکر می‌کنن… ولی…» |
| Q | Weird and surprising | odd, funny, unexpected AI stories that are real and verified | «باورت نمی‌شه این کار رو به هوش مصنوعی سپردن…» |

- A named person/podcast/interview is **optional** — use it only when the person *is* the story.
  At most 2 of any 7 reels may be built around one person's quote.
- Health/diet and food stories: report what was found and its limits (sample, who ran it, not
  peer-reviewed…), add «این توصیهٔ پزشکی نیست» in the caption, never tell people what to eat or take.
- Failed-startup stories: facts only (funding, dates, official statements, reputable reporting); no
  mocking of named people, no speculation presented as fact.
- Women-focused topics get a female narrator.
- Do not repeat a story, company or person used in the last 14 reels.

## 2. Story shape — rotate (never the same two days in a row)
1. **Shock fact** → explanation → why it matters → question.
2. **You-scenario**: «فردا صبح بیدار می‌شی و…» → the change → the twist → question.
3. **Before / after**: how it was → how it is now → who it affects.
4. **Countdown**: «۳ چیزی که…» with the strongest saved for last.
5. **Mystery / open loop**: a strange result first, the answer revealed at ~70%.
6. **Case story**: one company / agent / person, step by step, then the lesson.
7. **Two sides**: the claim, the push-back, what we actually know.
8. **Timeline / prediction**: now → in 1 year → in 5 years (only sourced predictions).
9. **Look-alikes, decoded** (reference: @buildwithomkar «They look the same. They're not.», 480k views):
   3–5 AI products/models/agents that look the same but do different jobs. Hook «این N تا *شبیه هم‌اند.*»
   over a `lineup` of tall cards → «ولی نیستن.» as the cards shrink (`compact_at`) → one chapter per item
   (`tabs` + `tab`, its own `tint`, one product-specific visual: `prompt` / `tasks` / `roles` / `ui` /
   a real screenshot) → «خلاصه‌ش» `stack` (last row = the surprise) → «جایی که مهمه» `table`
   (price · privacy · strength · limit, rows lighting up as they are spoken) → «تو کدومو استفاده می‌کنی؟».
   Look `soft-ui`, calm confident voice, 55–75 s. Every cell of the table is a verified fact from
   `dossier.json` (pricing page, docs, launch post); unknown = «اعلام نشده», never a guess. Product
   marks: the real logo only from the official press kit fetched through Drive, otherwise a coloured
   letter mark (`mark` + `color`); never a generated fake logo.

## 3. Hooks and watch-time craft
- **Second 0–1.5:** the strongest line + a visual pattern interrupt (huge word, unexpected object,
  stamp, split). No logo, no greeting, no «سلام». The hook text is also the cover text.
- Hook formulas (vary them): bold claim · direct "you" question · surprising number · contradiction
  («همه فکر می‌کنن… ولی») · insider («کسی بهت نمی‌گه») · stakes («اگه … رو ندونی»).
  Never promise what the reel does not deliver; no fake urgency; no invented numbers.
- **Open loop** in the first 5 s that pays off near the end. **Re-hook** about every 15 s
  («ولی اصل ماجرا اینجاست»، «و اینجا عجیب می‌شه»).
- **Pattern change** every 2–4 s: new visual, background swap, a huge word, a split, a counter.
- **Ending:** the payoff, then one simple question that is easy to answer in a comment
  («تو کدوم طرفی؟»، «کار تو پشت میزه یا با دست؟») + «جوابتو تو کامنت بنویس». Optionally make the
  last line lead back into the first (loop) so a rewatch feels natural.
- Caption = hook line + 2–4 sentences + the question + 👇 + source/date + credits + 4–6 hashtags.

## 4. Look — vary it (`story.json → theme`)
`theme = {preset, font_display, font_text, accent, paper, dark, ink, mode: color|mono, density: minimal|normal|busy}`
Backgrounds per beat: `paper`, `dark`, `accent` (a solid accent page for punch lines). A light accent
(e.g. acid yellow) automatically turns paper keywords into ink with an accent marker band.
Fonts available: `Vaz` (Vazirmatn), `Lalezar` (heavy display), `Kufi` (Noto Kufi), `Markazi` (serif,
editorial), `Reem` (geometric kufi), `Messiri` (soft), `Changa` (tech), `Inter` (Latin).

| preset | feel | fonts (display / text) | colours | mode / density | fits |
|---|---|---|---|---|---|
| `paper-ember` | the reference look | Vaz / Vaz | cream, near-black, orange #FF6A13 | color / normal | work, society |
| `mono-press` | newspaper, serious | Markazi / Vaz | white, black, red #E0242B | mono / minimal | policy, risk, investigations |
| `acid-pop` | loud, young, viral | Lalezar / Changa | light grey, black, acid #E8FF3C | color / busy | launches, demos, trends |
| `neon-night` | futuristic | Changa / Vaz | navy #070B1A, cyan #10F5EE | color / busy | agents, robots, breakthroughs |
| `clinic-calm` | clean, trustworthy | Kufi / Vaz | white, ink, teal #0FB5A6 | color / minimal | health, science |
| `terminal` | data, money | Changa / Vaz | black, green #00E676 | mono / busy | finance, markets, numbers |
| `warm-story` | human, soft | Messiri / Vaz | beige #F3E9DC, brown, terracotta #D2643C | color / minimal | women, family, education |
| `royal-tech` | premium | Reem / Vaz | deep purple #140B2E, gold #F2C14E | color / normal | big companies, money |
| `maxi-pop` | maximalist, fashion-magazine collage | Lalezar / Lalezar | a new clashing field every beat (yellow, pink, blue, green, orange, ice) + pink/blue/yellow/green patterns | color / busy | fashion, design, art, pop culture, launches with hype |
| `maxi-photo` | photoreal maximalist editorial sets (user reference 2026-10-22) | Lalezar poster headline / Vaz caption | whatever the scene photos carry: hot pink, sunflower yellow, cobalt, emerald, leopard / zebra / checker prints | color / minimal | fashion, design, lifestyle, beauty, culture |
| `soft-ui` | premium product explainer | Markazi headline / Vaz caption | off-white + pastel blobs (`tint` per beat), ink, blue #3B6BFF | color / minimal | comparisons, product launches, "how X works" (shape 9) |

`maxi-pop` adds: sunburst, polka dots, checkerboard and stripe bands, a spinning star badge (`story.badge`,
2–3 words), two tickers in opposite directions, sticker cut-outs (white border + hard black shadow), black/pink
boxed keywords tilted ±3°. Elements for it: `style` = «maximalist fashion-editorial collage cut-outs, glossy,
saturated, bold patterns, sequins and texture, studio light», 1–3 objects per beat, overlapping.

`maxi-photo` (engine story.html, visual `scene` on every beat): full-bleed photoreal maximalist sets — a
designer's studio wall, a dressing room, a runway backstage, a boutique — densely layered with props,
patterns, plants, neon shapes (no letters), real depth and warm light. Headlines are typeset by us on a
**blank poster / frame the scene reserves** (`poster` box from `python3 news-reel/find_poster.py img`,
`poster_text` with `*accent*` and `|`, `poster_sub`); the narration sits in a frosted-glass pill. The
camera explores each set: `from`/`to` = [x, y, zoom] in frame pixels, so 2–3 beats can travel across the
details of one image (poster → the sequinned dress → the tablet on the desk). Images: 4–7 scenes per reel
with `gen_image.py --kind story` (≈ $0.044 each; cap $0.40 for this look), prompt pattern: «Photorealistic
editorial photograph, vertical 9:16, of a maximalist … densely layered … [subject props tied to the beat] …
In the exact centre: a large EMPTY cream poster in a thin black frame (≈60% width, 22–58% height),
completely blank … 35mm, soft daylight + warm lamp glow … No text anywhere, no letters, no logos, no
watermark, no people» (people only when the beat needs a real person, from a real photo). Read every scene
before use; reject garbled letters, logos, warped objects. Never the flat `maxi-pop` stickers for this look.

`soft-ui` changes the layout: an optional serif headline on top (`head`, with `*word*` turning from
grey to ink at `head_at`, `head_sub` under it), the narration as a one-line karaoke caption near the
bottom (all words visible in grey, each turns ink/accent as it is spoken), soft white UI cards, focus-pull
(blur) cuts, optional chapter tabs (`story.tabs` = labels, `beat.tab` = active index).

Rules: match the preset to the story's mood; never the same preset two days in a row; one preset per
reel. Minimal = few elements, lots of air, slower cuts; busy = ticker, corner labels, dot texture,
more objects per beat. The element sheets follow the look (`style` in elements.json) but are always
**realistic, stylish and professional** (§8.2): photoreal premium product cut-outs, black-and-white press
photos, refined 3D renders with real materials, neon glass. Never flat clipart or toy-like clay.

## 5. Voice — chosen per story (ElevenLabs **eleven_v4** only)
| voice | id | gender | best for |
|---|---|---|---|
| Hooman — dry, friendly | XzieuK0bwYWT9Kl1LhLs | male | work, tech, everyday explainers |
| Kourosh — confident ad | VKDkQOjcRZb7aNtJGaWt | male | launches, bold claims, business |
| Kaveh — cheerful creator | xKk80LgyXTAl6McCiFke | male | useful tips, fun demos |
| Aran — professional, mature | PEdcOLzbXYhL8IKOswXB | male | serious, policy, science |
| Connery — narrator | 4D8rX5FMrycxXbF6iW0I | male | story-driven, mystery, history |
| Niloofar — curious creator | N7wuKHXQQ5fKd75noieq | female | trends, tech for everyone |
| Setareh — expressive creator | 8Ebkg5uUcbSbeqGucAoR | female | culture, art, emotional stories |
| Roya — warm narrator | ndcUYGFbbd96WXiZVVaQ | female | women's topics, health, human stories |
| Farideh — proud ad | GSj19hKjOQsPFCZlq1le | female | strong statements, business |

- Pick the voice whose character fits the story and its audience; a women-focused story → female.
  Not the same voice two days in a row. Record it (`voice`, `voice_name`).
- **Audio tags on every script** (skill `skill-elevenlabs-tts`): English, lowercase, one per bracket,
  placed where the tone turns (about every 1–2 beats), never the same tag twice in a row, matched to
  the voice and the line. Starter set: `[curious]` `[excited]` `[serious]` `[whispers]` `[warm]`
  `[sarcastic]` `[dramatic]` `[thoughtful]` `[surprised]` `[firm]` `[laughs]` `[sighs]` `[playful]`.
- Pauses: punctuation (، . …) or `[short pause]` after a full stop — never an ellipsis plus a pause
  tag in the same spot.
- Numbers, dates, percentages, prices: say them as Persian words and show the short form
  with `{shown|spoken}` → `{۲۰۲۵|دو هزار و بیست و پنج}`, `{۴۰٪|چهل درصد}`.
- **Names and loanwords go to the voice in Latin (user rule 2026-10-23).** Brands, startups, products,
  models and people are written in English exactly as the company or person spells them: `OpenAI`,
  `ChatGPT`, `Anthropic`, `Nvidia`, `Sam Altman`, never «اوپن ای آی». Persian-script words that
  ElevenLabs misreads are also written in English: `code` (never «کد»), `prompt`, `agent`, `AI`, `app`;
  Persian suffixes stay Persian after a space (`code ها`, `prompt ها`). The caption may still show
  Persian when that reads better: `{کدنویسی|code نویسی}`. `news-reel/fa_lexicon.mjs` converts the common
  Persian spellings on the spoken side automatically (story_voice and reel_voice); add story-specific
  names in `story.json → lexicon: {"اسنپ فود": "Snappfood"}`. After the voice run, read `voice/qc.json`
  and fix any name that still sounds wrong by respelling it in Latin.
- A mispronounced word: add diacritics on the wrong syllable only, or respell; then regenerate.
- `stability` 0.5 default; 0.35 for very expressive storytelling (set in story.json). No `style` /
  `speed` on v4 — pace comes from the writing and the reel's `tempo`.
- QC is automatic: best of up to 3 takes per beat by speech-to-text, forced alignment for word timing.

## 6. Rhythm — vary it
- `tempo` (story_voice `--tempo`): 1.1 calm/minimal … 1.2 default (approved) … 1.25 high energy.
- Beat length varies on purpose: quick 1–2 s punches next to 4–5 s explanations; one short `pause`
  before a reveal is allowed.
- `music_prompt` follows the mood (tense pulsing synth, warm acoustic, playful plucks, cinematic
  strings…); no vocals.

## 7. Script (story.json → beats)
- 18–34 beats. `text` is exactly what is said and shown, with markup: `[tag]` (spoken delivery,
  hidden), `*keyword*` / `*several words*` (big accent words, 1–2 per beat), `|` (line break),
  `{shown|spoken}`.
- Conversational Persian written for the ear; short sentences; one idea per beat.
- Only verified facts from `dossier.json`; quotes only when confirmed; attribute claims.

## 8. Visuals per beat

### 8.0 Engines, style rotation and motion craft (user rules 2026-10-22 — read before designing any reel)
The user rejected the collage look ("cut-outs and icons that just slide around look childish"). Reference:
the viral @ensan.besham reel (2.3M views) — glowing line-art explainers. **No fixed style (user rule 2026-10-22): every reel gets
its own style.** Four engines: **`kinetic.html`** (agency kinetic type + UI, below), **`flow.html`** (one morphing actor of light, below) and **`line.html`** (glowing line-art explainer, below) and **`story.html`** (looks
in §4: paper-ember, mono-press, acid-pop, neon-night, maxi-pop, soft-ui …). Choose engine + look per story;
never the same engine *and* look two reels in a row; across a week use at least three of the four engines and at least 4 looks.
The motion craft below (smooth expo easing, continuous movement, things that visibly happen, lead visual
filling the frame, no empty or frozen frames, no toy-like bouncing) applies to **every** engine and look.
- **One continuous canvas.** Each beat is a station on a big world; the camera travels to the next
  station (pull back → diagonal move with motion blur → push in) along a glowing rail that draws itself.
  No hard slide changes, no empty frames, no element "popping" with bounce easing.
- **Things are drawn, not pasted.** Line icons (Lucide, 1,500+) and line art draw on stroke by stroke with
  a soft glow; connectors carry travelling pulses; key words in a quoted sentence get a hand-drawn circle
  and a numbered badge; numbers roll like an odometer; gauges, bars and charts fill with glowing heads;
  a person grid lights one figure.
- **Easing:** expo/power3 out for arrivals, expo in-out for camera moves; never back/elastic. Readable
  landing → fast exit. A slow 3–4% push on every hold; dust particles and film grain for depth.
- **Hierarchy:** one lead visual filling 60–85% of the station, one small headline (`head`, with
  `*accent*`), small karaoke captions at the bottom + section dots. 1–2 reading targets at a time.
- **Colour:** dark base (`motion.theme.bg`), white glowing lines, one accent (`acc`) for what matters;
  or a palette (`accents: [...]`, one per station, with drifting colour glows) for a maximalist reel.
- Real people / products as line art: a real photo → `python3 news-reel/lineart.py photo.jpg el/x.svg`
  (plain background works best; crop to the subject first) → `lineart` visual. Credit the photo.

`story.json` for line.html: `{motion: {theme: {bg, line, acc, accents?}}, beats: [{id, text, head?, visual}], end_text}`.
**kinetic.html — agency kinetic typography + UI** (user references 2026-10-22: @arpit_clipsyk Dbc1KrKh2wV,
@olafmotion DbSpdwSsdnF, @mgulifes DM-pomvI6AM). Light gradient pages and dark pages alternate (`bg: "dark"`).
`story.json`: `{kinetic: {theme: {light, dark, ink, acc}}, beats: [{id, text, bg?, visual}], end_text}`; the
`text` may contain `[icon:lucide-name]` tokens, shown as icon tiles inside the typed line and not spoken.
Types: `type` (the narration typed with a cursor, icons inside the words, `*accent*` marker — the signature
move; use it for every 2nd–3rd beat), `whip` (`word`: one giant word that flies in with motion blur), `pills`
(`items`: glass pills sliding, a search lens turning each on — lists, pipelines), `kpi` (`label`, `from`,
`to`, `prefix`, `suffix`, `decimals`, `delta`, `points`: a dark card whose number climbs while its chart draws),
`stack` (`images`, `head`: real photos / screenshots as tilted 3D layers), `route` (`cards[{img, title, sub,
tag}]`: photo cards joined by a route line that draws), `zoom` (`icon`, `head`: an icon tile that zooms through
the camera into the next beat — a match cut). Non-`type` beats show the narration as a caption that lights up
word by word. Vary `theme` per reel (yellow/black is the reference; also lime/ink, coral/navy, ice/violet).

**flow.html — one actor that never cuts** (user references 2026-10-22: @louis_rlee DeKOzQRouIf, motion by
Claude in code; @topintownagency Dd8tGxYugym). A single point of light grows into each beat's form, lives
through the beat, and collapses back to a point that becomes the next form; bloom, lens streak, particle
trails, glossy gradients, an iris that opens a light page for one beat, one line of text under the actor
(the narration, words blurring in as spoken, `*accent*` in a gradient serif). Use it for stories with a
clear flow or a few big ideas; 8–16 beats. `story.json`: `{flow: {theme: {bg, ink, a1, a2, light}, top: "small
label"}, beats: [{id, text, bg?: "light", visual: {form, …}}], end_text}`. Forms: `spark` (falls, ripples,
flares — a strong opener), `ring` (`n` particles orbiting, optional `count` that counts up + `suffix`),
`flower` (the ring bending into petals), `star`, `prompt` (glass bar with a glowing gradient border typing
`prompt` — for agents / chatbots), `card` (glossy gradient card, `title`, `sub`, swings in, folds out),
`arcs` (concentric half-rings with runners; `labels`), `chain` (`steps` pills on springy ropes — processes),
`orbit` (hub + orbiting `chips` over a neon waveform — ecosystems, teams), `infinity` (loops, cycles),
`blob` (liquid blobs merging and splitting — flow, fluid, blending), `wave`. Vary the palette per reel
(`a1`/`a2`: warm amber/rose, cyan/violet, lime/teal, gold/white…); never two flow reels with the same colours.

Line visuals (all coordinates in a 1080-wide station, y 0–1350):
`icons` (`items[{icon, label, sub, acc}]`, `focus`), `flow` (`hub{icon,label}`, `nodes[{icon,label}]`, `side`
[left, right] arc labels, `dir`), `quote` (`text` with `*words*` to circle, `source`, `at[]` circle times),
`counter` (`to`, `prefix`, `suffix`, `label`, `ring` %), `bars` (`rows[{label, icon, value 0–100, text, acc}]`),
`people` (`n`, `cols`, `icon`, `focus`, `focus_at`, `light`, `label`), `compare` (`left{title}`, `right{title}`,
`rows[{label, l, r}]` true/false), `chart` (`points[]`, `value`, `label`), `timeline` (`events[{date,label}]`),
`word` (`text`, `sub`, `size`, `font`), `ui` (`title`, `rows[{icon,label,value,acc}]`), `lineart` (`src` svg,
`w`, `h`, `label`, `sub`, `draw` seconds), `none`. Icon names: lucide.dev (e.g. `brain-circuit`, `shirt`,
`scissors`, `gem`, `camera`, `landmark`, `server`, `shield-alert`, `user-round`, `trending-up`).
Every beat must visibly *produce* something (a line drawn, a number landing, a word circled).

### 8.1 story.html visuals (collage engine — secondary)
Types: `object` (1–3 cut-outs; `anim` pop/slide, `float`, `stamp`, `marks`), `person` (real photo,
b/w card, name + role), `quote` (card + source, optional round photo), `icon_grid`, `network`,
`counter`, `timeline`, `ui` (app card), `chart`, `split` (A «یا» B), `none`;
soft-ui types (work in any look): `lineup` (`items[{name, el | mark+color, bg, fg, sub}]`, `compact_at`,
`focus`), `prompt` (agent box that types `text`, `chips[{label, icon}]` pop with green dots, `status` pill
+ `count` counter), `tasks` (`cards[{title, sub, big | icon, progress}]` + `tags` lighting up in turn),
`roles` (hub + `roles[{label, color, sub}]` orbs joined by lines), `stack` (summary rows, `highlight` the
last), `table` (`cols` like lineup items, `rows[{label, cells}]`, `win` = column to colour, `row_at` = seconds
when each row lights up — sync it to the narration); `huge: true` for one giant
word; `iris: true` for a circle wipe. Every beat changes something on screen.

### 8.2 Elements and image prompts (user rule 2026-10-23)
**Realistic elements, not simple icons.** We generate with the best image models, so every object in a
motion graphic is a realistic, stylish, professional element: a real-looking phone with a glowing UI,
a brushed-metal server, a frosted-glass chat bubble, a silk dress on a mannequin, a gold coin stack. Plain
Lucide icons are only for small helpers (bullets, a tile inside a typed line next to text, UI chrome), never
the lead visual of a beat. In kinetic.html and atelier.html, `[icon:el.<id>]` puts the realistic cut-out
`el/<id>.png` inside the typed line instead of an icon; `zoom`, `route`, `stack` and `scene` take real
images. In line.html the lead visual is `lineart` traced from a real or generated photo, not an icon.

**Write every image prompt with prompt engineering** (skill `ai-photo-prompt-guide`). The formula is
subject + camera look + environment + light + materials + emotion + composition. Each prompt sets:
1. **Subject:** the exact object or scene, and the one detail that ties it to the beat.
2. **Aspect ratio:** 9:16 for scenes; the cell for sheets.
3. **Camera:** medium format or full-frame. **Lens:** 100mm macro for objects, 35mm for sets, 85mm for people.
4. **F-stop:** f/8 for objects (everything sharp), f/2.8 for sets (depth).
5. **Angle:** three-quarter or eye level; low angle for power.
6. **Lighting:** the most important choice, set as key + fill + rim: direction, quality and colour.
7. **Textures:** 2–4 concrete materials (brushed aluminium, frosted glass, satin, leather, ceramic).
8. **Background:** transparent for sheets; for sets, the place, the time of day and the clutter level.
9. **Composition:** where the eye goes; negative space for our type.
10. **Colour mood:** the reel's palette.
11. **Realism notes:** "premium advertising quality" and "physically accurate materials".
12. **Exclusions:** "no text, no letters, no logos, no watermark, not cartoon, not clipart, not flat icon".

Concrete words beat adjectives: write "soft 45° softbox key from the left, cyan rim light", not
"beautiful lighting". `elements.json → style` carries the shared camera, light, material and colour
language for the whole sheet. Each item's `desc` names its own object, material and angle, e.g. «matte
black smartphone, three-quarter view, screen glowing with a soft blue chat interface without readable
text, brushed aluminium edge catching a cyan rim light». Read every sheet. Reject and regenerate any that
looks like clipart or plastic toys, or has warped shapes or fake letters.

**Elements: at most 3 generated collage sheets (≤ 9 items each), cut out automatically** —
`python3 news-reel/sprite_sheet.py --dir work/story` with `elements.json`
(`style` + `sheets[{name, items[{id, desc}], refs?}]`). Never one image call per element. Read the
`el/_sheet-*.jpg` previews; regenerate a bad sheet at most twice. Real products: pass reference photos
as `refs` (RUNBOOK §1.5.1). Real people: real photos only (Wikimedia Commons first, fetched through
Drive), never a generated likeness; credit in the caption.

## 9. Commands
```
bash news-reel/setup.sh
python3 news-reel/sprite_sheet.py --dir work/story
node news-reel/story_voice.mjs  --dir=work/story [--tempo=1.2]        # exit 3 too long, 4 unclear speech
node news-reel/reel_render.mjs  --dir=work/story --page=line.html --mode=check    # Read out/sheet*.jpg (story.html for collage)
node news-reel/reel_render.mjs  --dir=work/story --page=line.html --mode=video    # background, timeout ≥ 60 min
python3 news-reel/reel_assemble.py --dir work/story                    # reel.mp4 + cover.jpg + reel.json
python3 news-reel/story_cut.py     --dir work/story                    # story.mp4 (≤ 60 s) for the Story share
```
`check` prints ISSUES when on-screen words and spoken words do not line up — fix before rendering.
