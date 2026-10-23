# Five scroll-based sections

- **id:** `083-five-scroll-based-sections` · **category:** TOPIC (Topic-led motion (the prompt sets the style))
- **source:** https://prompt-motion.com/ercankeskinx-ec2568 · **creator:** @ercankeskinx
- **use:** مناسب استفاده به‌عنوان تمرین سبک یا قطعه مستقل در یک کمپین/نمونه‌کار.
- **visual style:** موشن گرافیک موضوع‌محور؛ سبک دقیق را خود پرامپت تعیین می‌کند
- **mood:** مدرن و هدف‌محور · **audience:** مخاطب عمومی یا علاقه‌مند به موضوع
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Build 5 completely different scroll-driven sections, each on its own context and layout that you choose: your choice.
Each one should feel like a different studio made it: its own typography, color, and way of tying motion to the scroll.
Motion is driven by scroll position, scrubbable both ways, never by timers.
Banned: parallax for its own sake, fade-up on everything, glows, generic gradients, anything that looks like a template.
</direction>

<structure>
One section per screen-and-a-half of scroll, each with a clear beginning, middle and end tied to its scroll range.
</structure>

<build>
1. One HTML file, no libraries. Every style is computed from the section's scroll progress (0 to 1).
2. Smooth the scroll value with a critically damped spring so it settles without bounce.
3. Check every section at 1440 and 390 wide, scrolling forward and back, and fix anything that jumps.
</build>

<start>
List the 5 contexts and layouts you picked, then build it without asking me anything else.
</start>
````
