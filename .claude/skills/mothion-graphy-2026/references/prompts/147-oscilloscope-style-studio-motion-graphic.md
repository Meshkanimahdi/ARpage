# Oscilloscope-style studio motion graphic

- **id:** `147-oscilloscope-style-studio-motion-graphic` · **category:** MUSIC (Music-driven, audio-reactive motion)
- **source:** https://prompt-motion.com/rneayan-ea6129 · **creator:** @rneayan
- **use:** مناسب معرفی هویت برند/استودیو یا روایت یک مناسبت و نقطه عطف.
- **visual style:** موشن موسیقی‌محور و واکنش‌گرا به صدا
- **mood:** مدرن و هدف‌محور · **audience:** کارفرماها، مشتریان یا جامعه طراحان
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** متوسط تا زیاد در نمونه‌کار و محتوای بصری؛ وابسته به اجرا و پلتفرم
- **has an `<inputs>` block (slots to personalise):** yes

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<inputs>
Ask me for anything below I haven't given you. If I skip it, use the default: 3 to 6 screenshots of the real interface (default: capture them yourself), the logo (default: take it from the site), brand colors and font (default: an oscilloscope look: green phosphor lines on black, traces that glow and decay), and a royalty-free track with a clear beat (default: compose one in code).
</inputs>

<direction>
A 20-second studio film for my studio. Use the live site's real assets (logo, screenshots, copy) wherever they fit. Never invent features or numbers.
Pick one through-line object from the product itself (its cursor, a key button, the logo's mark, a single data point) and make every scene a transformation of it: it starts in the UI, changes shape or role in each scene, and becomes the logo on the end card. Name it before you storyboard.
Rebuild the real UI as vector layers so its parts can move on their own; never slide a flat screenshot in. A cursor drives every interaction with real clicks and drags, and the camera zooms screen-studio style so each moment fills the frame.
Brand: an oscilloscope look: green phosphor lines on black, traces that glow and decay. One typeface, one accent color used only on the through-line object and the key word, lots of empty space. Everything drawn as oscilloscope traces.
Motion rules: springs with at most a small overshoot; nothing appears from nothing (it grows, unfolds or is revealed by a mask); the camera never sits still (push from 1.0 to 1.04 across a scene, and start each scene at the zoom the last one ended on); something changes on every beat.
Banned: particle bursts, glows, lens flares, camera shake, RGB split, crossfades, generic gradients, bouncy easing, holds longer than half a second, anything that looks like a template.
</direction>

<structure>
120 BPM. Write a timed storyboard first, beat by beat, then build exactly that.
Hook (first bar): the problem in three to five words, in big type that the through-line object interrupts.
Middle: three or four moments of the product doing what it does best. Each begins with the through-line object turning into the next UI element and lands one readable idea.
Payoff (last bars): the strongest moment on the biggest beat, then the through-line object becomes the logo and the end card: the name and a one-line call to action.
</structure>

<build>
1. One HTML file at 1920x1080. Every style is computed from time inside window.seek(t): no CSS animations, no timers, no state carried between frames.
2. Use spring and exponential easing written as functions of time. Blur follows speed and direction on fast moves.
3. Write a soundtrack in code with the Web Audio API (OfflineAudioContext): a kick on every beat and a hit on each scene change. Render it to WAV.
4. Render with Playwright at 60fps, 3 subframes per frame blended with ffmpeg tmix for motion blur, then mux the audio.
5. Before the full render, render one frame per beat and look at them. Fix anything cluttered, off the beat, overlapping or hard to read.
</build>

<gotchas>
Measure element positions at runtime for match cuts instead of hard-coding them. When a shape fills the frame, scale it past all four corners. Give outgoing and incoming text separate timing so letters never overlap. Never put will-change on anything the camera scales, or text renders blurry.
</gotchas>

<start>
Show me what you found, the through-line object and a beat-by-beat storyboard, then build it without asking me anything else. Give me the final MP4.
</start>
````
