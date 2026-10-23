# Lightspark social promo video

- **id:** `112-lightspark-social-promo-video` · **category:** UI (Product / app motion with a rebuilt real UI)
- **source:** https://prompt-motion.com/davidmarcus-a28a60 · **creator:** @davidmarcus
- **use:** مناسب موزیک‌ویدئو، معرفی موسیقی یا محتوای رویداد؛ تدوین باید با ضرب هماهنگ باشد.
- **visual style:** موشن محصول با نمایش رابط واقعی
- **mood:** پرانرژی و پرشتاب · **audience:** کاربران بالقوه و تصمیم‌گیرندگان مرتبط با محصول
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** زیاد برای قالب‌های دیجیتال و اجتماعی؛ میزان بازدید واقعی سنجیده نشده
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A punchy, modern 20-second video for social that promotes Lightspark (@lightspark): its main capabilities. Research the product first and use its real interface and brand; never invent features or numbers.
It has to stop the scroll: a hook in the first second, one idea per shot, big readable type, captions that work with the sound off.
Production grade, with sound: music and effects synced to every cut.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
120 BPM, something happens on every beat.
Hook in beat one. Then one capability per bar, each made out of the last. End on the name and what to do next.
</structure>

<build>
1. One HTML file at 1080x1920. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a kick on every beat and a hit on each scene change. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
Show me what you found and a beat-by-beat storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
