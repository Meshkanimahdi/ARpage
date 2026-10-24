# Built motion-graphics prompts (skill motion-graphy-2026)

One engine page per catalog prompt, so later reels can reuse it with new data (`story.json` + `timeline.json`).
Page contract: see `news-reel/glass.html` (`window.ready`, pure `window.seek(t)`, `START = 0`, `DURATION`, `SCENES`
with optional `sfx`, `ISSUES`; beats carry `shot`). Add one line per new page and commit it.

| prompt id | title | page | built | used in |
|---|---|---|---|---|
| `089-frame-by-frame-launch-video` | Frame by Frame launch video (Apple-keynote glass sting) | `news-reel/glass.html` | 2026-10-23 | Walmart Agent Gateway demo (not published); REEL-006 smart TVs + Claude Code (2026-10-24 09:00) — added real-logo slot (`glass.logo`, `page_logos`, `card_logos`, `col_icons`) |
| `168-prompting-mistakes-video-tutorial` | Prompting mistakes video tutorial (one-diagram article explainer). **List/how-to topics only, never a news story (RUNBOOK §4.0, after REEL-007).** | `news-reel/pm/168-prompting-mistakes-video-tutorial.html` | 2026-10-23 | REEL-005 rebuild test (MAI-DxO, Science), original audio reused; REEL-007 MIT island-play agents (2026-10-24 15:00) — items `pic`/`logo`/`tag`/`arrow`/`check`/`debate` with real cut-outs, cams offset so content sits above the subtitle |
| `211-the-last-light-animated-short` | The Last Light animated short (shot-list story film) | `news-reel/pm/211-the-last-light-animated-short.html` | 2026-10-24 | REEL-007 rebuild under RUNBOOK §4.0: 29 full-bleed shots from 21 generated plates (`raw/<shot>.png`, one character kept with `--ref`), cut on action with directional whip blur, spring settle, per-beat grade, real logo chips, quote bubble, counter + strike, end card. Data: `beats[].shots [[word, plate, variant]]`, `moves{plate[.variant]: hook|in|out|left|right|up|down}`, `chips`, `bubble`, `counter`, `void`, `grade`, `end_shot`, `end_text`, `end_sub`. The page flags shots over 3.2 s. |
