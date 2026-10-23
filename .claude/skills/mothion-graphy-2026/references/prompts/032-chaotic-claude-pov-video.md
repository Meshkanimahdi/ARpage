# Chaotic Claude POV video

- **id:** `032-chaotic-claude-pov-video` · **category:** UI (Product / app motion with a rebuilt real UI)
- **source:** https://prompt-motion.com/kloss-xyz-15182a · **creator:** @kloss_xyz
- **use:** مناسب استفاده به‌عنوان تمرین سبک یا قطعه مستقل در یک کمپین/نمونه‌کار.
- **visual style:** موشن محصول با نمایش رابط واقعی
- **mood:** پرانرژی و پرشتاب · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
A 30-second chaotic brain-rot video at 1080x1920, generated in Python and rendered with ffmpeg, with excellent motion and sound design.
Put your own spin on it, tied to Anthropic's new launch, and tell it from your point of view: what it's like to be a very creative LLM I use every day.
Chaotic but authored: fast cuts, stacked captions, zooms and sound hits that all land on the beat, with one running joke.
Banned: real people's faces or voices, copyrighted clips, anything unreadable at phone size.
</direction>

<structure>
140 BPM. A hook in the first half second, escalation every few beats, a payoff at the end that loops back to the start.
</structure>

<build>
1. Generate every frame in Python (Pillow and numpy), every frame a function of time.
2. Generate the sound in Python too (numpy synthesis), with hits on every cut, and write it to WAV.
3. Encode with ffmpeg at 30fps and mux the audio.
4. Watch the result at full speed and fix anything off the beat or hard to read.
</build>

<start>
Show me the beat-by-beat plan, then build it without asking me anything else. Give me the final MP4.
</start>
````
