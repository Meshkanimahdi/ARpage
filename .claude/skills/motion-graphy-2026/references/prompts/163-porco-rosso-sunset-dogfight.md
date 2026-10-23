# Porco Rosso sunset dogfight

- **id:** `163-porco-rosso-sunset-dogfight` · **category:** ANIME (Anime / cinematic 3D action)
- **source:** https://prompt-motion.com/nft-chen-5f8bb0 · **creator:** @NFT_Chen
- **use:** مناسب محتوای دانشی یا فرهنگی؛ برای مخاطبی که دنبال توضیح روشن و مستند است.
- **visual style:** انیمه/سه‌بعدی سینمایی با حرکت نمایشی
- **mood:** گرم، صمیمی یا آرام · **audience:** یادگیرنده‌ها و مخاطب عمومی
- **gender target:** جنسیت هدف در پرامپت مشخص نشده؛ قابل ارائه به همه جنسیت‌ها
- **trend fit:** نیچ/وابسته به موضوع کمپین؛ با اجرای مناسب می‌تواند جذاب شود
- **has an `<inputs>` block (slots to personalise):** no

## Prompt — verbatim. Do not change its structure (see SKILL.md → "What you may change").

````text
<direction>
Build the dogfight over the sea at sunset from Hayao Miyazaki's Porco Rosso as one self-contained HTML page with three.js.
Style: Ghibli: hand-painted skies, purple cumulus clouds, warm sunset light, the sea catching it. Stylised, not photoreal: soft shading, painterly water reflections.
Design the signature shot first, the one frame someone would screenshot, and build everything toward it.
Camera: a film camera, not orbit controls. Every shot uses one named move (dolly, crane, orbit, push-in, rack focus), eased in and out, and the camera never passes through geometry.
Light and materials: a key, fill and rim light with soft shadows, an environment map for reflections, fog for depth, physically based materials with varied roughness, ACES tone mapping. Nothing should look like a default material.
Motion: things react to each other (what's hit moves, what's near lights up), driven by springs or simple physics, never linear tweens.
Banned: default materials and lighting, floating text labels, glows on everything, a slowly spinning object as the whole idea, anything that looks like a tech demo.
</direction>

<structure>
Fighter planes in white, green and red livery chase each other through the clouds while the camera moves like a Ghibli film, low over the water then up through the clouds. The words "just breathe." appear once, quietly.
Plan it as a shot list: an establishing wide, three to five shots that each have one camera move and one event, the signature shot, and a final wide that shows it in a new light.
</structure>

<build>
1. One HTML file, three.js from a CDN, no build step. Model everything in code; no downloaded models or textures.
2. Use MeshPhysicalMaterial, a PMREM environment from RoomEnvironment, soft shadows, ACES tone mapping and antialiasing. Add depth of field only on shots that need it.
3. Hold 60fps on a laptop.
4. Add a ?render mode where every frame is computed from time (seeded randomness, no clock), so it can be captured with Playwright into an MP4 at 1920x1080.
5. Capture one frame per shot, look at it, and fix anything flat, aliased, clipping or hard to read.
</build>

<gotchas>
Set shadow bias, or surfaces get striped acne. Keep near and far planes tight, or distant surfaces flicker. Seed every random number, or the render won't match the preview.
</gotchas>

<start>
Describe the signature shot and the shot list in a few lines, then build it without asking me anything else. Give me the HTML file and a 20-second MP4 captured with the ?render mode.
</start>
````
