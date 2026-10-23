# Derivative concept explainer

- **id:** `058-derivative-concept-explainer` · **category:** EXPL (Explainer: diagram, data or timeline)
- **source:** https://prompt-motion.com/linearuncle-5d2bae · **creator:** @LinearUncle
- **use:** مناسب آموزش یا توضیح موضوع؛ پیام را به گام‌ها و تصویرهای قابل‌فهم بشکند.
- **visual style:** موشن توضیحی، دیاگرام یا تایم‌لاین
- **mood:** روشن و آموزنده · **audience:** یادگیرنده‌ها و مخاطب عمومی
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** ماندگار؛ به‌جای موج کوتاه، به موضوع و کیفیت روایت متکی است
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Use Manim to make a 3-minute lesson on the derivative for complete beginners. Make it easy to understand, with concrete examples, and make people think.
Start from an everyday question that leads to the idea, build intuition step by step, and only then give the formal definition and formula. Every new idea gets something on screen: a graph, an animation, a color that tracks it.
Narrate it in Chinese with edge-tts (zh-CN-XiaoxiaoNeural), with subtitles synced line by line.
Banned: long blocks of static text, formulas piled up without animation, music louder than the voice.
</direction>

<structure>
The question, the intuition, two or three examples from easy to harder, the formal definition, and a question for the viewer to think about at the end.
</structure>

<build>
1. Write the narration script first, line by line, marking what's on screen for each line.
2. Generate each line with edge-tts and time the Manim animations to each line's real audio length.
3. Render with Manim at 1920x1080, 60fps, and mux in the narration and subtitles.
4. Before the full render, export a key frame from each section and check it. Fix anything crowded, overlapping or hard to read.
</build>

<start>
Show me the script and a storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
