# Carousels and stories

## 1. Why carousels got no reach (diagnosis from 26 carousels)
Median reach 38 (≈ 3 % of followers), 1 save and 4 shares in total, while reels on the same page had a median
of ~1,400. The carousels were news summaries with a date slide first, small headlines, and nothing worth
keeping. Five fixes, all approved and applied:
1. **Saveable, not news.** A carousel is a utility the viewer keeps: "5 prompts for…", a checklist, before/after,
   "if you are a [job], these 4 tools…", "never tell a chatbot these 5 things", a how-to, a comparison table.
   One sourced fact may anchor it; breaking news goes to reels.
2. **Topics from the reel winners' family** (jobs, money, everyday life, a named group); no B2B deal news.
3. **Slide roles:** slide 1 = a cover (below); slide 2 delivers a useful item at once (no context or date
   slide); slides 3–8 one item each, readable without the caption; the last slide asks for the save or the send
   ("save this so you don't forget", "send it to a [job/friend]"). The caption's first line is the same hook,
   never a news-wire opening.
4. **Push it right after posting:** story 1 is slide 1 with "new post 👆 swipe" and the first useful item as a
   teaser; stories 2–3 tease two more items (APIs cannot add poll or link stickers).
5. **Review after two weeks** against the old median; if carousels still do not reach ~150 reach and several
   saves each, cut them to one a week. Cadence while testing: every other day.

## 2. Production
- **9 slides from one board image** (2560×3200, a 3×3 grid of 4:5 panels, one prompt listing the 9 panels in
  reading order, one world, light and palette), cut at the gutters to 1080×1350. Three stories from one
  3×1 board of 9:16 panels. Two image calls per post.
- **No text in generated pictures.** All text is typeset in code over the panels (exact spelling and joining);
  the renderer fails a slide whose text does not fit (shorten it) or has > 45 words.
- Slide kinds: hook, point, stat (big number + label), quote (real, sourced), cta. ≤ 45 words per slide.
  Every number, name and quote from `allowed_claims`.
- **Slide 1 is a cover:** one centred text stack exactly like the reel cover (headline system, 8 candidates,
  big kicker on one line). Never a headline in the top quarter with the rest of the frame empty; no slide
  leaves more than half the frame without purpose (the photo's subject fills it, or a number/label sits there).
- Footer typeset in code: handle, "n of 9", and "concept image" when the picture is generated.
- Board QA: read the board before cutting (9 distinct compositions of one story; real products match refs);
  at most one board regeneration; a weak panel is replaced by reusing/cropping another.
- Real products and places: reference photos are mandatory (see `reel-production.md` §5).

## 3. Caption (posts)
1. A clear, accurate summary in 3–5 short sentences (what happened, who, what is new, the key limit) — the
   reader understands it from the caption alone; for utility posts, the hook + what they get.
2. One line of practical meaning and one natural question or invitation.
3. Source line with name and date; no URLs in the caption (not clickable); keep URLs in the sheet.
4. No "images made with AI" disclaimer line; a credit line only for a licensed real photo.
5. 3–6 relevant hashtags; never guess popularity.
Forbidden in images and caption: treatment claims, growth guarantees, fake links or polls, anything that looks
like a tappable button or sticker.

## 4. Stories
- Story layout: no sequence number, no "concept image" label; only the handle, small, centred, the lowest
  element, just above the bottom safe line. Keep text out of the top ~230 px and bottom ~280 px of 1920.
- Footers and handles are always added in code; image models ignore coordinates for small text (one post cost
  42 images trying).
- **Every reel is also shared to the story** as a ≤ 60 s cut at a sentence boundary + the end card.
- A failed story never causes the post or reel to be published again.

## 5. Grid variety (covers and slide 1 together)
Look at the last 9 grid items before designing. Differ clearly from the last 3 and, in the combination of
palette + layout type + light key, from all 9; alternate dark and light keys so the grid has rhythm. Record a
design fingerprint (palette hex, key, layout) per item and check similarity automatically on the 4:5 crop.
