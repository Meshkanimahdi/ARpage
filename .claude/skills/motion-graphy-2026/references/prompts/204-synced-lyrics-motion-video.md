# Synced lyrics motion video

- **id:** `204-synced-lyrics-motion-video` · **category:** TYPE (Kinetic typography)
- **source:** https://prompt-motion.com/samaote-5e2fc2 · **creator:** @samaote
- **use:** مناسب موزیک‌ویدئو، معرفی موسیقی یا محتوای رویداد؛ تدوین باید با ضرب هماهنگ باشد.
- **visual style:** تایپوگرافی جنبشی و متن‌محور
- **mood:** مدرن و هدف‌محور · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** متوسط تا زیاد در نمونه‌کار و محتوای بصری؛ وابسته به اجرا و پلتفرم
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Make a 30-second lyric video for the song I attach, with the lyrics and animation synced perfectly to the vocals and the beat.
Make it feel like a motion designer's showreel: kinetic type that acts out each line, one visual idea that grows with the song.
Style: your choice, fitting the song.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
Follow the song's sections. Verses stay simple, the chorus opens up, and the biggest moment lands on the biggest musical moment.
</structure>

<build>
1. Find the beat grid with numpy and the timing of every sung word (e.g. with whisper word timestamps, checked by ear).
2. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t), with each word timed to its moment.
3. Render with Playwright at 60fps with motion blur (3 subframes, ffmpeg tmix), then mux the song.
4. Watch it with sound and fix any word that's early or late.
</build>

<start>
Show me the lyric timing and a storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
