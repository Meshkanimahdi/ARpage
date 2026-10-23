# Pixel wizard crypto animation

- **id:** `161-pixel-wizard-crypto-animation` · **category:** PIXEL (Pixel art and retro graphics)
- **source:** https://prompt-motion.com/0xevinho-3777d8 · **creator:** @0xEvinho
- **use:** مناسب استفاده به‌عنوان تمرین سبک یا قطعه مستقل در یک کمپین/نمونه‌کار.
- **visual style:** پیکسل‌آرت و گرافیک رترو
- **mood:** مدرن و هدف‌محور · **audience:** کاربران و علاقه‌مندان مالی/فناوری مالی
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** زیاد برای قالب‌های دیجیتال و اجتماعی؛ میزان بازدید واقعی سنجیده نشده
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Make a new version of the last video we made, reworked around a crypto reference.
Keep what made the original work: its structure, pacing and visual language. Change the subject, imagery and copy to fit the new reference, so it reads as its own piece, not a reskin.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
Match the original beat for beat, then improve anything that was weak.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a kick on every beat and a hit on each scene change. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
Tell me what you'll keep and what you'll change, then build it without asking me anything else. Give me the final MP4.
</start>
````
