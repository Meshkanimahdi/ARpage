"""The confirmed plan as a 3D scene: walls with openings, windows, cabinets, and the 360 points.

Everything the guides, the viewer data and the panorama prompts need comes from here, so they cannot disagree.
Plan coordinates in metres: x to the right, y down (the living room's window wall is y = 0). Heights are estimates.
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan  # noqa: E402

CEIL = 2.8
ROOMS = {key: dict(name=name, poly=poly) for key, name, poly, _ in plan.ROOMS if poly}
ROOM_EN = {"living": "living room with open kitchen", "wc": "guest toilet", "hall": "corridor", "bath": "bathroom",
           "bed1": "bedroom 1", "bed2": "bedroom 2"}

# openings: endpoints on the plan, kind, head height, English label for the prompt
OPENINGS = [
    dict(a=(7.45, 6.4), b=(8.45, 6.4), kind="front", head=2.1, label="the front door (closed, brown wood with carved panels)", rooms=["living"]),
    dict(a=(7.0, 4.9), b=(7.0, 5.7), kind="door", head=2.1, label="open door to the guest toilet", rooms=["living", "wc"]),
    dict(a=(10.25, 2.4), b=(11.05, 2.4), kind="door", head=2.1, label="open door to the bathroom", rooms=["hall", "bath"]),
    dict(a=(10.15, 3.6), b=(11.05, 3.6), kind="door", head=2.1, label="open door to bedroom 1", rooms=["hall", "bed1"]),
    dict(a=(12.3, 2.55), b=(12.3, 3.45), kind="door", head=2.1, label="open door to bedroom 2", rooms=["hall", "bed2"]),
    dict(a=(10.0, 2.4), b=(10.0, 3.6), kind="open", head=2.45, label="the corridor opening", rooms=["living", "hall"]),
]
# glazing: sill and head; the terrace door is a full-height glazed door
WINDOWS = [
    dict(a=(0.55, 0), b=(1.4, 0), sill=0.05, head=2.1, label="the glazed terrace door"),
    dict(a=(2.3, 0), b=(4.0, 0), sill=0.95, head=2.3, label="a living-room window"),
    dict(a=(5.0, 0), b=(6.7, 0), sill=0.95, head=2.3, label="a living-room window"),
    dict(a=(7.6, 0), b=(9.3, 0), sill=0.95, head=2.3, label="a living-room window"),
    dict(a=(12.9, 6.0), b=(12.9, 7.2), sill=1.0, head=2.25, label="the bedroom window (frosted, onto a light well)"),
    dict(a=(13.4, 5.6), b=(14.8, 5.6), sill=1.0, head=2.25, label="the bedroom window (frosted, onto a light well)"),
]
# flush wardrobe fronts set into a wall
PANELS = [dict(a=(13.1, 1.2), b=(13.1, 2.3), head=2.6, label="a white built-in wardrobe (two tall doors, black handles)")]
# boxes: x0, y0, x1, y1, z0, z1, kind, label
BOXES = [
    # kitchen, U-shaped in its recess (x 0..4.65, y 4.7..6.0). "cab" is white, "stone" is grey stone-look
    (0.65, 5.4, 4.05, 6.0, 0, 0.9, "cab", "kitchen base cabinets on the back wall (white doors, cream counter: sink on the left part, gas hob on the right part)"),
    (2.85, 5.65, 4.05, 6.0, 1.45, 2.35, "cab", "white upper cabinets above the sink"),
    (2.4, 5.4, 2.85, 6.0, 0, 2.35, "stone", "a tall grey stone-look column between the sink part and the hob part"),
    (0.65, 5.65, 2.4, 6.0, 1.75, 2.35, "stone", "grey stone-look upper cabinets above the hob"),
    (0.65, 5.6, 2.4, 6.0, 1.45, 1.75, "cab", None),
    (0.65, 5.97, 4.05, 6.0, 0.9, 1.45, "stone", None),                       # backsplash
    (4.05, 4.7, 4.65, 5.4, 0, 0.9, "cab", "the end of the kitchen counter beside the radiator wall (white end panel)"),
    (4.05, 4.7, 4.65, 4.75, 0.9, 2.35, "stone", None),                        # tall grey end panel
    (4.3, 4.75, 4.65, 5.65, 1.35, 2.35, "cab", "white wall cabinets above the counter (flat doors with black handles; cabinets, not a door)"),
    (0.0, 5.4, 0.65, 6.0, 0, 2.35, "cab", None),                              # corner unit
    (0.0, 4.55, 0.65, 5.4, 1.75, 2.35, "cab", "the tall white fridge unit: an open fridge niche framed in grey, white cabinets above"),
    (0.0, 4.55, 0.08, 5.4, 0, 1.75, "niche", None),                           # back of the empty fridge niche
    (0.0, 4.5, 0.7, 4.55, 0, 2.4, "stone", None),                             # its grey end panel
    (0.95, 3.55, 2.45, 4.35, 0.84, 0.9, "island", "the kitchen island (grey stone-look top and end panel, white drawers under its far half)"),
    (2.4, 3.55, 2.45, 4.35, 0, 0.84, "island", None),
    (0.95, 3.6, 1.75, 4.3, 0, 0.84, "cab", None),
    (12.3, 3.86, 12.84, 5.6, 0, 2.6, "wardrobe", "a white built-in wardrobe (tall flat doors, black handles)"),
    (8.68, 4.9, 8.8, 6.1, 0.15, 0.75, "rad", "a white panel radiator"),
    (8.75, 4.9, 8.8, 5.1, 1.4, 1.66, "fix", "a white video intercom handset on the wall"),
    (4.8, 4.58, 6.0, 4.7, 0.15, 0.75, "rad", "a white panel radiator"),
    (0.0, 0.75, 0.12, 2.0, 0.15, 0.75, "rad", "a white panel radiator"),
    (0.0, 2.4, 0.22, 3.6, 2.0, 2.32, "fix", "a white split air conditioner high on the wall"),
    (7.0, 6.0, 7.04, 6.3, 1.45, 1.72, "fix", "a small fuse-box cover on the wall"),
    (10.26, 0.26, 10.86, 0.7, 0, 0.85, "fix", "a white pedestal sink"),
    (11.5, 0.3, 12.04, 0.95, 0, 0.78, "fix", "a white one-piece toilet"),
    (5.0, 5.9, 5.5, 6.34, 0.35, 0.85, "fix", "a small white vanity sink with a white-framed mirror above"),
    (5.0, 5.2, 5.5, 5.62, 0, 0.03, "fix", "a white squat toilet pan set flush into the floor"),
    (4.8, 5.24, 4.92, 5.58, 1.15, 1.5, "fix", "a white plastic flush tank high on the wall, a thin pipe down to the squat toilet"),
    (9.62, 0, 10.0, 0.36, 0, CEIL, "col", None), (0, 0, 0.34, 0.4, 0, CEIL, "col", None),
]
# door leaves standing open inside their rooms: hinge, tip
LEAVES = [((6.84, 4.93), (6.06, 4.9)),     # guest toilet, against its side wall
          ((10.27, 2.24), (10.22, 1.46)),  # bathroom, against its side wall
          ((10.17, 3.76), (10.0, 4.64)),   # bedroom 1
          ((12.3, 2.57), (13.18, 2.47))]   # bedroom 2, against the wall of its short entry
LEAF_H = 2.05
# wet rooms are clad in slabs: white marble-look, with dark grey stone-look where a wall point falls in one of these boxes
SLAB_ROOMS = ("wc", "bath")
DARK = [(11.9, 0.0, 12.3, 2.4),      # bathroom: the wall behind the toilet and the shower
        (10.0, 0.0, 10.95, 0.4),     # bathroom: the strip behind the sink
        (4.7, 6.2, 5.7, 6.6)]        # guest toilet: the panel behind the vanity
# 360 points: a = heading shown first (0 right, 90 down on the plan); refs = photos (pNN) or video frames (vNN = second)
NODES = [
    dict(n=1, room="living", x=7.9, y=5.7, a=-90, cap="ورودی، رو به پنجره‌ها", refs=["n04", "n03", "n02", "n05", "p49"],
         note="The camera stands just inside the entrance: the dark brown front door is very close and fills the place the render "
              "shows in brown; the plain cream wall with the radiator and the intercom is very close on the other side. The radiator "
              "is one complete panel, as long as its block in the render."),
    dict(n=2, room="wc", x=5.95, y=5.6, a=180, cap="سرویس مهمان", refs=["p58", "p55", "p57", "p56"],
         note="This small room has no window and no radiator. The squat toilet pan is in the floor where the render shows the flat "
              "white rectangle, the flush tank on the wall above it; the vanity stands only in front of the dark grey panel."),
    dict(n=3, room="living", x=7.4, y=2.5, a=180, cap="پذیرایی، رو به آشپزخانه", refs=["p49", "n14", "k5", "k3", "v17"],
         note="The far end wall of this long room is a plain cream wall with an air conditioner high up, a radiator below and the "
              "glazed terrace door beside it: there are NO kitchen cabinets on that end wall. The kitchen stands to the side, in a "
              "recess behind the cream wall with the radiator, and is seen from the side and only partly: the tall white fridge "
              "unit at the far corner, a piece of the cabinet row, and the island in front, exactly as small as their blocks in "
              "the render. All three windows are on the one long wall; that wall is one flat wall with one smooth baseboard, no "
              "fold or joint in it. The corridor ends in an open white doorway to a cream room, not in a brown door."),
    dict(n=4, room="living", x=4.6, y=2.2, a=0, cap="نشیمن، رو به راهرو و ورودی", refs=["n14", "k1", "k4", "n15", "n06"],
         note="There is no door and no doorway in the cream wall with the radiator, and no intercom on it: the intercom hangs only "
              "where the render shows its small white block. The terrace door is one glazed white uPVC door, closed, with no "
              "second leaf. The corridor ends in an open white doorway to a cream room, not in a brown door; no brown door is "
              "visible from here."),
    dict(n=5, room="living", x=3.3, y=4.1, a=120, cap="آشپزخانه", refs=["k1", "k5", "k3", "k4", "k2"],
         note="The camera stands at the open side of the U-shaped kitchen, next to the island. There is no door and no doorway "
              "among or beside the kitchen cabinets: every tall white panel there is a cabinet. The cream wall next to the kitchen "
              "carries only a radiator. The corridor ends in an open white doorway to a cream room; no brown door is visible "
              "from here."),
    dict(n=6, room="hall", x=11.2, y=3.0, a=0, cap="راهرو", refs=["n10", "n11", "p38", "n08"],
         note="Three doorways open off this corridor; what is behind each one is fixed by the render and the list above. Only the "
              "doorway whose inside is dark grey and pale grey in the render is the bathroom (stone slabs, pedestal sink). The other "
              "two are empty bedrooms with cream painted walls: no tiles, no sink. Between the doorways the corridor walls are plain "
              "cream paint: no niche, no extra frame, no extra door. Through the wide opening the long living room is seen, and at "
              "its far end the kitchen island and the tall fridge unit, as small as the render shows them."),
    dict(n=7, room="bath", x=11.0, y=1.45, a=-90, cap="حمام و سرویس", refs=["p38", "p50", "p46", "p37", "p47"],
         note="All four walls of this room are clad in slabs from floor to ceiling; there is no painted wall here. One floor drain."),
    dict(n=8, room="bed1", x=10.9, y=5.7, a=90, cap="اتاق خواب ۱", refs=["p07", "p19", "p18", "p03", "p17"]),
    dict(n=9, room="bed2", x=14.8, y=3.4, a=90, cap="اتاق خواب ۲", refs=["p26", "p24", "p39", "p22", "p21", "p28"]),
]
for _p in NODES:
    _p["h"] = 1.5

FINISH = {
    "living": ("An empty, unfurnished new apartment. Floor: glossy large-format light cream marble-look porcelain tiles (about 80 cm) "
               "with thin joints and soft reflections. Walls: plain cream-white paint, white baseboard. Ceiling: white gypsum with a "
               "rectangular recessed tray and small round recessed spotlights. White uPVC windows with a hazy low-rise city skyline in "
               "daylight. The kitchen is U-shaped: white base cabinets with black handles and a cream counter, a grey stone-look "
               "backsplash, white upper cabinets over the sink, a tall grey stone-look column, grey stone-look upper cabinets over the "
               "gas hob, and a tall white fridge unit with an empty niche framed in grey; the island has a grey stone-look top and "
               "end panel and white drawers. Interior doors: white, classic raised panels, brass handles."),
    "wc": ("A small guest toilet. Walls clad in large white marble-look slabs with grey veins (pale grey in the render), one dark "
           "grey stone-look panel behind a small white wall-hung vanity sink with a white-framed mirror; a squat toilet set in the "
           "light grey floor tiles with a white flush tank on the wall above it and a chrome bidet tap; white ceiling with one "
           "recessed light and a small vent."),
    "hall": ("A short empty corridor. Same glossy light cream floor tiles, plain cream-white walls, white baseboard, white doors with "
             "classic raised panels and brass handles in white frames, white ceiling with one recessed spotlight."),
    "bath": ("A bathroom. Walls clad in large slabs: where the render is dark grey they are dark grey stone-look slabs (the wall "
             "behind the toilet and the shower, and the strip behind the sink); where it is pale grey they are white marble-look "
             "slabs with grey veins. Light grey floor tiles with a floor drain; a white pedestal sink, a white one-piece toilet, a "
             "chrome shower set on the dark grey wall with no enclosure; white ceiling with a recessed light and a vent grille."),
    "bed1": ("An empty bedroom. Slightly matte light cream floor tiles, plain cream-white walls, white baseboard, a white built-in "
             "wardrobe with tall flat doors and black handles, a white two-pane window with frosted-looking glass onto a light well "
             "(no view), a white radiator under the window, white ceiling with two small recessed spotlights."),
    "bed2": ("An empty bedroom. Slightly matte light cream floor tiles, plain cream-white walls, white baseboard, a white built-in "
             "wardrobe with two tall flat doors and black handles, a white two-pane window with frosted-looking glass onto a light "
             "well (no view), a white radiator under the window, white ceiling with small recessed spotlights."),
}


THROUGH = {"living": "the bright living room with glossy cream floor", "wc": "the guest toilet clad in white marble-look slabs",
           "hall": "the corridor with cream walls", "bath": "the bathroom clad in dark grey and white stone-look slabs",
           "bed1": "bedroom 1, an empty cream-walled room", "bed2": "bedroom 2, an empty cream-walled room"}


def room_at(x, y):
    for key, r in ROOMS.items():
        if inside(r["poly"], x, y):
            return key
    return None


def segments():
    """Every wall as a segment with its holes: (ax, ay, bx, by, room, [(s0, s1, z0, z1, kind, label)])."""
    out = []
    for key, r in ROOMS.items():
        P = r["poly"]
        for i in range(len(P)):
            (ax, ay), (bx, by) = P[i], P[(i + 1) % len(P)]
            L = math.hypot(bx - ax, by - ay)
            ux, uy = (bx - ax) / L, (by - ay) / L
            holes = []
            for o in OPENINGS + WINDOWS + PANELS:
                (px, py), (qx, qy) = o["a"], o["b"]
                # same direction, close to this wall line, overlapping its span
                if abs((qx - px) * uy - (qy - py) * ux) > 1e-6:
                    continue
                if abs((px - ax) * uy - (py - ay) * ux) > 0.3:
                    continue
                s0, s1 = sorted((((px - ax) * ux + (py - ay) * uy) / L, ((qx - ax) * ux + (qy - ay) * uy) / L))
                if s1 <= 0.001 or s0 >= 0.999:
                    continue
                kind = o.get("kind", "window" if "sill" in o else "panel")
                holes.append((max(0, s0), min(1, s1), o.get("sill", 0), o["head"], kind, o["label"]))
            out.append((ax, ay, bx, by, key, holes))
    return out


def inside(poly, x, y):
    c = False
    for i in range(len(poly)):
        (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
            c = not c
    return c


def sight(ax, ay, bx, by, margin=0.12):
    """True when nothing solid stands between two floor points: every sample lies inside a room, off the tall boxes."""
    n = int(math.hypot(bx - ax, by - ay) / 0.05) + 2
    for i in range(n + 1):
        x, y = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
        if not any(inside(r["poly"], x, y) for r in ROOMS.values()):
            return False
        if any(b[0] - margin < x < b[2] + margin and b[1] - margin < y < b[3] + margin and b[5] > 1.0 and b[6] != "col" for b in BOXES):
            return False
    return True


def links():
    """Where each point can go: another point in the same room in plain sight, or the room behind a door (ring at the door)."""
    out = {}
    for a in NODES:
        ls = []
        for b in NODES:
            if b is a:
                continue
            if a["room"] == b["room"] and sight(a["x"], a["y"], b["x"], b["y"]):
                ls.append(dict(n=b["n"], x=b["x"], y=b["y"]))
                continue
            for o in OPENINGS:
                if a["room"] in o["rooms"] and b["room"] in o["rooms"] and a["room"] != b["room"]:
                    mx, my = (o["a"][0] + o["b"][0]) / 2, (o["a"][1] + o["b"][1]) / 2
                    d = math.hypot(a["x"] - mx, a["y"] - my)
                    rx, ry = mx + (a["x"] - mx) / d * 0.45, my + (a["y"] - my) / d * 0.45
                    if sight(a["x"], a["y"], rx, ry):
                        # the nearest point of that room stands for the room
                        near = min((q for q in NODES if q["room"] == b["room"]), key=lambda q: math.hypot(q["x"] - mx, q["y"] - my))
                        if near is b:
                            ls.append(dict(n=b["n"], x=round(rx, 2), y=round(ry, 2), door=True))
        out[a["n"]] = ls
    return out


if __name__ == "__main__":
    import json
    markup, total = plan.svg(final=True)
    data = dict(CEIL=CEIL, ROOMS=[dict(id=k, name=r["name"], poly=r["poly"]) for k, r in ROOMS.items()],
                NODES=[{k: v for k, v in p.items() if k != "refs"} for p in NODES], LINKS=links(),
                DOORS=[dict(a=o["a"], b=o["b"], kind=o["kind"]) for o in OPENINGS],
                TOTAL=round(total), PLAN_SVG=markup)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "home.js")
    open(out, "w", encoding="utf-8").write("// generated by tools/scene.py from the confirmed plan (metres; x right, y down)\nwindow.HOME = "
                                           + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n")
    for n, ls in data["LINKS"].items():
        print(n, "->", [(l["n"], "door" if l.get("door") else "") for l in ls])
