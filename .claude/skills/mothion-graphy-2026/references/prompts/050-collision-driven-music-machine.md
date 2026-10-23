# Collision-driven music machine

- **id:** `050-collision-driven-music-machine` · **category:** MUSIC (Music-driven, audio-reactive motion)
- **source:** https://prompt-motion.com/kamstudiolabs-447565 · **creator:** @KamStudioLabs
- **use:** مناسب موزیک‌ویدئو، معرفی موسیقی یا محتوای رویداد؛ تدوین باید با ضرب هماهنگ باشد.
- **visual style:** موشن موسیقی‌محور و واکنش‌گرا به صدا
- **mood:** گرم، صمیمی یا آرام · **audience:** یادگیرنده‌ها و مخاطب عمومی
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** متوسط تا زیاد در نمونه‌کار و محتوای بصری؛ وابسته به اجرا و پلتفرم
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Build a 45-second machine that plays an original piece of music, where every note comes from a visible collision: balls, bells, pegs and xylophone bars, like a Rube Goldberg marble run.
Compose the piece first, then design the machine so the physics produces it exactly: every hit lands on its note.
Style: warm wood and brass on a clean background.
Banned: notes without a visible cause, glows, generic gradients, anything that looks like a tech demo.
</direction>

<structure>
The machine starts quiet with one voice, adds parts as it goes, peaks, and resolves on a final hit.
</structure>

<build>
1. Write the piece as note data (time, pitch, instrument) and synthesize it with the Web Audio API (OfflineAudioContext) to WAV.
2. One HTML file at 1920x1080. Positions are solved backwards from each note's time, so every collision is exact. Every frame is a function of time inside window.seek(t).
3. Render with Playwright at 60fps with motion blur, then mux the audio.
4. Watch it with sound and fix any hit that's off.
</build>

<start>
Describe the piece and the machine, then build it without asking me anything else. Give me the final MP4.
</start>
````
