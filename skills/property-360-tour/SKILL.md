---
name: property-360-tour
description: Turn a property owner's phone photos and walk-through video into (1) an accurate, owner-confirmed 2D floor plan and (2) a Street-View-style 360° teleport virtual tour built on that plan, with AI-rendered panoramas that are checked against the plan and corrected. Use this skill whenever the user sends or mentions photos/video of an apartment, house, villa, office or shop and wants a floor plan, a 2D plan, a 360 tour, a virtual tour, a walkable tour, panoramas, or "like Google Street View inside the home" — including Persian requests such as «پلان دوبعدی», «تور ۳۶۰», «تور مجازی», «تور تلپورت», «فایل جدید / خونه جدید برات میفرستم» — and also when the user reports errors in an existing plan or tour made this way and wants them root-caused and fixed, or wants a cost estimate or a capture checklist for such a tour.
---

# Property plan + 360° tour from photos and video

## What this produces and why it is built this way

Input: ordinary phone photos (20–60) and, ideally, one continuous narrated walk-through video.
Output: a confirmed 2D floor plan (SVG/PNG) and a 360° teleport tour (one HTML file) whose panoramas are AI-rendered.

The image model can paint a convincing room but it cannot be trusted with *where things are*. Left alone it mirrors
rooms, invents doors, moves kitchens. So the pipeline keeps geometry and appearance apart:

```
photos + video + narration ──► home.json (the plan, in metres)  ──► owner confirms the plan
                                      │
                                      ├─► plan.svg
                                      ├─► plain 3D render of each tour point (ray-cast, exact)
                                      │        │
real photos (appearance only) ────────┴────────┴─► image model: "turn this render into a photo"
                                                          │
                                   check against the render, zoom into risk spots, fix locally
                                                          │
                                                     tour viewer
```

`home.json` is the single source of truth: plan drawing, 3D renders, prompt text, tour links and minimap all come from
it, so they cannot disagree. Every error in a finished tour is therefore one of exactly three kinds, and the first job
when something is wrong is to decide which:

1. **Plan error** – home.json is wrong (a wall, recess, door or fixture is not where the real one is). Fix home.json,
   re-render every point that sees the changed area.
2. **Render error** – home.json is right but the image model painted something else. Fix that spot locally.
3. **Fix residue** – an earlier local fix left a ghost, a blur or a mismatch. Fix it again, then look at the neighbours.

`references/lessons.md` is the record of every failure met so far, with root cause and remedy. Read it before starting
a property; add to it whenever the owner reports something new. That file is how this skill gets better.

## Before starting

- Reply in the user's language (for Persian: plain wording, few technical terms). File contents stay English except
  the on-screen Persian labels.
- Tools: Python with `numpy`, `opencv-python`, `pillow`; `ffmpeg`; Node with Playwright for PNG export and the browser
  test. Image generation and transcription go through OpenRouter: `OPENROUTER_API_KEY` must be set. Default image model
  is `google/gemini-3.1-flash-image` (`IMAGE_MODEL` overrides); model names change, so if a call fails with an unknown
  model, look up the current image-capable model rather than guessing.
- **Money needs the owner's approval, every time.** Nothing that costs money runs without it:
  1. Before the first paid call of a project, give an estimate (references/costs.md) and wait for a clear yes.
  2. Before every further paid round (re-renders, a batch of fixes, second candidates), say what it is for and what it
     will cost, and wait for a yes. "Start", "do your best" or "fix it" approve the work, not unlimited spending.
  3. Stop and ask as soon as a project's spend would pass the approved amount.
  4. After every paid round, report what it cost and the running total. Never let the owner find the total by asking.
  5. Try a new method on one or two points at 1K first ($0.07 each), never on the whole tour at 4K.
  Reference prices: about $0.15 per 4K panorama, $0.10 per local fix, well under a cent for transcription; a 9-point
  home costs $1.5–2.5 in images when the plan is right first time and $5–9 when it is not. Check the remaining credit
  (`GET https://openrouter.ai/api/v1/credits`) before asking for approval, and say if it will not cover the job.
- Work in a per-property folder: `input/photos`, `input/frames`, `guides`, `guides4k`, `work` (candidates and checks),
  `tour/panos`. Keep `home.json` at its root.
- Privacy: the photos show the inside of someone's home. Do not commit panoramas or source photos to a public
  repository, do not send them anywhere but the image model, and scan results for people, reflections of the
  photographer, personal photographs and documents.

All scripts are in `scripts/` and print usage when run without arguments.

## Phase 1 — Intake: make sure the evidence is complete

Wrong plans came from missing evidence more often than from bad reasoning. So before drawing anything:

1. Collect everything. If the user uploads in batches, acknowledge each batch with a count and wait for their "done".
   Files that arrive while you are still working may not be saved: after every batch, list the folder and compare the
   count with what was sent; ask again for anything missing rather than working from memory of an image you saw.
2. `media.py convert` numbers the photos in the order taken (p01, p02 …). The order is evidence: people start at the
   front door and walk on. `media.py frames --every 2` cuts the video; `media.py transcribe` writes down the narration
   with timestamps (the narration says what is left, right, straight ahead, and how many rooms there are).
3. `media.py sheet` makes labelled contact sheets. Read all of them. Build a table: photo → room → which walls it shows.
4. **Coverage check.** For every room list each wall and whether at least one photo or frame shows it *including both
   of its corners*. For every doorway: is there a view through it from each side? For the main room: is there a view
   from each end toward the other? Anything uncovered goes to the user as a request **now**
   (see `references/capture-guide.md` for the checklist to send). An uncovered wall is where the next plan error is.

## Phase 2 — The plan (gate: the owner confirms it)

Read `references/plan-from-media.md` for the method. In short: fix the entrance and the walk order from the video,
place rooms by the narration's left/right/ahead, size them by counting floor tiles and by door widths, then go wall by
wall and write `home.json` (format: `references/home-schema.md`, worked example: `examples/apartment-4/home.json`).

Rules that exist because breaking them cost a full redo:

- **Never assume a wall is straight because it looks straight from one end.** A recess, a pier or a chamfer seen
  end-on looks like a flat wall. A wall counts as known only when a photo shows it at an angle with both corners.
- **Handedness.** Check left/right against the video and narration, not against a single photo. A mirrored plan looks
  perfectly reasonable on paper.
- **Put every assumption in `questions`** (with the wall segment it concerns). `plan.py` draws them in red on the
  draft. Ask them in chat as numbered questions. Do not choose silently and hope.
- State plainly which evidence each part came from (narration / video / photos); owners ask.

Then: `home.py validate` → `plan.py HOME.json plan_draft.svg` → `svg2png.js` → send the PNG with the questions.
**Stop here until the owner says the plan is right.** Corrections come back as marked-up screenshots: apply, re-send.
Rendering before confirmation is how money is wasted; one wrong recess meant re-rendering five panoramas.

## Phase 3 — The 3D scene

Still in `home.json`, add what the renders need (details in `references/home-schema.md`):

- `boxes` for everything with volume that a photo shows: cabinets (model a U- or L-shaped kitchen leg by leg, tall
  units, the fridge niche, the island), wardrobes, radiators, sanitary fixtures, columns and piers, wall units like an
  intercom or air conditioner. A thing that is not modelled will be invented somewhere else.
- `leaves`: every interior door standing open, where the photos show it. Unmodelled leaves get invented, usually in
  the wrong doorway.
- Wet rooms: `"slab": true` and `slab_dark` boxes for dark cladding, so they read as tiled when seen through a door.
- `nodes` (tour points). One per room; two to four in a long main room; one at the mouth of an open kitchen, not
  inside the aisle. Keep 0.6 m or more from walls. Prefer positions from which the room's important features are seen
  square-on rather than along the wall. For each: `refs` = 4–5 photos that show what this point looks at, best first
  (video frames are fine), and a `note` only for what the render cannot say.
- `finish` per room: materials and colours as seen in the photos. Mention only what is visible *in that room*: a line
  about "the brown front door" in the living-room text produced brown doors at the end of the corridor.

`home.py validate` must report 0 errors (every opening on its walls, every point inside its room and reachable).

## Phase 4 — Renders, prompts, and the first check

```
python3 scripts/guides.py HOME.json guides 2048      # what the image model gets
python3 scripts/guides.py HOME.json guides4k 4096    # what fix_pano zooms into
```

Look at a sheet of the guides before spending anything: does each one look like the place from that spot? Compare
with a real photo taken near the point. A guide that looks wrong will not turn into a photo that looks right.
Read each `dirsNN.txt` (the prompt's "what stands where") and `risksNN.txt` (see Phase 5).

Render every point (`render_pano.py`, 4K, in parallel; `--size 1K` is enough to try a prompt idea for half the price).
For the points that matter most — the main room — render two candidates and keep the better one; a second candidate
is cheaper than two rounds of fixes.

## Phase 5 — Verify every panorama, then fix

Do this for every point, every time. The errors the owner later found were all visible in these checks, or would have
been if the check had been run on that spot.

1. `check_pano.py overlay` — the plan's edges in red over the photo. Corners, door frames, windows and cabinet blocks
   should sit under the lines. A whole-image offset means the model turned or reframed: re-render.
2. `check_pano.py risks` — a zoomed pair for every feature that is far, narrow or grazing. **This is where the model
   lies**: a window painted on a distant end wall, a terrace door merged into a pier, a fridge unit turned into an
   oven. Look at each pair; the two halves must show the same things in the same places.
3. `check_pano.py seam` — the stretch where the model's two edges met: no step in the ceiling, no half object.
4. Scan the full-size image for: doors, doorways, windows or fixtures the render does not have; duplicates (a second
   island, a second radiator); door leaves where none is modelled; folds or vertical lines in long plain walls;
   people, reflections, text; a different door or floor than the neighbouring points show.
5. Compare with the real photos of that view. Would the owner recognise it?

Decide per defect (plan error / render error / fix residue, as above):

- Much wrong, or geometry off → re-render (add one precise sentence to the point's `note`; do not pile on general
  warnings).
- One spot wrong → `fix_pano.py` with `--guide guides4k --node N` and `--refs` real photos of that spot. Get the box
  from `risksNN.txt` or `home.py span`. For something small and far, zoom the model in: `--context 1.3 --minw 800`.
  Say what is wrong now, what is really there, and what must stay. When it matters, run two candidates.
- After every fix: `check_pano.py compare` on the box **and** `check_pano.py zoom` on a wider box around it. Fixes
  leave ghosts just outside what you were looking at.

The same feature seen from several points must be checked from each of them; the owner walks through all of them.

## Phase 6 — Build, test, deliver

```
python3 scripts/build_tour.py HOME.json tour --standalone tour.html
node scripts/test_tour.js tour.html shots [--look N,X,Y]
```

The test visits every point on desktop and phone sizes; look at the screenshots, and use `--look` to view the spots
you fixed from inside the tour. Deliver the single HTML file (and publish it as an Artifact when that tool exists).

Report, briefly and honestly:
- what was made, and the link/file;
- that the panoramas are AI-rendered on the confirmed plan — layout follows the plan, small details (switches, veins
  in stone, the view outside) are invented;
- the assumptions still open (estimated sizes, any unanswered question);
- known imperfections you could not remove, with the point number;
- what it cost.

## Phase 7 — Feedback loop (how the tour and this skill improve)

When the owner marks errors on screenshots:

1. Save every marked image; restate the list of errors in your own words so they can correct your reading.
2. For each: find the root cause first and say which of the three kinds it is, with the evidence (the coordinates in
   the panorama, the photo that shows the truth). If they ask for root causes only, do not start fixing.
3. If more photos are needed, say exactly which views.
4. Fix at the right layer; re-check from every point that sees the spot; re-deliver with before/after crops.
5. **Record it**: add an entry to `references/lessons.md` (symptom → root cause → remedy → how to catch it earlier).
   If the remedy can be automated, change the script or the validation instead of adding prose.

## Scripts

| script | use |
|---|---|
| `media.py` | convert/number photos, cut video frames, contact sheets, transcribe narration |
| `home.py` | load `home.json`; `validate`, `links`, `locate`, `span` |
| `plan.py`, `svg2png.js` | draft plan (red = assumptions) and final plan |
| `guides.py` | plain 3D render per point + `dirs` (prompt) + `risks` (what to inspect) |
| `render_pano.py` | render → 4096×2048 panorama through the image model |
| `check_pano.py` | `overlay`, `risks`, `zoom`, `seam`, `compare` |
| `fix_pano.py` | repaint one box, guided by the render and real photos |
| `build_tour.py`, `test_tour.js` | assemble the viewer, pack one file, browser test |

## References

- `references/capture-guide.md` — what to ask the owner to shoot; the checklist to send them (Persian included).
- `references/plan-from-media.md` — deriving the plan: method, sizing, ambiguity checklist.
- `references/home-schema.md` — the `home.json` format, coordinates, kinds, palette, furnished homes.
- `references/panorama-generation.md` — how the render/prompt/seam/fix machinery works and how to tune it.
- `references/costs.md` — unit prices, cost of a typical project, what lowers it, optional photo services.
- `references/lessons.md` — every failure so far with root cause and remedy. Read first; append after each project.
