# Four seasons train window

- **id:** `088-four-seasons-train-window` · **category:** STORY (Character-driven story animation)
- **source:** https://prompt-motion.com/itsolelehmann-e47532 · **creator:** @itsolelehmann
- **use:** مناسب معرفی بازی، مکانیک بازی یا محتوای سرگرمی برای بازیکنان.
- **visual style:** انیمیشن داستانی با شخصیت، موقعیت و مسیر روایی
- **mood:** گرم، صمیمی یا آرام · **audience:** بازیکنان و علاقه‌مندان موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** ماندگار؛ به‌جای موج کوتاه، به موضوع و کیفیت روایت متکی است
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 30-second animated film: 4 seasons passing outside a train window, a cozy carriage, a cup of coffee on the table.
Style: Grand Budapest Hotel: symmetrical framing, pastel palette, flat theatrical depth. Build it entirely in code, with layered 2D illustration and a slow, steady camera.
Let the scene unfold in four to six moments, each changing one thing, while the rest stays still. Small details carry the story: light, steam, weather, what's on the table.
Banned: glows, lens flares, camera shake, generic gradients, anything that looks like stock clip art.
</direction>

<structure>
Equal time for each moment, joined by slow transitions that happen inside the scene (light changing, things passing the window), never cuts.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a quiet ambient soundtrack and the sounds of the scene. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
Show me the moments and a storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
