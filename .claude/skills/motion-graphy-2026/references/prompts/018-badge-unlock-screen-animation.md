# Badge unlock screen animation

- **id:** `018-badge-unlock-screen-animation` · **category:** 3D (3D cinematic space)
- **source:** https://prompt-motion.com/bthreeagency-b9b8d9 · **creator:** @BThreeAgency
- **use:** مناسب محتوای دانشی یا فرهنگی؛ برای مخاطبی که دنبال توضیح روشن و مستند است.
- **visual style:** سه‌بعدی و فضاسازی سینمایی
- **mood:** پریمیوم و کنترل‌شده · **audience:** یادگیرنده‌ها و مخاطب عمومی
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Build a badge unlock screen from the Figma frame I link. Match the design exactly: use the file's assets, lighting, type and layout, and add only the motion.
The badge unlock should feel premium and celebratory: build its scene, reveal it, then celebrate with gold particles.
Treat the badge as a solid 3D object that tilts toward the cursor following real physics (mass, damping), fast and smooth, never bouncy.
Banned: overshoot, wobble, glows the design doesn't have, anything that looks like a template.
</direction>

<structure>
The scene builds in, the badge arrives and settles with weight, the celebration plays once, then the badge stays interactive.
</structure>

<build>
1. One HTML file. Export the frame's assets from Figma and place them exactly.
2. Drive the tilt with a critically damped spring toward the cursor, so it never overshoots.
3. Check it at 60fps and fix any frame that stutters or doesn't match the design.
</build>

<start>
Tell me which assets you exported and how the sequence runs, then build it without asking me anything else.
</start>
````
