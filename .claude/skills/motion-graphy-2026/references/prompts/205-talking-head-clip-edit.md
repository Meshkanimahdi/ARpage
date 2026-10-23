# Talking-head clip edit

- **id:** `205-talking-head-clip-edit` · **category:** MUSIC (Music-driven, audio-reactive motion)
- **source:** https://prompt-motion.com/sab8a-364a5a · **creator:** @sab8a
- **use:** مناسب موزیک‌ویدئو، معرفی موسیقی یا محتوای رویداد؛ تدوین باید با ضرب هماهنگ باشد.
- **visual style:** موشن موسیقی‌محور و واکنش‌گرا به صدا
- **mood:** پرانرژی و پرشتاب · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Cut my raw talking-head clip into a punchy, fun 60-second edit for TikTok and Reels.
Keep the best lines and cut every pause, filler word and false start. Add word-by-word subtitles (bold white, one or two words at a time), graphics that illustrate the key points, and music with an upbeat, playful feel.
Banned: random stock footage, emoji spam, zoom punches on every line, captions that cover the face.
</direction>

<structure>
Hook in the first two seconds, using the strongest line even if it's not the first. One idea at a time after that. End on a clean last line, not a fade.
</structure>

<build>
1. Transcribe with word timestamps (e.g. whisper) and make the cut list from the transcript.
2. Cut with ffmpeg at 1080x1920, with jump cuts hidden by small zoom changes.
3. Make the subtitles and graphics as HTML rendered with Playwright, then composite them over the video.
4. Use music whose license allows the platform, ducked under the voice. Loudnorm to -14 LUFS.
5. Watch the result at full speed and fix any cut that clips a word.
</build>

<start>
Ask me for the clip, then show me the cut list with timestamps before you edit. Give me the final MP4.
</start>
````
