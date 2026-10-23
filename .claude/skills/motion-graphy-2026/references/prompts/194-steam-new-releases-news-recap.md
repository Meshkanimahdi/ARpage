# Steam new releases news recap

- **id:** `194-steam-new-releases-news-recap` · **category:** EXPL (Explainer: diagram, data or timeline)
- **source:** https://prompt-motion.com/gigabit-million-16b3a0 · **creator:** @gigabit_million
- **use:** مناسب آموزش یا توضیح موضوع؛ پیام را به گام‌ها و تصویرهای قابل‌فهم بشکند.
- **visual style:** موشن توضیحی، دیاگرام یا تایم‌لاین
- **mood:** بازیگوش و سرگرم‌کننده · **audience:** بازیکنان و علاقه‌مندان موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** ماندگار؛ به‌جای موج کوتاه، به موضوع و کیفیت روایت متکی است
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 60-second explainer on the games released on Steam from September 25 to 26: what's fun about each one, from a gamer's point of view for gamers. Research it first and keep every fact right; never invent numbers or quotes.
Build the whole explanation as one diagram in one continuous space: the camera zooms into a part to explain it and pulls back to show how it fits, so the viewer always knows where they are. Every idea gets a picture before it gets words, and labels sit on the thing they name, never in a legend.
Style: a fast news roundup: one card per game with its real capsule art and a one-line hook, on-screen text in Japanese.
Motion rules: one thing moves at a time, and the eye always knows where to look; arrows and flows animate in the direction things actually move; no more than seven words on screen at once, held for at least 0.3 seconds a word.
Banned: walls of text, bullet lists, generic gradients, stock-looking icons, glows, crossfades, anything that looks like a template.
</direction>

<structure>
Write a timed storyboard first, then build exactly that.
Hook: a question the viewer already has, asked over the first picture.
Middle: three to five steps. Each zooms into one part of the diagram, shows one concrete example, then pulls back as that part locks into place.
Payoff: a final pull back to the whole diagram, now complete, and a one-line takeaway.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a soft pulse under each step and a hit as each idea lands. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<gotchas>
Check every number and name against a source. Keep the diagram's layout fixed so zooming in and out never reshuffles it. Give outgoing and incoming text separate timing so letters never overlap.
</gotchas>

<start>
Show me the steps, the diagram and a timed storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
