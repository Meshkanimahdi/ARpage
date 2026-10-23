# Sahi trading terminal reveal

- **id:** `181-sahi-trading-terminal-reveal` · **category:** MUSIC (Music-driven, audio-reactive motion)
- **source:** https://prompt-motion.com/dale-vaz-cc612a · **creator:** @dale_vaz
- **use:** مناسب استفاده به‌عنوان تمرین سبک یا قطعه مستقل در یک کمپین/نمونه‌کار.
- **visual style:** موشن موسیقی‌محور و واکنش‌گرا به صدا
- **mood:** مدرن و هدف‌محور · **audience:** کاربران و علاقه‌مندان مالی/فناوری مالی
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 30-second, breathtaking animation of the Sahi Trading Terminal, in JavaScript. Be detailed and accurate: real-looking data, real layouts.
The journey: it starts as a single dot on a black screen; windows appear (Charts, Positions, Option Chain, Watchlist); the camera zooms in and out at several scales, then pulls out until the desktop is a point in space, and zooms back in to a phone in landscape with a chart in one half and an option chain in the other.
It ends on "Single Screen Trading on SAHI".
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
100 BPM. Each window lands on a beat; each zoom spans a bar; the pull-out to a point in space is the strongest moment.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a soft hit as each window lands and a swell on the big zoom. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
Show me a storyboard with every scale change, then build it without asking me anything else. Give me the final MP4.
</start>
````
