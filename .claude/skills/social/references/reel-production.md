# Reel production (story reels with motion graphics)

One story per reel that matters to the viewer's life, told with strong hooks for watch time; the on-screen
text follows the narration word by word. Voice, sound and casting: `voice-and-sound.md`. Gates:
`quality-gates.md`. Cover: `headlines-and-covers.md`.

## 1. Order of work (cheapest decisions first)
1. Topic + dossier (`topics-and-research.md`).
2. **Concept (text only) → concept gate.** Nothing is generated before it passes.
3. Motion style chosen from a catalog of distinct prompts; engine built from that prompt's own look.
4. Cast list → script with shot list → voice.
5. Cover (8 candidates) and stills of the first 2 s → **preflight gate**.
6. Full render → assembly (mix) → attention QA → story cut.
7. Independent critic → **final gate** (again at publish time on the exact files).

## 2. The concept (`concept.json`)
- story: summary, source, date, field, `life`, `life_impact`
- 3+ headlines with the chosen one; the first spoken line contains it
- hook: frame 0 (real photo/video of what, how big), motion (push-in, whip, slam), on-screen line, optional
  number/result card
- cover: subject (real face/product/place), real vs generated, kicker, sub, logo, 4 headline variants
- motion: catalog prompt id, category, ≥ 6 scenes, each with ≥ 4 animated layers
- cast: every character who speaks or is shown (gender, age, role, voice)
- length: 30–150 s, chosen by topic (quick hit 35–50 s, checklist/explainer 60–90 s, data story 90–120 s)
- series block when it is a series part (`series.md`)

## 3. Visual rules
1. **Shot list with the script:** every sentence (beat) has a `shot` saying what the viewer sees while it is
   spoken: the real person, product, place, logo or event. Never a pun on a word, never a decorative object.
2. **A designed, filled frame, always.** Main subject ≥ 40 % of the frame width; never an empty canvas with
   small cut-outs while the narrator talks; no text truncated; nothing cut by the edge unless full-bleed.
3. **Professional motion graphics, never a photo slideshow.** Every scene is a composition drawn in code with
   ≥ 4 animated layers from: numbers counting up and stat cards; charts that draw on (bar, line, donut,
   progress ring) with labels and a highlighted point; real UI rebuilt as vectors (cards, chat bubbles,
   dashboards) with a cursor or taps; light and depth (glow, light sweeps over glass, parallax, camera moves in
   depth); real logos on chips, icons, kinetic type, arrows, highlights. Photos are one layer inside a frame,
   at most 2 photo-led shots per reel. Ken Burns over generated plates is a failure.
4. **Rhythm and sync:** a new shot or clear camera change every 1.5–3 s; no still over 1.5 s (end card ≤ 2 s);
   every number, name or result on screen within 0.3 s of the word that says it (time it from word timings,
   not scene order); no empty frame between shots; cut on action. Average ≤ 4 s per shot, no hold > 2.5 s.
5. **Hook in 2 seconds:** from frame 0 a huge readable hook line (≥ 120 px, ≤ 2 lines, inside the safe area)
   over a bright subject ≥ 60 % of the frame, already moving. Banned in 0–2 s: an illustrated opening, a dark
   tight crop, small UI text, an empty or transition frame, a logo alone, a slow fade, a greeting.
6. **Watch-time craft:** open loop in the first 5 s paid off near the end; a re-hook about every 15 s ("but
   here's the real story"); pattern change every 2–4 s; end on the payoff + one easy question for comments
   (or the series dilemma) + the share ask. Never promise what the reel does not deliver.
7. **Clear beats fancy** for life topics: readability of the message and the checklist wins over motion
   complexity.

## 4. Motion style variety (hard rules)
- Choose from a catalog of distinct, tested motion prompts (deduplicate the catalog: many "different" prompts
  are renamed twins; map each copy to its kept prompt so a family is blocked as one).
- **No prompt family and no engine from the last 10 reels**; the category (UI, kinetic type, editorial, 3D,
  story, explainer, music-driven…) differs from the previous reel.
- **Each prompt gets its own engine built from its own text**; never rename a copy of another engine. A gate
  compares code similarity with recent engines (> 60 % the same = fail).
- Keep a ranked rotation list of the most dynamic prompts (data-rich terminals, product films with
  dashboards, punchy promos, morphing UI, scale/big-number pieces, beat-cut edits) and take the next unused
  one that fits the story. Character/story prompts only for character stories.
- A one-diagram/zoom-map prompt is for how-to topics, never for a news story.
- Write the script to fit the prompt's structure (one beat per section); a short prompt is stretched by giving
  each beat its own section, not by repeating sections.
- A newly built engine is committed so later reels can reuse it after its cooldown.

## 5. Images for reels
- Generated pictures come from storyboard boards (up to 12 vertical panels in one 3840×2160 image, one prompt
  listing the panels in reading order, same world/light/character, a `--ref` for a recurring character), cut
  at the gutters. Regenerate a whole board at most once; replace a bad panel by reusing another.
- Prompts follow a photography checklist: subject, camera, lens and f-stop, angle, key/fill/rim light, 2–4
  materials, background, composition, colour mood, exclusions. Realistic and premium, never clipart.
- Physical products, places and public people must look like the real thing: find 3–6 real reference photos,
  describe the real look, pass 1–2 refs to every call, and check side by side before use. A look-alike is a
  failure.
- A fresh cover background for every reel; never reuse an earlier reel's plate.

## 6. Render, assemble, check
- Render stills first (cover, t = 0, 0.5, 1, 1.9 s, and one still per scene) → preflight.
- Full render (allow ≥ 60 min), then assemble: H.264 1080×1920 30 fps + AAC, the planned length, −15.5…−12
  LUFS (target −14), true peak ≤ −1 dBFS.
- **Attention QA** on the MP4: empty-screen share, holds, average shot length, hook motion, length; read a
  contact sheet (1 frame per second) against the narration for cropped elements and mismatches.
- Story share: cut the reel to ≤ 60 s at a sentence boundary + the end card.
- Caption: hook line (same angle as the cover) · 2–4 short sentences with attribution · the question or the
  dilemma · source and date · photo credit if a real photo is used · 4–6 hashtags · no URLs in the body.

## 7. Publishing a reel
Identity check → publish-time gate on the exact files → wait for the slot → create container (video, cover,
caption, share to feed) → poll until `FINISHED` (≤ 10 min) → publish → verify (type, username, caption) →
share the story cut → refresh the performance tab → unshare files. A failed story never re-publishes the
reel. Large files: re-encode (≈ 8–10 Mbps) if the container errors on size.
