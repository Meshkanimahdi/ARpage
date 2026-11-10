# Series with a decision cliffhanger

## Why
A survival mini-series («۲۰۰ روز تا یخبندان | قسمت اول», 131 s) got 103k plays and **1,557 comments in ~17 h**
(≈ 15 comments per 1k plays; a typical reel gets under 1). Its ending is the reason: copy its **structure**,
never its story, script or visuals.

## Structure of every part except the last
- **A concrete dilemma with real stakes and no right answer.** Build a situation (a budget, a countdown, a
  family), then stop at the moment of choice: two numbered options, both defensible, both with a cost
  ("1️⃣ I open the door. 2️⃣ I keep it shut."). No quiz with one correct answer; no generic "what do you think?".
- **The viewer decides the next part.** Last spoken line, end card and caption opener: "1 or 2? Write it in the
  comments — the next part is built from your choice." The caption restates the dilemma in 2–4 short lines,
  lists the two options, then «series name | part N», then hashtags.
- **Tie it to the page's niche:** e.g. the AI is a character that recommends one option with its reason, and the
  viewer may overrule it; its recommendation is argued fairly, never as the obvious winner.
- **Series name on everything:** a short story name (not a format label) on the cover, in the first second and
  in the caption, with the same look across parts so a returning viewer recognises it in the feed.

## Between parts
- **Exactly one week between parts, same weekday and same slot** (part 1 Tuesday 15:00 → part 2 the next
  Tuesday 15:00), so part N has a full week to collect comments. Several series can run side by side, each on
  its own weekday and slot; other content fills the slots in between.
- Part 1's end card and caption name the day: "Part 2: next Tuesday, 15:00".
- **Count the real vote** on the morning of the next part's prepare: read part N's comments, count «1»/«2»
  (both digit scripts and clear words). Open part N+1 with the true result ("63 % of you said open the door —
  so…") and follow the majority. **Never invent a percentage;** under 30 votes, say "most of you said…" with no
  number.
- A gate fails a part dated less than 7 days after the previous part, a part without the real vote, and a
  non-final part without a two-option choice and the AI's pick. The history records `series` and `series_part`.

## The last part
Resolves the story, says what the choices taught (one practical takeaway), ends with the share ask and the
next series' name.

## Concept fields
`series: {name, part, of, choice: {question, options: [a, b], ai_pick}, vote: {"1": n, "2": n}}`

## Also: part 2 for a hit
A standalone reel that passes ~20k views in 24 h gets a part 2 one week later, same weekday and slot (same
topic, the next useful step), announced in part 1's caption.

## Tone
Calm and true; no gore, no war predictions; survival themes are "what would you do / how to be ready".
