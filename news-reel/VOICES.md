# Narration voices (ElevenLabs, Persian)

Rule (user, 2026-10-20): alternate gender every reel — one reel female, the next male —
and pick the voice whose tone fits the news.

| Voice | id | Gender | Fits |
|---|---|---|---|
| Niloofar | N7wuKHXQQ5fKd75noieq | female | business, tech, science, everyday services — clear, warm |
| Setareh | 8Ebkg5uUcbSbeqGucAoR | female | health, culture, art, food — soft, friendly |
| Hooman | XzieuK0bwYWT9Kl1LhLs | male | industry, policy, finance, automotive — confident, firm |
| Mahdi (clone) | gZb98rbX5NXaD96zWH4i | male | page-owner voice, special announcements |

Log the voice used in the reel's slot JSON (`reel.voice`) so the next reel switches gender.

## Motion style rule (all motion graphics: reels, logo motion, future videos)
Every motion graphic uses the full effects set:
- 3D: scene entrances with translateZ + rotateX, rotateY flips for icons/tiles/logos, rotateX tilts for cards. Give each scene its own `perspective` and do not use `preserve-3d` on scene containers (it slices intersecting planes).
- Glowing lights: neon text glow, pulsing drop-shadow glows, a diagonal light streak after each cut.
- Particles: bokeh layer behind the content, sparks in front (screen blend), and a radial spark burst at each scene cut.
- Neon-morphic cards: glass cards with a neon border glow (cyan, or orange as the accent) and inset highlights.
