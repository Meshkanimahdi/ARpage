# Prompting mistakes video tutorial

- **id:** `168-prompting-mistakes-video-tutorial` · **category:** EXPL (Explainer: diagram, data or timeline)
- **source:** https://prompt-motion.com/henkvaness-0e06af · **creator:** @henkvaness
- **use:** مناسب آموزش یا توضیح موضوع؛ پیام را به گام‌ها و تصویرهای قابل‌فهم بشکند.
- **visual style:** موشن توضیحی، دیاگرام یا تایم‌لاین
- **mood:** روشن و آموزنده · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** ماندگار؛ به‌جای موج کوتاه، به موضوع و کیفیت روایت متکی است
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 90-second explainer on the article I paste in for someone who hasn't read it.
Build the whole explanation as one diagram in one continuous space: the camera zooms into a part to explain it and pulls back to show how it fits, so the viewer always knows where they are. Every idea gets a picture before it gets words, and labels sit on the thing they name, never in a legend.
Style: clean editorial motion graphics: one typeface, one accent color, diagrams that build themselves. Narrate it with a clear synthesized voice (e.g. edge-tts en-US-AriaNeural), with subtitles synced line by line. Stay faithful to the article: no claims it doesn't make.
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
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux in the narration, quiet music under it and subtitles.
5. Before the full render, export a key frame from each section and check it. Fix anything crowded, overlapping or hard to read.
</build>

<gotchas>
Check every number and name against a source. Keep the diagram's layout fixed so zooming in and out never reshuffles it. Give outgoing and incoming text separate timing so letters never overlap.
</gotchas>

<start>
Show me the script, the diagram and a timed storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
