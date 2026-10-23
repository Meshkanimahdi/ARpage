# Worked example: prompt 089 → `news-reel/glass.html` (2026-10-23)

**Story:** Walmart unveiled Agent Gateway (21 Oct 2026). It is an MCP server where approved AI agents search
and buy, with per-agent profiles and spending limits; at the same time, Amazon blocks agents.
**Category:** UI (a platform launch). **Prompt:** `089-frame-by-frame-launch-video` (Apple-keynote glass sting).
**Why it won:** its chain "header → click → icon → menu bar → prompt box → answer page → card → two cards →
logo" maps onto the story one to one: the product, the launch, the agent request, the profile rules, the
payment safeguard, Open vs Blocked, and the question to the viewer.

## Allowed edits made
- changed: 1080x1080 → 1080x1920; coordinates re-laid for the tall frame (timing/size rule).
- changed: 12 s → 34.4 s. Each shot got a stretch range inside its existing drift or hold, so the narration
  fits and the entries and exits keep their speed (duration rule).
- changed: inputs → product "Agent Gateway", pill "Walmart", bag-and-sparkle mark, prompt «شیر و نون همیشگی
  این هفته رو بخر», page "پروفایل ایجنت" with key phrase «سقف خرج», cards "Open" / "Blocked", wordmark
  MESHKANI.PRO (topic slots).
- changed: "Mixkit Rising Forest" → ElevenLabs music at 124 BPM, delayed 0.2 s so its accent lands on the
  orbit cut; the prompt's SFX cues are kept (page standard).
- changed: 59.94 fps master → 30 fps reel_render (page standard).
- added: Persian narration (Niloofar, eleven_v4) and a frosted karaoke caption (page standard).
- kept: palette, Inter, every shot and its order, the hard cuts, blur-follows-speed, frosted glass,
  zoom-smear end card, the single frozen hold (logo disc), the banned list, and pure `seek(t)` with no
  `Math.random`.
