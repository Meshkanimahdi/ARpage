# Analytics loop

Measure what the audience really does with every post, story and reel, and feed it back into every prepare.
Read-only on the platform.

## 1. North-star metrics
Rank by **shares per 1k reach** first, then saves per 1k reach, then follower change on the publish day. Likes
are secondary. Track which topic families win on shares and follows (`life_topics`) and which reels qualify
for a part 2 (≥ ~20k views in 24 h).

## 2. Daily run (before the first prepare)
1. Inventory the last 30 days of media (paged); stories come from state files (they are not in the media list);
   join every media id to its state file for content id, field, topic, slot, format, angle, shape, look, voice,
   motion prompt and category, and the hook (first caption line). Media with no state file is tagged `manual`.
2. Metrics per type (retry once with fewer metrics on an error):
   - reels: views, reach, likes, comments, shares, saved, total interactions, average watch time, total watch
     time → retention = average watch ÷ duration
   - carousels: views, reach, likes, comments, shares, saved, total interactions
   - stories (only under 24 h old): views, reach, replies, shares, navigation, follows, profile visits
   Measure at 24 h, 72 h and 7 days; keep the latest value and its age.
3. Account: followers count (kept in a daily file), reach, views, accounts engaged, profile views, follows.
4. Sheet: a `Performance` tab (one row per media id, updated in place, incl. shares/1k and saves/1k) and an
   `Insights` tab (one row per day: followers, Δ, reach, best and worst item, top 3 lessons, changes applied).
5. Score each item against the median of its type over 14 days:
   - reels: 0.35 retention · 0.25 reach · 0.25 (shares + saves) ÷ reach · 0.15 follows/profile visits
   - carousels: 0.4 reach · 0.4 (saves + shares) ÷ reach · 0.2 likes/comments
   - stories: 0.5 reach ÷ followers · 0.3 navigation (fewer exits is better) · 0.2 replies and shares
6. Rank by field, topic type, format, angle, shape, look, motion category, voice gender, hook type, slot and
   length; a value needs ≥ 3 items before it counts as a leader or laggard.
7. Write `insights.json`: leaders, laggards, hook/caption/design lessons, explore (next untried options), and
   3–5 concrete recommendations for the next 48 h (e.g. "40–55 s reels with a question hook kept 20 % more
   viewers → next reel ≤ 55 s with a question hook"). Recommendations never break fact, rotation or owner rules.
8. Headline learning: join reach and 3-second hold with the headline angle and features; add clear winners to
   the lexicon.

## 3. Light refresh after every publish
At the end of every publish run, re-read the last 30 days' insights, add the item just published, rewrite the
whole Performance tab with a "last refreshed" cell, and record followers. A failed refresh is logged and never
delays publishing.

## 4. Weekly review
Compare the week with the one before (followers, reach, retention, saves + shares per reach); name the 3
strongest and 3 weakest patterns; set 3 experiments for next week; report cost per published item by format.

## 5. Reporting
Quote only live numbers. When the owner gives a number that contradicts yours, fetch fresh data before
answering, and say which was stale.
