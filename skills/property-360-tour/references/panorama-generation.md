# How the panoramas are made, and how to tune it

## The render (guides.py)

For each tour point a ray is cast per pixel of an equirectangular image against the walls (with holes for openings),
floor, ceiling, door leaves and boxes of `home.json`. Rays continue through `door` and `open` openings, so the next
room is visible where it really is. Surfaces get plain colours close to the real finishes, soft edge lines, floor
tile joints (they give the model the perspective), simple shading by wall direction.

Outputs per point: `guideNN.png` (rolled so the image edge is on the plainest wall), `rollNN.txt`, `sidNN.npy`
(surface ids, unrolled), `dirsNN.txt` (prompt text: what is at 0/25/50/75% and each labelled feature left to right,
with distance; things in other rooms are tagged), `risksNN.txt` (labelled features under about 2% of the width, and
doorways seen at a grazing angle), each line `X0 X1 Y0 Y1 | label | why`, in percent of the *final* panorama.

Make two sets: 2048 wide for the image model, 4096 wide for zoomed checks and fixes.

## The call (render_pano.py)

- Image 1: the render, padded to 21:9 with its own wrap-around on both sides so the model paints across the seam.
  Then up to five real photos.
- Prompt: an image-to-image *edit* ("turn this render into a photograph, keep its geometry"), rules about door leaves
  and blocks, the `dirs` list, the room's `finish`, the state of the home, the point's `note`.
- Model output is cut back to 2:1, the first 3.5% blended with what was painted past the right edge, resized to
  4096×2048, and rolled back so the centre looks up the plan.
- `--size 1K` to try a wording cheaply; judge layout only at that size.

Tuning, in order of effect:
1. Fix the render (a missing box or leaf) rather than the wording.
2. Change which photos are `refs` and their order.
3. One precise sentence in the point's `note` about this view ("The far end wall is plain cream with an air
   conditioner; there are no cabinets on it"). Positive statements work better than lists of prohibitions.
4. Move the tour point.
General prompt changes come last and need a re-check of points that were already fine.

## Checking (check_pano.py)

`overlay` for the whole image, `risks` for every small feature, `seam` for the join, `zoom` for any box,
`compare` for before/after. `home.py locate` / `span` give the percent position of any plan point or wall stretch,
which is how to aim a zoom or a fix at a specific corner of the plan.

Two failure modes are easy to miss: a correct-looking object in the wrong place by its own width (compare with the
render, not with your expectation), and plain walls that have a fold, a ghost outline or a soft smear.

## Local fixes (fix_pano.py)

The panorama is rolled to centre the box; a 16:9 window around it goes to the model with the instruction, the same
window of the 4096 render (`--guide`, `--node`) and real photos of the spot (`--refs`). Only the box is pasted back,
feathered, tone-matched on a ring around it.

- Box: a little larger than the thing to change; include the floor contact when removing something.
- Window: default shows 2.4× the box (min 1100 px). For a small far target use `--context 1.3 --minw 800` so the
  target is 60+ px wide in the model's view.
- Instruction pattern: "Now it wrongly shows A. Correct is: B at …, C beside it … . D stays as it is."
- Chain fixes in one panorama sequentially (each reads the previous output); fixes in different panoramas in parallel.
- Removing a large object: no guide needed if the guide has nothing there, but it never hurts.
- Always look at a wider crop afterwards.

## Cost and credit

4K panorama ≈ $0.155; 1K trial ≈ $0.07; local fix (2K) ≈ $0.10; transcription ≈ $0.003.
`curl -s https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $OPENROUTER_API_KEY"` → total and used.
