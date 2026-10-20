# Daily reel — spec format and authoring rules

The daily reel (≈60 s, 1080×1920) is rendered from one work dir, e.g. `work/reel/`:

```
work/reel/spec.json        what to show and say (you write it)
work/reel/A/ … B/          the source images of news 1 and news 2 (the six published finals each,
                           plus at most 2 clean plates per news)
work/reel/timeline.json    written by reel_voice.mjs
work/reel/voice/           narration takes, qc.json, trim/<line>.wav
work/reel/out/             stills, contact sheets, news.mp4, scenes.json, mix.wav
work/reel/reel.mp4         final (logo intro + reel + mix), cover.jpg, reel.json (QC numbers)
```

Commands (repo root):

```
bash news-reel/setup.sh                                          # once per session: npm deps + font/playwright link
node news-reel/reel_voice.mjs   --dir=work/reel                  # TTS + STT check + tempo fit + timeline
node news-reel/reel_render.mjs  --dir=work/reel --mode=check     # one still per scene -> out/sheet1..3.jpg
node news-reel/reel_render.mjs  --dir=work/reel --mode=video     # out/news.mp4 (~12-15 min; run in background)
python3 news-reel/reel_assemble.py --dir work/reel                # reel.mp4 + cover.jpg + reel.json
```

Exit codes: voice 3 = script too long (shorten lines), 4 = speech-to-text score < 0.8 on a line
(respell or rephrase it); render 5 = page error / missing file; assemble 6 = duration or loudness out of range.

## Structure (fixed)

`logo intro (0–4.2 s) → news 1 (~25 s) → divider «خبر دوم» (~1.1 s) → news 2 (~25 s) → end card with the
closing line` ≤ 60.5 s. Each news has its own narrator (§Voices). Subtitles, the two-part progress bar, the
`n/2 · <tag>` chip, particles, light streaks, flashes and the divider/end cards are automatic.

## spec.json

```json
{
 "date": "2026-10-21", "posts": ["POST-014", "POST-015"],
 "end_line": "[warm] جزئیات کامل هر دو خبر، توی پست‌های دیروز.",
 "end_text": "جزئیات کامل هر دو خبر در پست‌های دیروز",
 "music_prompt": "<English music brief: mood fitting both news, tempo, instruments, no vocals, under narration>",
 "news": [
  {"id": "POST-014", "tag": "<field in Persian>", "voice": "<voice id>", "voice_name": "Niloofar (female)",
   "lines": [{"id": "A1", "text": "..."}, {"id": "A2", "text": "...", "pause": 0.2}],
   "scenes": [{"type": "hook", "at": "A1", ...}, {"type": "duo", "at": "A2", ...}]},
  {"id": "POST-015", ... line ids B1.., scenes ...}
 ]
}
```

- Line ids: `A1…` for news 1, `B1…` for news 2. Every scene starts at the start of its `at` line
  (+ optional `offset` seconds); it lasts until the next scene. The first scene of news 1 starts right
  after the logo.
- Images: `{"src": "A/story-2.jpg", "box": [x, y, w, h], "shape": "circle", "fit": "cover"}`. `box` is a
  crop in source pixels (the slides are 1080×1350, the stories 1080×1920). Paths are relative to the
  work dir; `/news-reel/...` reaches the shared library. Transparent PNG cut-outs: `"fit": "contain",
  "alpha": true`.
- Inline text markup: `*word*` orange neon, `_word_` cyan neon, `[[Latin]]` Latin font. Persian digits.

### Scene types

| type | use for | fields |
|---|---|---|
| `hook` | first scene of each news: full-bleed image, HUD brackets around the subject, 2 chips, 3–4 kinetic words | `plate` (image), `focus` [x,y,w,h] in frame px (1080×1920), `chips` [≤2], `words` [str or {t, hl/cy}] |
| `duo` | who with whom / who and where | `a`, `b`: {text, latin, bar:[colours]}, `chip` (date · place), `card` {kicker, title, sign:false} |
| `steps` | a process or 2–4 parts | `title`, `accent`, `sub`, `items` [{img, label}] (round crops), `pill` {text, strike} |
| `grid` | 2–4 named things (companies, products, places) | `big` (a number), `title`, `sub`, `tiles` [{img, fa, en}], `focus` [fractions when each tile is mentioned] |
| `stat` | one number, date or an unknown | `glyph` {src(+box) or text}, `label`, `value`, `count` {from,to,prefix,suffix}, `flicker`, `stamp` |
| `quote` | a statement by a named person/organisation | `plate`, `glow` [x%,y%], `kicker`, `quote`, `by` |
| `points` | 2–3 takeaways / limits | `title`, `items` [text] |
| `frame` | show one image as a floating 3D card | `img` (with box), `caption` |

Per news: 4–6 scenes, the first is `hook`, no type more than twice, and news 2 should not repeat news 1's
sequence of types. A scene shows what the line says, but its on-screen words are short labels, not the
spoken sentence (the subtitles carry the sentence).

## Writing the narration (user rules)

- Fresh, conversational Persian written for the ear. **Do not read the text that is on the images**;
  say the same facts in new words. Hook first, then what happened, who, the key detail, then the
  limit or what it means. 4–6 lines, ≤ ~25 s of speech per news (the tool fails above tempo 1.25).
- Only facts from the post's dossier `allowed_claims` / caption. Keep company claims attributed.
- Emotion tags at the start of a line are allowed: `[excited]`, `[curious]`, `[thoughtful]`, `[warm]`.
- Latin names: write them the way they are said in Persian (اسپیس‌ایکس, انویدیا), so the voice and the
  speech-to-text check agree.

## Voices

Two different narrators per reel: one female, one male (`config.json → reel.voices`), each chosen to fit
its news (see `VOICES.md`). The closing line is read by news 2's narrator. Alternate the order every
day: if yesterday's reel opened with a female voice, today's opens with a male one (read the previous
reel slot JSON → `voices`).

## Visuals

- Use only the published images of the two posts. Crop elements out of them (`box`), avoid crops that
  include the baked-in titles, page handle, numbers or the «تصویر مفهومی» label.
- If a news has no text-free area large enough for a `hook`/`quote` plate, make a clean plate from one of
  its stories: `python3 meshkani-pro/scripts/gen_image.py --kind story --prompt-file
  news-reel/plates/p/clean.txt --ref work/reel/A/story-1.jpg --out work/reel/A/story-1-clean.png`
  (≤ 2 per news, ~$0.055 each, cost goes into the reel slot JSON). No other image generation.
- After `--mode=check`, open every contact sheet with Read and fix: text outside the frame or overlapping,
  crops that show baked-in text, an element that does not match its line, faces/products distorted.
