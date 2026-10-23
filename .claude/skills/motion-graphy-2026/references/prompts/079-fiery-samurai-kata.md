# Fiery samurai kata

- **id:** `079-fiery-samurai-kata` · **category:** ANIME (Anime / cinematic 3D action)
- **source:** https://prompt-motion.com/chrisjdimarco-f068db · **creator:** @chrisjdimarco
- **use:** مناسب استفاده به‌عنوان تمرین سبک یا قطعه مستقل در یک کمپین/نمونه‌کار.
- **visual style:** انیمه/سه‌بعدی سینمایی با حرکت نمایشی
- **mood:** پرانرژی و پرشتاب · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 30-second animation in pure JavaScript (canvas, no libraries) of a samurai performing a routine in a single spot: a series of impressive poses, strikes and stances.
Make the movement seriously impressive: real weight, anticipation and follow-through, holds that land on the beat. Surround it with a fiery display.
Banned: stiff tweening between poses, glows that hide the figure, camera shake, anything that looks like a template.
</direction>

<structure>
100 BPM. One pose or move per bar, building to the most impressive one, then a final held pose.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): music with a hit on each pose. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
List the poses in order, then build it without asking me anything else. Give me the final MP4.
</start>
````
