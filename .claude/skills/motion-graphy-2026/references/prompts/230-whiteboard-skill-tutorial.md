# Whiteboard skill tutorial

- **id:** `230-whiteboard-skill-tutorial` · **category:** EXPL (Explainer: diagram, data or timeline)
- **source:** https://prompt-motion.com/lemomo-ai-0d9cff · **creator:** @lemomo_ai
- **use:** مناسب آموزش یا توضیح موضوع؛ پیام را به گام‌ها و تصویرهای قابل‌فهم بشکند.
- **visual style:** موشن توضیحی، دیاگرام یا تایم‌لاین
- **mood:** روشن و آموزنده · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** ماندگار؛ به‌جای موج کوتاه، به موضوع و کیفیت روایت متکی است
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 90-second explainer on how to create videos with the Lemo-Opuscar skill on Opus 5.5: one prompt, one answer, then ship the film for a creator trying it for the first time. Research it first and keep every fact right; never invent numbers or quotes.
Build the whole explanation as one diagram in one continuous space: the camera zooms into a part to explain it and pulls back to show how it fits, so the viewer always knows where they are. Every idea gets a picture before it gets words, and labels sit on the thing they name, never in a legend.
Style: a whiteboard explainer: a marker draws each step as it's explained. Narrate it with a clear synthesized voice (e.g. edge-tts en-US-AriaNeural), with subtitles synced line by line.
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
1. Write the narration script first, line by line, marking what's on screen for each line.
2. Generate each line with a clear synthesized voice (e.g. edge-tts en-US-AriaNeural) and time the animation to each line's real audio length.
3. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
4. Render with Playwright at 60fps, 3
````
