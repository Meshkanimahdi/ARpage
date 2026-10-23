# TypingMind logo reveal

- **id:** `217-typingmind-logo-reveal` · **category:** GEO (Geometric shapes and continuous morphing)
- **source:** https://prompt-motion.com/tdinh-me-815acb · **creator:** @tdinh_me
- **use:** مناسب رونمایی نشان یا پایان‌بندی کمپین؛ تمرکز روی خوانایی و لحظه آشکارشدن.
- **visual style:** فرم‌های هندسی و مورفینگ پیوسته
- **mood:** انتزاعی و تجربه‌محور · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 10-second logo reveal for TypingMind: a slow, satisfying transition where abstract fragments of its shapes assemble piece by piece and only resolve into the logo in the last few seconds.
Use the logo file I attach exactly; never redraw it from memory. Palette: the logo's own colors.
The build-up should keep the eye guessing; the moment it becomes the logo should feel inevitable.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
90 BPM. Slow at first, a little faster each bar, then the logo lands on a downbeat and holds for one bar.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): soft textures building with the assembly and one clean hit as the logo lands. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
Ask me for the logo file (SVG if possible), then show me a storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
