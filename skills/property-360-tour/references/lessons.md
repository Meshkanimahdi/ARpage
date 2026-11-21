# Lessons: what went wrong, why, and what now prevents it

This is the memory of the skill. Each entry: **symptom → root cause → remedy → how to catch it earlier**.
Append to it after every property (newest at the bottom of its section) and bump the changelog.
When a remedy can be enforced by a script, change the script and note it here.

Contents: A. Evidence · B. Plan · C. 3D scene and tour points · D. Rendering · E. Local fixes · F. Viewer ·
G. Working with the owner · H. Approaches that were tried and dropped · Changelog

## A. Evidence

**A1. Photos sent mid-task were lost.**
Uploads that arrive while a turn is running are shown but not saved as files. Later the plan was drawn without them.
→ Acknowledge each batch with a count, wait for "done", compare the folder listing with what was sent, ask for the
missing ones by description. Never use an image "from memory" as a render reference: it has to be a file.

**A2. The kitchen recess was invisible in the first photo set.**
No photo showed the corner where the radiator wall ends and the cabinets begin, so the wall was drawn straight.
The owner then sent 20 more photos and said the missing ones were "the cause of the other errors".
→ Coverage check in Phase 1: every wall with both corners, every doorway from both sides, the main room from both
ends. Ask for the gaps before drawing.

**A3. Sparse listing photos cannot be reconstructed automatically.**
Structure-from-motion needs heavy overlap; listing photos have almost none. Video registers (70–80% of frames) but
the automatic layout does not separate rooms.
→ The plan is derived by reasoning over narration + frames + photos. Do not retry photogrammetry unless the capture
changes (see H).

## B. Plan

**B1. Plan mirrored (kitchen and living room swapped).** (apartment 3)
The layout was guessed from photos alone; nothing fixed left versus right.
→ Take handedness from the video walk and the narration ("on the left as you enter"). Verify by naming, for one
video moment, what is on the left and right and checking the plan agrees.

**B2. A diagonal (chamfered) corner drawn as a square corner.** (apartment 4)
The angled face was visible but was reasoned away as a straight wall.
→ When a face looks angled in two different photos, it is angled. Put it in `questions` with a size estimate.

**B3. Kitchen drawn on the main wall line; in reality it sits in a recess beside the guest toilet and is U-shaped.**
(apartment 4)
From the entrance the wall and the cabinets line up and look like one plane; a tall grey panel was read as the end
of a straight run when it was the start of the side leg.
→ A wall is known only when seen at an angle with both corners. Cabinet runs: find the sink, the hob and the fridge
separately and ask which wall each is on. Only one photo, taken from inside the kitchen, settles the shape.

**B4. Narration says "three bedrooms", the media shows two.**
Unresolved; the plan went ahead with two and said so.
→ Any conflict between narration and images goes into `questions`.

**B5. Sizes.** All sizes come from tile counts (measure one tile against a door: usually 60 or 80 cm) and door widths
(interior 0.8–0.9 m, front 1.0 m). Errors of 10–15% are normal; say "estimated" on the sheet. One real measurement
(the length of the main room) rescales everything: ask for it.

## C. 3D scene and tour points

**C1. Things not modelled get invented elsewhere.** Door leaves appeared in wrong doorways, a wall-hung toilet
replaced a squat toilet, a black oven replaced a fridge niche.
→ Model every open door leaf, every fixture, and distinctive units (fridge niche, intercom, air conditioner).

**C2. A tour point inside the kitchen aisle gave a panorama that was mostly cabinet fronts**, and the model filled the
confusion with a doorway. → Stand at the mouth of the kitchen, 0.6 m+ from any front.

**C3. `finish` text leaks.** "Front door: brown wood" in the living-room text produced a brown door at the end of the
corridor in three points. → Per room, describe only what is visible in that room; put door colour in the front door's
own `label`.

**C4. Tour point closer than 0.4 m to a wall**: that wall fills a quarter of the panorama. `validate` warns.

## D. Rendering

**D1. Line-drawing guides: the lines appeared in the result** (black arcs across walls). → Shaded render, no outlines.

**D2. Flat colour-coded "map" guide: the model drew an ordinary wide-angle photo and ignored the projection.**
→ A plain shaded 3D render that already looks like an untextured version of the photo, plus an *edit* framing
("turn IMAGE 1 into a photograph, keep its geometry"). This was the change that made layouts hold.

**D3. Seam across a door or window**: the model paints the two image edges separately; whatever sits there breaks.
→ `guides.py` turns each render so its edge falls on the plainest wall and `render_pano.py` turns the result back.

**D4. Doorways listed in the prompt but not actually visible** (behind a wall, or at a grazing angle) were painted
as full doors on the nearest wall. → `guides.py` lists a doorway only when a ray reaches it and it is seen at more
than about 15°; grazing ones go to `risks`.

**D5. Fixtures of the next room painted in this room** (a toilet in the living room). → Anything seen through a
doorway is listed as "NOT in this room: inside the X, seen through the doorway".

**D6. Far, narrow or grazing features are where the model lies.** A window painted on an end wall 11 m away; a
terrace door merged into the corner pier; a cabinet turned into an appliance. They occupy a few dozen pixels of the
render and the model fills in "what rooms usually have".
→ `risksNN.txt` lists every such feature; `check_pano.py risks` zooms each; fix with `fix_pano.py --guide … --context
1.3 --minw 800` and a real photo of the spot.

**D7. Vertical fold in a long plain wall, with a kink in the baseboard.** The model built the wall from two flat
pieces. Not a stitching seam. → The prompt now says long walls are flat; still scan plain walls; re-render or fix.

**D8. Duplicates**: a second island, a second radiator, a pier between two windows. → Scan for anything the render
shows once and the photo shows twice.

**D9. Too many reference photos dilute the render.** 4–5 is the working number. Put first the photo that shows the
view this point faces.

**D10. Small inconsistencies between points remain** (door panel style, floor tone in a room seen from outside versus
inside). Not solved. Reduce by reusing the same reference photos for neighbouring points; tell the owner.

**D11. Invented view outside the windows** (a famous bridge once). → The prompt asks for hazy sky and indistinct
rooftops; check.

## E. Local fixes

**E1. Removing an object left a faint outline** (door frame ghost on the wall). → The prompt asks for no ghost; after
every fix zoom on a wider box than the one fixed.

**E2. A fix guided only by words put things in slightly wrong places** (pier too wide, covering the door beside it).
→ Always pass `--guide guides4k --node N`: the same crop of the render goes to the model as the layout to follow.

**E3. A fix that restores one thing can erase its neighbour** (removing a stray door leaf also removed the real
terrace door). → Say in the instruction what must stay; compare before/after.

**E4. Small target, large crop**: the model cannot draw a 30-pixel door. → Shrink the window (`--context`, `--minw`)
until the target is 60+ pixels wide in what the model sees.

**E5. Privacy pass** on furnished homes: a mirror showed the photographer, frames showed family photographs.
→ Scan every panorama; repaint with `fix_pano.py` ("plain mirror reflecting the opposite wall", "empty picture frames").

## F. Viewer

**F1. Thin dashed line where the panorama wraps around.** Anisotropic texture filtering smears across the u = 0/1
jump. → Removed from the viewer; do not re-enable.

**F2. `file://` pages cannot load neighbouring images** in some browsers → the standalone build inlines everything.
The address for a local server is `http://localhost:8000/…`, not `www.localhost.com`.

**F3. Rings on the floor are not enough to find doors.** → Each doorway carries a label with the next room's name.

## G. Working with the owner

- "The plan is fine except this" on a screenshot is the normal form of feedback: save the image, restate, root-cause.
- Owners care where the plan came from (video or photos). Say which evidence fixed which part.
- When asked to root-cause only, do not fix yet; they may be about to send the missing evidence.
- A reconstruction-style point cloud viewer was rejected outright ("terrible"); the Street-View feel of full
  panoramas with teleport is what is wanted.
- Do not commit home interiors to a public repository without asking.

- **Spending without asking.** On apartment 4 about $9.2 went on images (about $3 of it on method trials and second
  candidates) with no estimate up front and no question before each round; the owner found out only by asking and
  was rightly upset. "Start, show me your best" was read as approval of any spend. It is not. → SKILL.md "Money needs
  the owner's approval": estimate first, ask before every paid round, report spend after each, trial new methods on
  one or two points at 1K.

## H. Approaches tried and dropped

- **Photogrammetry / SfM from the photos** (pycolmap): too few overlaps; global mapper registers frames but puts them
  metres off. Usable only with a slow, overlapping video of every room and even then the room layout needs hand work.
- **Projecting the real photos onto the sketch model** and walking through it: holes and stretched textures; does not
  feel like a 360 tour.
- **Line guides and colour-coded maps** as model input: see D1, D2.
- **Rebuilding a whole panorama to fix one corner**: the corner comes out right and something else goes wrong. Fix
  locally.

## Changelog

- v1.1 — paid steps need the owner's approval each round; spend reported after each round (lesson G, last entry).

- v1.0 — first version, distilled from five properties (Airbnb flat, apartments 2–4). Apartment 4 is the worked
  example: plan confirmed after two corrections (chamfer, kitchen recess); tour accepted after three rounds of fixes,
  all of kinds D6/E1/E2.
