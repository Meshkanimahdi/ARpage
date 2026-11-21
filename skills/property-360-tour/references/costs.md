# Unit costs and how to keep a project cheap

Prices are OpenRouter list prices read on 2026-11-21; re-read them (`GET /api/v1/models`) before quoting.
"Measured" = seen on our own invoices; "estimate" = computed from token counts, not yet measured.

## Unit prices

| item | model | price | basis |
|---|---|---|---|
| 360 panorama, 4K | google/gemini-3.1-flash-image | $0.155 | measured |
| 360 panorama trial, 1K | same | $0.07 | measured |
| local fix / photo edit, 2K | same | $0.10 | measured |
| narration transcript (1–2 min) | google/gemini-2.5-flash | $0.003 | measured |
| reasoning model, per 1M tokens in / out / cached | claude-sonnet-5.5 $2 / $10 / $0.10 · claude-opus-5.5 $4 / $20 / $0.20 · claude-fable-5.2 $8 / $40 / $0.20 · gemini-3.1-pro $2 / $12 / $0.20 · gemini-3.7-flash $0.75 / $3.75 / $0.07 | list |

## One two-bedroom flat, 9 tour points

| | plan right first time | typical | plan redone once |
|---|---|---|---|
| panoramas (9 + 3 second candidates) | $1.9 | $1.9 | $1.9 + $0.8 re-renders |
| local fixes | 3 → $0.3 | 8 → $0.8 | 15 → $1.5 |
| reasoning (plan + checking), estimate | $2–4 | $3–6 | $5–10 |
| **total** | **$4–6** | **$6–9** | **$9–14** |

Reasoning is the least certain line. A fixed pipeline (a handful of calls: read media → plan → check each panorama)
needs roughly 0.6–1.2 M input tokens and 30–60 k output: $2–4 on Sonnet-class, $5–10 on the top tier. An open-ended
agent that re-reads its context on every step uses ten times the input tokens, mostly at the cached price.
Cost scales with tour points: about $0.35–0.55 per extra point all in.

## What lowers cost (largest effect first)

1. **Complete capture** (capture-guide.md). A wrong plan is the one thing that multiplies cost; it was the difference
   between $2 and $9 of image spend on the same flat.
2. **Owner confirms the plan before rendering.** Free, and it catches what no model does.
3. **Automatic checks before the owner looks** (overlay, risk zooms): each catch is a $0.10 fix instead of a round trip.
4. **Fewer tour points**: one per small room; add points only in long rooms.
5. **Tiered models**: cheap model for transcription, photo sorting and coverage tables; strong model only for the plan
   and for judging panoramas. Batch pricing (half price) where a few hours' delay is acceptable. Prompt caching.
6. **Second candidates only for the main room.** 1K trials when testing wording.
7. **No AI for colour and exposure**: classic processing (white balance, exposure, straightening) is free and
   deterministic. Use the image model only for what needs it.

## Optional photo services (per delivered photo)

| service | how | cost |
|---|---|---|
| colour / light correction | classic processing | ~$0 |
| colour / light correction, "magazine" look | image model, 2K | ~$0.10 |
| remove clutter / unwanted objects | image model, 2K, mask-and-paste like fix_pano | ~$0.10 (plan for 1.3 tries → $0.13) |
| virtual staging of an empty room | image model, 2K–4K | $0.10–0.16, 1.5 tries → ~$0.20 |

The tour's panoramas need none of this: they are rendered clean and evenly lit from the plan whatever the source
photos looked like (dirty floors and boxes in the photos did not appear in the result).
