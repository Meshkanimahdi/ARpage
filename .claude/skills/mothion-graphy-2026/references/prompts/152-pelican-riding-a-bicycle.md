# Pelican riding a bicycle

- **id:** `152-pelican-riding-a-bicycle` · **category:** STORY (Character-driven story animation)
- **source:** https://prompt-motion.com/axtonliu-0b861d · **creator:** @AxtonLiu
- **use:** مناسب روایت داستانی، محتوای برندمحور یا فیلم کوتاه احساسی.
- **visual style:** انیمیشن داستانی با شخصیت، موقعیت و مسیر روایی
- **mood:** مدرن و هدف‌محور · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** ماندگار؛ به‌جای موج کوتاه، به موضوع و کیفیت روایت متکی است
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 30-second animated short film: a pelican riding a bicycle.
Style: the most complex, detailed and beautiful version you can make: real anatomy, a bicycle that actually works, a full landscape around them. Build it entirely in code.
Write the story first. Give the main character one clear want, three attempts that fail in different and escalating ways, a turn, and an ending that lands, plus a last-second gag after it.
Everyone draws this in HTML and SVG; go far beyond that, with any technology. There's no rush: take as long as you need.
Acting: every character reads in silhouette; every action has anticipation before it and follow-through after it; squash and stretch on anything soft; the eyes move first and the body follows; hold key poses for at least six frames.
Staging: one action per shot, framed so it reads instantly. Cut on action, matching the movement across the cut. Let the color shift with the mood.
Sound: a score and sound effects written in code. Sound should tell half the story.
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
