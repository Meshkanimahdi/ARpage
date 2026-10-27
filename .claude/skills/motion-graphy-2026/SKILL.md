---
name: motion-graphy-2026
description: "Catalog of 85 distinct, tested, approved motion-graphics prompts from Prompt Motion: product/UI films, explainers, kinetic type, 3D, showreels, editorial, music-driven, hand-drawn, story, pixel and stop-motion. Each has a title, use, mood, audience, trend fit and the full verbatim prompt. Use it BEFORE designing any reel, story animation, promo or motion graphic, especially for meshkani.pro. Pick the style that fits the news, keep the prompt's structure exactly, and change only timing, size/aspect ratio, duration and the topic-specific slots. Triggers: reel, Reels, motion graphics, موشن گرافیک, ریلز, animation, promo video, explainer video, product sting, showreel, kinetic typography."
---

# motion-graphy-2026: tested motion-graphics prompts

Mahdi's rule (2026-10-23): before producing **any** reel, first consult this skill and choose, for the news and
its content, the best motion-graphics style from this catalog. The prompts were tested and approved; professional
samples were made with them. **Never change the core structure of a prompt.**

## Files
- `references/index.md`: all 85 prompts grouped by visual category, one line each (id, title, brief, mood,
  trend fit, whether it has an `<inputs>` block). Read this first.
- `references/prompts/<id>.md`: one prompt per file with its notes (use, style, mood, audience, gender target,
  trend fit, creator, source link) and the **verbatim** prompt.
- `references/catalog.json`: the same metadata as data, for filtering and for rotation checks.
- `references/adaptation.md`: a worked example showing how prompt `089-frame-by-frame-launch-video` became
  the vertical Persian news reel `news-reel/glass.html`, and which edits counted as allowed.

## Workflow (every reel)
1. **Read the story first.** Use the verified dossier: topic, sector, key facts (`allowed_claims`), emotion,
   audience, and whether there is a real product UI, a person, data, a place or a process to show.
2. **Read what performs.** Read `_automation/insights.json` (the daily ANALYTICS phase, RUNBOOK §6), which
   lists the categories, prompts, topics and hooks that earned the best reach, watch time and saves.
3. **Shortlist 3 prompts.** Use the mapping table below to pick 1–2 categories. In `index.md`, pick 3
   candidates. Open each `prompts/<id>.md` and read the full prompt.
4. **Choose one** for: fit with the story (does its structure have a place for every key fact?), the
   insights, and rotation (below). Write one line on why it won and why the other two lost.
5. **Adapt, then save a copy.** Copy the prompt verbatim into `<work dir>/motion_prompt.md` and make only
   the allowed edits (next section). Under it, list every edit you made (`- changed: … → …`). Anything not
   in that list must be byte-identical to the catalog.
6. **Build exactly that prompt.**
   - Implement it as an engine page `news-reel/pm/<id>.html` that follows the page contract (`window.ready`,
     `window.seek(t)` as a pure function of time, `START = 0`, `DURATION`, `SCENES`, `ISSUES`; data from
     `story.json` + `timeline.json`). See `news-reel/glass.html`.
   - If `news-reel/pm/<id>.html` already exists (list: `news-reel/pm/README.md`; `089` is `news-reel/glass.html`),
     reuse it with new data. After building a new page, add it to that list.
   - Follow the prompt's own `<build>`, `<gotchas>` and `<start>` steps. Where `<start>` says "show me stills
     first", render those stills and review them yourself (Read them). The publisher never waits for
     approval. Fix what is cluttered, off-beat, overlapping or hard to read, then render the film.
7. **Record it.**
   - Slot file: `motion_prompt: {id, title, link}`.
   - Sheet column "Motion Graphics Prompt": the adapted prompt.
   - Automation Log: the id plus the one-line reason.

## What you may change (nothing else)
1. **Timing.** Beat times, frame ranges and hold lengths may follow the narration. Stretch only where the
   prompt already has a drift or hold; entries and exits keep their designed speed. Keep the prompt's BPM;
   line its hard cuts and accents up with the music and the narration.
2. **Size and aspect ratio.** Render vertical **1080x1920 (9:16)** for Reels and Stories. Re-lay coordinates
   for the tall frame so the lead visual fills 60–85% of it. Keep Instagram's UI out of the text: no text in
   the top 230 px or the bottom 280 px.
3. **Duration.** Use the standard lengths:
   - 09:00 news reel: ≈60 s.
   - 15:00 story reel: 60–90 s.
   - Story cut: ≤60 s.

   Extend by giving each section of the prompt's structure more time, or by repeating its middle pattern
   (one extra "moment" per key fact). Never by inventing new kinds of sections.
4. **Topic-specific slots.** Everything in `<inputs>` and every product-specific noun:
   - product or company name, logo/mark, the line typed into a prompt box, page titles and copy;
   - feature or card names, screenshots, data points, the through-line object, the music track;
   - palette, when the prompt says "its own / brand colors". In that case use the news subject's real
     palette, or the page theme.

   Fill them from the verified news only. A fixed palette written in the prompt stays as written.
5. **Page standards.** These are required, not structural:
   - On-screen text is Persian (RTL). Latin names stay Latin. Persian text uses Vazirmatn or a fitting Persian
     face; Latin text keeps the prompt's typeface.
   - Our narration (ElevenLabs eleven_v4 per STORY_SPEC §5) and a karaoke caption are added on top.
   - The music bed may come from ElevenLabs music at the prompt's BPM instead of a track coded in Web Audio.
     The prompt's sound cues (kick per beat, hits on cuts, riser, clicks, ticks) are kept as SFX through
     `SCENES[].sfx`.
   - The render runs through `news-reel/reel_render.mjs` at 30 fps.
   - The `<start>` questions are answered from the dossier; nobody is asked.

## Priority rule: full-frame shots for news reels (user rule 2026-10-24, after REEL-007)
- A news story never uses a one-diagram/zoom-map prompt (e.g. 168, 194): they left the frame mostly empty
  with tiny cut-outs. Those prompts are only for list or how-to topics.
- Pick a shot-based prompt and keep its structure. Every frame is designed and filled with exactly what the
  narration says (no word-pun objects), but not every reel is a full-screen photo slideshow: follow the
  prompt's own look (typography, UI, editorial, 3D, framed photos…).
- A different prompt for every reel: never one used in the last 10 reels; rotate categories.
- Plan first (`production_plan.md`: shots, how each is made cheapest-first, budget ≤ $0.25), and make
  generated pictures as storyboard sheets of 12 panels (`gen_image.py --kind board` + `news-reel/storyboard_cut.py`),
  never one image call per shot (RUNBOOK §4.0 rules 7–8).
- New picture or camera change every 1.5–3 s, no still over 1.5 s, hook in the first 2 s, 40–55 s.
- Gate: `python3 news-reel/reel_qa.py <reel.mp4>` must pass, then read its contact sheet (RUNBOOK §4.0).

## Priority rule: realistic elements and real logos (user rule 2026-10-23)
This rule overrides a prompt's style lines. Every prompt's structure, shots, timing logic and motion rules
stay as they are, but its *visual vocabulary* yields to realism:
- Objects in a scene are realistic, stylish, premium elements: real photos, or prompt-engineered
  photoreal cut-outs (STORY_SPEC §8.2). This applies even when the prompt says "flat", "line icons",
  "no stock icons" or "clean diagrams". A diagram can still be a diagram, but its nodes, products and
  places are realistic cut-outs, not drawn pictograms.
- Real icons and **the real logo** of every company, startup, product, app or lab the story names are
  mandatory, both in the reel and on the cover. Sources and handling: RUNBOOK §4.3 step 2. Never generate
  or redraw a logo.
- If a prompt bans something this rule requires (for example "no logos" or "no photos"), this rule wins.
  Note it in `motion_prompt.md` as `- overridden by user rule (realism/logo): …`.

## What you must never change
The order and role of the sections and shots, the story beats, the through-line or continuity idea, the
transition grammar (match cuts, morphs, whips, blur dissolves), the camera language, the easing and motion
rules, the type and colour rules, the `Banned:` lists, the `<gotchas>`, and the build discipline (pure
`seek(t)`, no CSS animations, timers or `Math.random`).

If a prompt cannot hold the story without breaking its structure, pick another prompt. Do not bend this one.

## Choosing a category for a news story
| news is about | first choice | also good |
|---|---|---|
| a product, app, model or feature launch; a pricing or agent platform | UI | TYPE, REEL |
| research, a benchmark, policy, a timeline, "how it works", numbers | EXPL | GEO, EDIT |
| a statement, quote, debate or warning by a person | TYPE | EDIT |
| chips, data centres, robots, cars, space, hardware | 3D | ANIME, GEO |
| culture, fashion, art, design, lifestyle | EDIT | HAND, STOP, REEL |
| music, audio, voice or video generation | MUSIC | REEL |
| games, nostalgia, internet culture | PIXEL | ANIME |
| a human story, a company story, a cautionary tale | STORY | HAND |
| a broad "state of AI" or weekly roundup | REEL | GEO, TYPE |
| cooking, recipe or a step-by-step process | STEP | EXPL |
| no clear fit | TOPIC | the best match by mood |

## Rotation
- Never use the same prompt twice within 14 days (check `catalog.json` against the slot files and the sheet).
- **Deduplicated (2026-10-27, Mahdi):** the catalog had 230 entries but only 85 different prompts; the 145 copies
  (same text, only the brand/product/duration changed) were removed. `references/duplicates.json` maps a removed id
  to the kept one, and `news-reel/pm/families.json` makes the gate treat them as the same prompt.
- **meshkani.pro reels pick from the rotation list** in `meshkani-pro/RUNBOOK.md` §4.0 rule 9, data-rich prompts first
  (181, 155, 207, 112, 117, 120, 225, 095, 219, 228, 032, 089). Every reel must be professional motion graphics with
  numbers, charts, rebuilt UI, glow and layered elements, never a photo slideshow (rule 2b). Walmart/089 is the
  quality bar, not a template to copy.
- Never use the same category in two reels in a row. Across a week, use at least 4 categories.
- Reusing an already-built `news-reel/pm/<id>.html` saves time and counts as using that prompt.
- Build time: give the 09:00 reel (prepared from 21:45) any prompt. For the 15:00 reel (prepared from
  12:45), prefer a prompt that is already built, or a simple one.
- Insights may tilt the choice toward what performs. Keep 1 in 4 reels as an exploration pick (an untried
  category), so the page keeps learning.

## Honesty
- Rebuild a UI only from real screenshots or official material.
- Otherwise, build a clearly conceptual interface: no fake features, no invented numbers, no copied logos.
- Every on-screen claim comes from `allowed_claims`.
- Images follow STORY_SPEC §8.2: realistic, premium, prompt-engineered, with no text or logos baked in.
