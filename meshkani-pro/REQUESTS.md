# One-off requests from the user (read first in every REEL_PREPARE / PREPARE run)

A request names a slot. For that slot it overrides the rotation and variety choices (angle, topic area,
look, shape) — never the safety, fact-checking, source, budget or publishing rules. Record in the slot
file `creative.request` which request you followed. Requests for past slots are ignored.

## Reel 2026-10-23 09:00 (prepared 2026-10-22 21:45, user request 2026-10-22)
- **Topic area:** the role of AI in fashion and style, told so it appeals to women — design and
  collections, virtual try-on and AI stylists, AI models in campaigns / on the runway, trend forecasting,
  fashion brands' AI moves. Pick the strongest *verified* story trending in the last 72 h; if nothing big,
  widen to the last 14 days (still verified, dated in the caption). Angle: creative work (STORY_SPEC §1).
- **Look: `maxi-photo`, mandatory** (from the user's reference 2026-10-22: a photoreal maximalist creative
  studio — posters, disco ball, pink balloon dog, plants, leopard / checker prints, neon heart — with the
  headline on a poster inside the scene and the caption in a frosted-glass pill). Engine `story.html`,
  `theme.preset = "maxi-photo"`, every beat `visual.type = "scene"` (STORY_SPEC §4 maxi-photo). 4–7 scene
  images, each a different maximalist fashion set that fits its beats: designer studio with mannequin and
  fabric rolls, mirrored dressing room, runway backstage with racks of sequinned gowns, boutique with a
  virtual-try-on mirror screen, mood-board wall, a laptop / tablet showing colourful AI pattern designs;
  2–3 beats per image with the camera travelling between details. Poster headlines on beats 1, the
  turning point and the ending. Approved test scene: `news-reel/assets/maxi-studio-1.png` (blank poster box [331, 284, 443, 580]; may be
  reused for the hook). No flat stickers / sunbursts / checkerboard shapes, no sprite-sheet collage.
- **Voice: female**, warm and energetic (STORY_SPEC §5 table), v4 tags.
- Everything else as usual: word-level sync, 60–90 s, reel + Story share at 09:00.
