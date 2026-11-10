# Lessons learned (failure → rule)

Each row is a real failure from running an automated page, and the rule that now prevents it. Read before
designing a new pipeline; most of these are invisible until they cost a week.

| what went wrong | rule now |
|---|---|
| Gates with an 8/10 bar and no fallback left slots empty for days | Bars 6, max 3 rounds, backlog first, never an empty slot (`production-pipeline.md` §3) |
| "Publish first" let four of six reels out on the same motion engine | Gate splits hard vs score fails; only score fails may publish |
| Reels looked alike: same effects, same motion, similar narrators | Variety is a hard rule: engine/family/category cooldowns, voice gender alternates, SFX set differs from last 3 |
| One "whoosh" on every cut annoyed viewers | Effects match the motion; ≤ 2 whooshes; no sound > 40 % |
| Photos sliding and zooming passed as "motion graphics" | ≥ 4 animated layers per scene; ≤ 2 photo-led shots; critic scores motion richness |
| Renamed copy of another engine made a "new" style look old | Each prompt gets its own engine; code-similarity check |
| "Different" catalog prompts were renamed twins | Deduplicate the catalog; block whole families |
| Covers all carried a format label ("from the AI's point of view") and looked childish | No labels or fatigue word on covers; expert register; series names are story names |
| Cover headline gave away the twist | Spoiler penalty; angle W ("what if…"); stranger test |
| 8 cover candidates all had the same weak line | The 8 candidates vary the wording too: 4 headlines × 2 backgrounds |
| Kicker number had no noun and wrapped to 2 lines | Kicker one line, number with its noun and time; renderer enforces |
| Carousel slide 1 headline sat at the top with 70 % of the frame empty | Slide 1 is a cover: centred stack; renderer refuses `top` on a hook slide |
| A girl's line was voiced by the male narrator | Cast list; speaker beats with matching gender/age voices; refuse mismatches |
| Brand names read with a local accent ("chet-GPT", "Pero") | Pronunciation test per English term, cached; glossary for native misreads |
| Narration sounded dry | Mix chain (EQ, de-ess, comp, short room, ducking) and −14 LUFS master; expressive tags |
| Image model painted political portraits on a classroom wall | Check every generated panel for real faces; drop the panel |
| Image model wrote footers in the wrong place (42 images on one post) | All text and footers typeset in code; never ask the model for text |
| One image per element blew the budget | One or two boards per package, cut into panels; per-package ledger |
| Credits ran out silently; reels reused old plates | Report 402s immediately with the top-up path; never reuse plates without saying so |
| Owner asked to repost a viral reel "with credit" | Credit is not permission; offer a permission message, a Collab, or our own remake |
| Rules changed mid-run caused a missed slot | New rules apply from the next prepare; tell the owner the first slot under the rule |
| A stale view count was quoted to the owner | Fetch live numbers before every report |
| Two sessions in one sandbox overwrote each other's variables | Never pass data between cells in plain globals; read back every write |
| Old "vary headline position" check survived a "centre everything" rule | Change the gate with the rule; delete contradicting checks |
| Reel published on a different engine than reported to the owner | Report what actually shipped (from state and history), including fallbacks |
| Next series part came the next day, before comments arrived | One week between parts, same weekday and slot; real vote count |
| Carousels: median reach 38, 1 save in 26 posts | Utility carousels (checklists, prompts, comparisons), slide 2 delivers, save/send ask, story push |
