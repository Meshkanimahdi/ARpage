# Negroni recipe animation

- **id:** `138-negroni-recipe-animation` · **category:** EXPL (Explainer: diagram, data or timeline)
- **source:** https://prompt-motion.com/ror-fly-9950f1 · **creator:** @Ror_Fly
- **use:** مناسب آموزش یا توضیح موضوع؛ پیام را به گام‌ها و تصویرهای قابل‌فهم بشکند.
- **visual style:** موشن توضیحی، دیاگرام یا تایم‌لاین
- **mood:** گرم، صمیمی یا آرام · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** ماندگار؛ به‌جای موج کوتاه، به موضوع و کیفیت روایت متکی است
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 30-second recipe explainer for a cocktail of your choice, from an empty glass to the finished drink.
Show each ingredient and its measurement as it goes into the glass: the pour, the level rising, the measure in clean type beside it. Then the final touches (stirring and any garnish) and a moment to admire it.
Style: clean, bright product photography in motion: a soft background, crisp liquid and glass.
Banned: stock clip art, glows, generic gradients, measurements you'd have to pause to read.
</direction>

<structure>
100 BPM. One ingredient per bar, the glass in the same spot throughout, the camera easing in for the finish.
</structure>

<build>
1. One HTML file at 1080x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a pour, ice or clink sound on each step, under light music. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<start>
List the recipe with measurements, then show a storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
