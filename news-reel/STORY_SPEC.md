# Daily story reel — format (user decision, 2026-10-21)

Reference the user chose: @mgh.mobin reel «انسان‌ها، گاوهای آینده‌ان؟» (Harari + Musk, 69 s).
One reel a day at 09:00 Tehran: **one idea**, told as a short story, 60–70 s, one narrator,
**the on-screen text is exactly the narration, word by word**, in the reference's look. This replaces
the two-news reel (REEL_SPEC.md is legacy). The neon / particles / 3D rule does not apply to these reels.

## What the reel is about
- One strong idea about AI's real effect on people's life, work, money or society, carried by a known
  person, institution or study (an interview, talk, book, report, survey), ideally from the last 14
  days or tied to something current. Example: Hinton's "a good bet would be to be a plumber".
- Verified like news (RUNBOOK §1.3): who said it, where, when. Direct quotes only when the wording is
  confirmed by the primary source or consistent across reputable outlets; otherwise paraphrase and
  attribute. Never invent quotes, numbers or dates.
- Not a repeat of the last 14 reels (Reels tab), and not the same field two reels in a row.

## Script (story.json → beats)
- 18–26 beats, one short spoken sentence each (≈2–4 s). The beat `text` is spoken exactly as written:
  `*word*` or `*several words*` = big orange keyword (1–2 per beat), `|` = line break (not spoken).
- Arc: provocative hook (claim or metaphor) → who said it (name, credential) → the explanation with a
  concrete everyday image → "why?" turn → evidence/second voice → the takeaway → one question to the
  viewer → «جوابتو تو کامنت بنویس». Conversational Persian written for the ear; Latin names written as
  they are said (هینتون، اسپیس‌ایکس).
- `story_voice.mjs` fits the tempo (≤1.2) to land at 60–70 s; above 75 s it fails → shorten.

## Look (story.html)
- Two backgrounds that alternate: `paper` (warm off-white, big grey arc, small barcode) and `dark`
  (near-black, perspective grid floor, orange glow). One accent colour: orange #FF6A13.
- Words appear one by one at the moment they are spoken (blur → sharp). Keywords big orange.
- Every beat shows one visual. Types: `object` (1–3 cut-outs, `anim` pop/slide, `float`, optional
  `stamp` and `marks` ؟), `person` (real photo, black & white card, name + role), `quote` (dark card,
  quote + source, optional round photo), `icon_grid` (icons filling orange + %), `network` (AI node +
  satellites), `counter`, `timeline`, `ui` (dark app card), `chart`, `split` (A «یا» B), `none`, and
  `huge: true` for a single giant word («چرا؟»). `iris: true` = circle wipe into the beat.
- End card: logo + MESHKANI.PRO + the closing question (`end_text`).

## Elements: at most 3 generated sheets (user rule)
All objects come from **≤ 3 collage sheets, ≤ 9 items each**, generated once each and cut out
automatically — never one image call per element:
`python3 news-reel/sprite_sheet.py --dir work/story` reads `elements.json`
(`style` + `sheets[{name, items[{id, desc}], refs?}]`) → `el/<id>.png` (transparent, trimmed) and
`el/_sheet-<name>.jpg` previews (~$0.08 per sheet). Read the previews; a bad item → fix its `desc`
and regenerate only that sheet (`--sheets s2`). Physical real products: pass reference photos as `refs`
(RUNBOOK §1.5.1). Real people: use a real photo (Wikimedia Commons first; fetch through Drive), never a
generated likeness; credit in the caption.

## Commands
```
bash news-reel/setup.sh
python3 news-reel/sprite_sheet.py --dir work/story
node news-reel/story_voice.mjs  --dir=work/story
node news-reel/reel_render.mjs  --dir=work/story --page=story.html --mode=check   # Read out/sheet*.jpg
node news-reel/reel_render.mjs  --dir=work/story --page=story.html --mode=video   # background, ~15 min
python3 news-reel/reel_assemble.py --dir work/story                               # reel.mp4 + cover.jpg + reel.json
```
`check` prints ISSUES when a beat's on-screen words do not match the spoken words — fix before video.
