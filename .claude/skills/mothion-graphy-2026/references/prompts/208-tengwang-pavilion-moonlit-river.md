# Tengwang Pavilion moonlit river

- **id:** `208-tengwang-pavilion-moonlit-river` · **category:** MUSIC (Music-driven, audio-reactive motion)
- **source:** https://prompt-motion.com/demitiyageekzen-7770ad · **creator:** @DemitiyaGeekzen
- **use:** مناسب استفاده به‌عنوان تمرین سبک یا قطعه مستقل در یک کمپین/نمونه‌کار.
- **visual style:** موشن موسیقی‌محور و واکنش‌گرا به صدا
- **mood:** گرم، صمیمی یا آرام · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Using your strongest thinking, pick a topic I'd probably like, based on what you know about me, and make two things from it: a 30-second video and an interactive HTML page that goes deeper.
Show off your front-end skills as much as you can: WebGL, canvas and Web Audio where they help, with real interaction on the page.
Style: your choice.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
The video teases the topic and ends on an invitation to the page. The page lets me explore it, with the video's visual language.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a kick on every beat and a hit on each scene change. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
Tell me the topic and why you picked it, then build both without asking me anything else. Give me the MP4 and the HTML file.
</start>
````
