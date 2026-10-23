# Shin Majin-shiki promo

- **id:** `187-shin-majin-shiki-promo` · **category:** UI (Product / app motion with a rebuilt real UI)
- **source:** https://prompt-motion.com/majin-appsheet-2d3c1a · **creator:** @Majin_AppSheet
- **use:** مناسب معرفی یا عرضه محصول دیجیتال؛ مزیت و تجربه استفاده را با رابط واقعی نشان دهد.
- **visual style:** موشن محصول با نمایش رابط واقعی
- **mood:** روشن و آموزنده · **audience:** کاربران بالقوه و تصمیم‌گیرندگان مرتبط با محصول
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** زیاد برای قالب‌های دیجیتال و اجتماعی؛ میزان بازدید واقعی سنجیده نشده
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 30-second promo video for Shin Majin-shiki. Research it first: what it is, what it does and who it's for. Use only what you find; never invent features or numbers.
Carry one visual idea all the way through, with every scene made out of the last instead of cutting or fading.
Tone: poppy and full of energy. One typeface, one accent color, lots of empty space. On-screen text in Japanese.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
120 BPM, something happens on every beat.
Hook in the first bar. Then one strength per bar, each flowing out of the last. End on the name and a one-line tagline.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write the music and sound effects in code with the Web Audio API (OfflineAudioContext), on the beat grid and on each scene change. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
Show me what you found and a beat-by-beat storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
