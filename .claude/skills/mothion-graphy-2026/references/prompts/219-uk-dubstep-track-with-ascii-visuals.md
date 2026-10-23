# UK dubstep track with ASCII visuals

- **id:** `219-uk-dubstep-track-with-ascii-visuals` · **category:** MUSIC (Music-driven, audio-reactive motion)
- **source:** https://prompt-motion.com/rames-jusso-589f80 · **creator:** @Rames_Jusso
- **use:** مناسب موزیک‌ویدئو، معرفی موسیقی یا محتوای رویداد؛ تدوین باید با ضرب هماهنگ باشد.
- **visual style:** موشن موسیقی‌محور و واکنش‌گرا به صدا
- **mood:** پرانرژی و پرشتاب · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 30-second music visual: a Rusko and Skream style UK dubstep track at 140 BPM, written in code, with visuals driven by it.
Write the track first: drums, a sub bass and a wobble bass on a real arrangement (intro, build, drop). Then make every visual move come from the music: kicks, snares and wobbles each drive something you can see.
Visual style: bold geometric shapes and type in two colors, hit hard by the bass.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
Intro, a build that tightens, the drop on a downbeat as the strongest moment, and a short outro.
</structure>

<build>
1. Write the track with the Web Audio API (OfflineAudioContext) and render it to WAV; keep the note and hit times as data.
2. One HTML file at 1080x1080. Every style is computed from time and that hit data inside window.seek(t): no timers, no state between frames.
3. Render with Playwright at 60fps with motion blur (3 subframes, ffmpeg tmix), then mux the audio.
4. Watch it with sound and fix anything that isn't locked to the beat.
</build>

<start>
Describe the arrangement in a few lines, then build it without asking me anything else. Give me the final MP4.
</start>
````
