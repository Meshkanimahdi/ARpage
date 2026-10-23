# Bento.surf product video

- **id:** `021-bento-surf-product-video` · **category:** UI (Product / app motion with a rebuilt real UI)
- **source:** https://prompt-motion.com/bizibeast-10f264 · **creator:** @bizibeast
- **use:** مناسب موزیک‌ویدئو، معرفی موسیقی یا محتوای رویداد؛ تدوین باید با ضرب هماهنگ باشد.
- **visual style:** موشن محصول با نمایش رابط واقعی
- **mood:** مدرن و هدف‌محور · **audience:** کاربران بالقوه و تصمیم‌گیرندگان مرتبط با محصول
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** زیاد برای قالب‌های دیجیتال و اجتماعی؛ میزان بازدید واقعی سنجیده نشده
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 5-minute animated short film: a story about time.
Style: drawn from this machine's own environment: its terminal, theme and fonts. Build it entirely in code.
Write the story first. Give the main character one clear want, three attempts that fail in different and escalating ways, a turn, and an ending that lands, plus a last-second gag after it.
Set up any tools you need yourself. When it's rendered, keep only the final video and clean up everything else.
Acting: every character reads in silhouette; every action has anticipation before it and follow-through after it; squash and stretch on anything soft; the eyes move first and the body follows; hold key poses for at least six frames.
Staging: one action per shot, framed so it reads instantly. Cut on action, matching the movement across the cut. Let the color shift with the mood.
Sound: music, narration and subtitles. Sound should tell half the story.
Banned: glows, lens flares, generic gradients, anything that looks like stock clip art, everything moving at once.
</direction>

<structure>
Write a shot list first, one action per shot, with timings, then build exactly that. Shots join through motion and sound, never crossfades.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): the film's sound, timed to the shot list. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<gotchas>
Lock feet and hands where they touch things, so contacts never slide. Keep the character's proportions the same in every shot. Give each gag a beat of stillness before it lands.
</gotchas>

<start>
Show me the story in a few lines and the shot list, then build it without asking me anything else. Give me the final MP4.
</start>
````
