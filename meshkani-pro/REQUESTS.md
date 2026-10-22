# One-off requests from the user (read first in every REEL_PREPARE / PREPARE run)

A request names a slot. For that slot it overrides the rotation and variety choices (angle, topic area,
look, shape) — never the safety, fact-checking, source, budget or publishing rules. Record in the slot
file `creative.request` which request you followed. Requests for past slots are ignored.

## Reel 2026-10-23 09:00 (prepared 2026-10-22 21:45, user request 2026-10-22)
- **Topic area:** the role of AI in fashion and style — design, collections, virtual try-on, AI models on
  the runway / in campaigns, trend forecasting, fashion brands' AI moves. Pick the strongest *verified*
  story trending in the last 72 h; if nothing big, widen to the last 14 days (still verified, dated in the
  caption). Angle: creative work (STORY_SPEC §1).
- **Look: maximalist colour + professional motion, mandatory** (updated 2026-10-22 18:30: the user now
  rejects collage cut-outs). Engine `line.html` (STORY_SPEC §8.0), `motion.theme = {bg: "#07060B",
  accents: ["#FF2E93", "#00E5FF", "#FFE14D", "#7CFF4F", "#B388FF"]}` — a different neon accent per station
  with drifting colour glows. Fashion visuals as glowing line art: real runway / campaign photos traced
  with `lineart.py` (credited), Lucide icons (`shirt`, `scissors`, `gem`, `camera`, `sparkles`, `ruler`,
  `shopping-bag`, `palette`), `counter` / `chart` / `compare` / `flow` for the numbers and the
  human-vs-AI tension. No sprite-sheet collage for this reel.
- Voice: energetic; a female voice fits if the story is about women's fashion (STORY_SPEC §5).
- Everything else as usual: v4 tags, word-level sync, 60–90 s, reel + Story share at 09:00.
