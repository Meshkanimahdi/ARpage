# Built motion-graphics prompts (skill motion-graphy-2026)

One engine page per catalog prompt, so later reels can reuse it with new data (`story.json` + `timeline.json`).
Page contract: see `news-reel/glass.html` (`window.ready`, pure `window.seek(t)`, `START = 0`, `DURATION`, `SCENES`
with optional `sfx`, `ISSUES`; beats carry `shot`). Add one line per new page and commit it.

| prompt id | title | page | built | used in |
|---|---|---|---|---|
| `089-frame-by-frame-launch-video` | Frame by Frame launch video (Apple-keynote glass sting) | `news-reel/glass.html` | 2026-10-23 | Walmart Agent Gateway demo (not published) |
| `168-prompting-mistakes-video-tutorial` | Prompting mistakes video tutorial (one-diagram article explainer) | `news-reel/pm/168-prompting-mistakes-video-tutorial.html` | 2026-10-23 | REEL-005 rebuild test (MAI-DxO, Science), original audio reused |
