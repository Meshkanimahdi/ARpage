# Backlink audit data promo

- **id:** `017-backlink-audit-data-promo` · **category:** UI (Product / app motion with a rebuilt real UI)
- **source:** https://prompt-motion.com/palashbagchi11-0a4b6b · **creator:** @PalashBagchi11
- **use:** مناسب موزیک‌ویدئو، معرفی موسیقی یا محتوای رویداد؛ تدوین باید با ضرب هماهنگ باشد.
- **visual style:** موشن محصول با نمایش رابط واقعی
- **mood:** مدرن و هدف‌محور · **audience:** کاربران بالقوه و تصمیم‌گیرندگان مرتبط با محصول
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** زیاد برای قالب‌های دیجیتال و اجتماعی؛ میزان بازدید واقعی سنجیده نشده
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Add music to the video I attach: a good, fast track, royalty-free with a license that allows social media.
Then make two versions: 1920x1080 landscape and 1080x1920 portrait, recomposing each frame for its shape rather than cropping blindly, so the important part is always in view.
</direction>

<structure>
Cut the music so it starts and ends with the video, with big moments landing on the beat.
</structure>

<build>
1. Find the beat grid of the music and nudge cuts to it where it helps.
2. Duck the music under any speech. Loudnorm to -14 LUFS.
3. Export each version with ffmpeg and watch each one through.
</build>

<start>
Tell me the track you picked and its license, then make the versions without asking me anything else.
</start>
````
