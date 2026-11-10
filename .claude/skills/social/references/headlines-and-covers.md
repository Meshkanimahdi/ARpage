# Headlines and covers

The cover (reel thumbnail, carousel slide 1) and its headline decide whether anyone watches. The same
headline system covers the first spoken line, the first caption line and topic-bank headlines.

## 1. What the data said
On one page, the winners named the viewer's job, money, family or a famous person, with tension, and never
led with the niche's buzzword ("AI"). The losers led with the buzzword, used jargon, were long, or had no
stake for the viewer. **Lesson: the niche angle lives inside the content, not on the cover.**

## 2. Rules
1. **Category-fatigue word banned on covers** (set it in the brand profile; for an AI page: AI, agent, model,
   chatbot, algorithm). Name the effect on people instead. Only where the headline means nothing without it.
2. **Stakes first:** job, salary, rent, children, health, exams, phone, car, fuel, internet.
3. **Power names** only when the story is really about that person or brand.
4. **Tension:** contrast, ban, firing, secret, reversal, command ("become a…", "don't…", "delete…").
5. **Short:** 4–7 words, one accent word, no full stop.
6. **Truth gate:** every name and number is in `allowed_claims`; a question mark on anything uncertain; no
   invented quotes, incitement, medical scare or fake "breaking".
7. **Controversial, not bland:** a headline that only describes or summarises the story fails.
8. **Never give away the twist.** "It was your child's voice, but not your child" tells the ending; "What if
   that's not your child on the phone?" makes them watch. The cover asks; the content answers.
9. **Clear before clever:** no nicknames, puns or riddles a newcomer cannot decode.
10. **Expert register when the brand is expert:** state a claim, a number or a consequence the way a sharp
    consultant would; no emoji, baby talk, filler hype ("you won't believe", "insane"), cartoon robots.

## 3. Angles (write candidates across all of them)
| angle | pattern | example |
|---|---|---|
| H — your life | name the viewer + a concrete stake | «اگه می‌خوای شغلت امن بمونه… لوله‌کش شو؟» (116k) |
| W — what if | `if <your person/thing> <the unthinkable>, then what?` | «اگه بچت پشت تلفن نباشه چی؟» |
| N — number contrast | `<number> <effort/cost> for only <number> <reward>` + kicker naming whose life | «۳.۶ ساعت کار در ازای فقط ۱ دلار» / kicker «درآمد یک ایرانی» |
| G — group call-out | name a job or life group, promise or warn | «آرایشگرها منتظر باشن» |
| B — power name | famous person/brand in the story | |
| C — conflict | ban, fight, firing, secret | |
| D — contrarian/command | "become…", "stop…", "everyone is wrong about…" | «حفظ کردن دیگه شغل نمیاره» |
| F — shock number | one number framed for a person | |

For money, work, price or time topics at least one candidate is angle N, and it wins when its numbers are
sourced. For danger or trust topics at least one is angle W.

## 4. Process
1. Write 12 candidates across the angles.
2. Score them automatically (length, fatigue words −6/−8, stake +3, life +4, what-if +4, tension +3, name +3,
   question +1.5, number +1, spoiler shape −3, novelty vs last 14 covers, truth gate on names/numbers).
3. **Stranger test (blocking):** an independent critic, given only the top 3 and a one-line summary, writes in
   one sentence what a newcomer understands in one second. If it does not name the stake (whose money/job/
   child, what happens), the headline fails. `headline_clarity` ≥ 7 to pass; ≤ 4 when the paraphrase is wrong.
4. Keep the winner and runner-up in state; the caption's first line and the first spoken line use the same
   angle.
5. Learn weekly: join reach and 3-second hold with the headline angle and features; add clearly winning
   words to the lexicon (≥ 3 items, ≥ 2× median reach); keep 1 cover in 4 on an under-tested angle.

## 5. Cover design
- **Its own design, never a video frame.** A premium photoreal thumbnail aimed at the audience, even when
  the video is typography or UI.
- **One centred text stack:** kicker, headline, optional sub, logo and handle together in the middle of the
  frame (inside the 4:5 grid crop), never scattered to the edges. Covers differ by background, palette and
  light key, not by text position.
- **Headline 120–150 px**, 2 lines; renderer fails it if it does not fit (shorten, don't shrink).
- **Kicker = one line**, big (≈ 100–120 px; shrink to fit, fail below ~56 px → shorten it to 2–5 words).
  A number always carries its noun and time: «۳۹٪ مهارت‌ها تا ۲۰۳۰ عوض می‌شه», never «تا ۲۰۳۰: ۳۹٪».
- **No labels:** never a recurring tag, series-format label or the fatigue word in the kicker, title, sub or
  logo label. At most a real number or a real name as the kicker.
- **No repeated cover element:** kicker/sub text never repeats any of the last 5 covers.
- **Real logo only of the main subject**, the official file placed as-is on a chip; never generated,
  redrawn or recoloured. No official file → the name in Latin type.
- **Real face** when the story is about a famous person (real photo, ≥ 40 % of frame).
- **Grid test:** place the cover next to the last 8 published covers; if the row looks like a template or the
  cover copies a neighbour (palette + layout + light key), redo it.
- **No text from the image model:** all words are typeset in code (exact spelling, RTL joining). Image
  prompts say "no text, no letters, no logos, no watermark".

## 6. Eight candidates in one frame (every cover and carousel slide 1)
1. **Two board calls** (the package's whole image budget), each prompted as **four vertical panels side by
   side with thin black gutters, every panel a different scene, subject, palette, light and composition**, no
   text, the subject in the middle third. These panels also serve as plates for the content.
2. **Four different headlines**, one per angle: W, N, H and one controversial claim, each `{title, kicker}`.
3. Render each headline on 2 panels → 8 covers; build a numbered 4×2 contact sheet.
4. The critic scores all 8 in one pass on `cover_stop_power` and `headline_clarity` (plus the stranger test);
   the best becomes the cover. Save the sheet and scores. When the owner wants to choose, send the sheet;
   their pick wins.
5. Eight near-copies do not count (same scene, different angle): rewrite the board prompt. A panel with real
   faces, political portraits, banknote faces or garbled text is dropped.
6. Cropping: cut each panel at its gutters, trim ~1.5 % per side, centre-crop to 9:16, upscale to 1080×1920;
   for the grid preview crop 1080×1350 from y≈285.

Board prompt pattern: «One wide 16:9 image divided into FOUR equal vertical panels side by side, separated by
thin pure-black gutters. Each panel is a completely different photoreal scene with its own lighting, palette
and composition. No text, no letters, no numbers, no logos anywhere. [Audience/setting]. [Who may appear and
how — e.g. children only from behind]. Panel 1: … Panel 4: … Cinematic, 35 mm film look, subject in the
middle third of each vertical panel.»

## 7. Fixing a published cover
Platforms do not let an API change a published reel's cover. Render the new cover (full 9:16 plus a 4:5
grid crop, and a text-free background if the owner wants to edit), and tell the owner the in-app path
(open the reel → ⋯ → Edit → Edit cover → upload).
