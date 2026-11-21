# home.json

One file describes the property. Worked example: `examples/apartment-4/home.json`. Check with `home.py validate`.

## Coordinates

- Plan: metres, **x to the right, y down** (as on the sheet). Pick the orientation once (e.g. the main window wall is
  the top edge, y = 0).
- Heights: metres above the floor.
- Angles (`a` of a tour point): degrees, 0 = toward +x (right), 90 = toward +y (down the sheet), −90 = up.
- Panoramas: 4096×2048 equirectangular; the centre column looks toward −y (up the sheet); going right in the image
  turns clockwise on the plan. `home.py locate N X Y [Z]` converts a plan point to image percent.

## Top level

| key | meaning |
|---|---|
| `title`, `note` | shown in the tour; `note` is the sentence under the plan sheet (how it was made, what is estimated) |
| `measured` | true when sizes were measured; otherwise the sheet says "≈" |
| `ceiling`, `eye`, `tile`, `wall_thickness`, `leaf_height` | 2.8, 1.5, 0.8, 0.16, 2.05 by default |
| `style` | `state` ("empty" or "furnished"), `door_leaf` (how an interior door looks), `door_frame`, `window_view`, `through_legend` |
| `palette` | optional `"#rrggbb"` overrides for the plain render: `floor`, `joint`, `wall`, `base`, `ceiling`, `front`, `cab`, `counter`, `stone`, `island`, `wardrobe`, `niche`, `rad`, `fix`, `furn`, `slab`, `slab_dark`, `slab_floor`, `leaf`, `frame`, `glass_top`, `glass_low`. Set `floor`, `wall` and `front` to plain versions of the real colours: leftover render colour then does no harm |

## rooms

```json
{"id": "living", "name": "پذیرایی و نشیمن", "name_en": "living room with open kitchen",
 "poly": [[0, 0], [10, 0], [10, 3.6], ...],          // inner outline, any polygon, either winding
 "label": [5.6, 1.9], "label_tour": [6.0, 1.2],       // where the name sits on the draft / on the tour sheet (clear of tour points)
 "small": true,                                        // small type, no area line
 "slab": true,                                         // wet room: walls clad to the floor (uses slab colours)
 "finish": "An empty ... Floor: ... Walls: ... Ceiling: ...",   // English, for the prompt; only what is visible in this room
 "through": "the bathroom clad in dark grey and white stone-look slabs"}   // how it reads when seen through a doorway
```

A room without `poly` is a label only (an open kitchen or entrance that is part of a bigger room).
Rooms that are open to each other without any wall belong in **one** polygon; a wide opening in a wall is an
`openings` entry of kind `open`.

## openings, windows, panels

Each has two end points `a`, `b` lying on the wall line (within 0.3 m) of every room it belongs to.

```json
"openings": [{"a": [7.45, 6.4], "b": [8.45, 6.4], "kind": "front", "head": 2.1, "label": "the front door (closed, brown wood with carved panels)", "rooms": ["living"]},
             {"a": [7.0, 4.9], "b": [7.0, 5.7], "kind": "door", "label": "open door to the guest toilet", "rooms": ["living", "wc"]},
             {"a": [10, 2.4], "b": [10, 3.6], "kind": "open", "head": 2.45, "label": "the corridor opening", "rooms": ["living", "hall"]}],
"windows":  [{"a": [2.3, 0], "b": [4.0, 0], "sill": 0.95, "head": 2.3, "label": "a living-room window"},
             {"a": [0.55, 0], "b": [1.4, 0], "sill": 0.05, "head": 2.1, "label": "the glazed terrace door", "door": true}],
"panels":   [{"a": [13.1, 1.2], "b": [13.1, 2.3], "head": 2.6, "label": "a white built-in wardrobe (two tall doors)"}]
```

- `front`: drawn closed, solid. `door`: interior doorway, rays pass through; give it a `leaves` entry. `open`: no door.
- A glazed balcony door is a window with a low sill and `"door": true` (drawn as one leaf, grey on the plan).
- `panels` are flush fronts in a wall (built-in wardrobe doors).
- Labels are English and go into the prompt verbatim; put colour and material of that object here.

## leaves

`{"hinge": [6.84, 4.93], "tip": [6.06, 4.9]}` — an open door leaf from its hinge to its free edge, inside the room it
opens into, as the photos show it (usually folded back against a wall). One per interior door.

## boxes

`{"box": [x0, y0, x1, y1, z0, z1], "kind": "cab", "label": "kitchen base cabinets ...", "plan": "سینک و گاز"}`

- `kind` picks the plain colour: `cab` (white unit; top face drawn as counter when it is a base unit), `stone` (grey
  unit or panel), `island`, `wardrobe`, `niche` (back of an empty recess), `rad`, `fix` (white fixture or wall unit),
  `col` (column or pier: wall colour, black on the plan), `furn` (furniture in furnished homes).
- `label` (English) makes it a named feature in the prompt and in the risk list. Leave it out for sub-parts.
- `plan` (Persian) draws its footprint on the plan with that name. `rad` and `col` are drawn automatically.
- Build composite things from several boxes: base run + upper run + tall column + backsplash strip + end panel.
  A flat thing on the floor (squat toilet pan, shower tray) is a box 3 cm high.
- `plan_marks`: `{"rect": [x0, y0, x1, y1], "name": "دوش"}` for plan-only marks with no 3D box.

`slab_dark`: `[x0, y0, x1, y1]` boxes in plan; any slab-room wall point inside one is drawn dark (feature walls).

## nodes

```json
{"n": 3, "room": "living", "x": 7.4, "y": 2.5, "a": 180, "cap": "پذیرایی، رو به آشپزخانه",
 "refs": ["p49", "n14", "k5"], "note": "The far end wall is plain ... no cabinets on it."}
```

`a` is the heading shown on arrival. `refs` are photo file names (without `.jpg`) in the photos folder, best first.
`note` is appended to the prompt for this point only: use it for what the render cannot express, in plain positive
statements about this view. Numbering follows the walk from the front door.

## Draft-only

`steps`: `{"at": [x, y], "mark": "۱", "text": "در ورودی"}` — the walk order.
`questions`: `{"a": [x, y], "b": [x, y], "mark": "۱", "text": "..."}` — an assumed wall (drawn red) and its question.
`dims`: `{"a": [x, y], "b": [x, y]}` — dimension lines (length is computed). `outside`: `{"rect": [x, y, w, h], "name": "تراس"}`.

## Furnished homes

Set `style.state` to `"furnished"` and add the main furniture as `furn` boxes with labels ("a grey three-seat sofa").
The prompt then asks for furniture only where the blocks are, styled from the photos. This mode has had less testing
than empty homes: expect more duplicates and run the privacy pass (lessons E5).
