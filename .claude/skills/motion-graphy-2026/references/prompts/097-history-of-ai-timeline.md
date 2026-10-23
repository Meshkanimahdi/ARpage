# History of AI timeline

- **id:** `097-history-of-ai-timeline` · **category:** EXPL (Explainer: diagram, data or timeline)
- **source:** https://prompt-motion.com/kloss-xyz-fe0c31 · **creator:** @kloss_xyz
- **use:** مناسب آموزش یا توضیح موضوع؛ پیام را به گام‌ها و تصویرهای قابل‌فهم بشکند.
- **visual style:** موشن توضیحی، دیاگرام یا تایم‌لاین
- **mood:** روشن و آموزنده · **audience:** یادگیرنده‌ها و مخاطب عمومی
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** زیاد برای قالب‌های دیجیتال و اجتماعی؛ میزان بازدید واقعی سنجیده نشده
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 2-minute video highlighting the key moments in the history of AI. Research it first and choose 12 to 15 moments that changed its course. For each: the year, what happened and why it mattered, in one line.
Style: a clean editorial timeline, one typeface, archival photos where the license allows. Keep the facts right: date and name every moment, and never invent a quote.
Banned: glows, generic gradients, stock-looking icons, crossfades, anything that looks like a template.
</direction>

<structure>
A short hook, then the moments in order on one continuous timeline the camera travels along. Each moment gets the same rhythm: the year lands, the event appears, one line on why it mattered. End on where things stand now.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a hit as each year lands, and music that builds toward the present. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
Show me your list of moments with sources and a storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
