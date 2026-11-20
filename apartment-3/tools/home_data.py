"""The third apartment, as read from 26 photos and an 82-second walk-through video. Plan coordinates in metres:
x to the east, y to the south. Sizes are estimated (door widths about 0.8-0.9 m, floor tiles about 0.6 m); no
measurement was given. Running this file writes ../home.js.

Layout as seen: the front door opens into a wood-panelled vestibule with a small WC; past a curtain lies an open
space with the sitting area (sectional sofa by the big curtained window), a breakfast counter and the kitchen on
the window side; two fluted columns separate it from the formal living room (TV wall, two sofas); a corridor with an
arch runs from there to the two bedrooms and the bathroom.
"""
import json
import os

CEIL = 2.8

ROOMS = [
    dict(id="vest", name="ورودی", x0=0.0, y0=0.0, x1=1.6, y1=2.6),
    dict(id="wc", name="سرویس", x0=-1.3, y0=0.0, x1=0.0, y1=1.5),
    dict(id="family", name="نشیمن و پیشخوان", x0=1.6, y0=0.0, x1=6.4, y1=4.2),
    dict(id="kitchen", name="آشپزخانه", x0=1.6, y0=-3.0, x1=6.4, y1=0.0),
    dict(id="salon", name="پذیرایی", x0=1.6, y0=4.2, x1=6.4, y1=8.6),
    dict(id="hall", name="راهرو", x0=0.4, y0=2.6, x1=1.6, y1=10.6),
    dict(id="bed1", name="اتاق خواب ۱", x0=-3.2, y0=8.6, x1=0.4, y1=12.6),
    dict(id="bath", name="حمام", x0=0.4, y0=10.6, x1=2.4, y1=12.6),
    dict(id="bed2", name="اتاق خواب ۲", x0=1.6, y0=8.6, x1=4.8, y1=10.6),
]
# openings: wall line ("x" = along x at y=c, "y" = along y at x=c), span a0..a1
OPENINGS = [
    dict(axis="y", c=0.0, a0=0.5, a1=1.4, kind="front", head=2.1, rooms=["vest"]),
    dict(axis="y", c=0.0, a0=0.2, a1=0.9, kind="door", head=2.1, rooms=["vest", "wc"]),
    dict(axis="y", c=1.6, a0=0.6, a1=1.9, kind="open", head=2.4, rooms=["vest", "family"]),
    dict(axis="x", c=0.0, a0=2.6, a1=6.0, kind="open", head=2.3, rooms=["family", "kitchen"]),
    dict(axis="x", c=4.2, a0=2.2, a1=6.4, kind="open", head=2.6, rooms=["family", "salon"]),
    dict(axis="y", c=1.6, a0=4.4, a1=5.4, kind="open", head=2.6, rooms=["salon", "hall"]),
    dict(axis="y", c=1.6, a0=2.8, a1=4.0, kind="open", head=2.4, rooms=["family", "hall"]),
    dict(axis="y", c=0.4, a0=9.2, a1=10.0, kind="door", head=2.1, rooms=["hall", "bed1"]),
    dict(axis="x", c=10.6, a0=0.6, a1=1.4, kind="door", head=2.1, rooms=["hall", "bath"]),
    dict(axis="y", c=1.6, a0=9.7, a1=10.5, kind="door", head=2.1, rooms=["hall", "bed2"]),
]
WINDOWS = [
    dict(axis="y", c=6.4, a0=0.4, a1=3.8, sill=0.2, head=2.6, room="family"),
    dict(axis="x", c=-3.0, a0=2.4, a1=5.2, sill=0.9, head=2.3, room="kitchen"),
    dict(axis="x", c=12.6, a0=-2.8, a1=-0.6, sill=0.7, head=2.5, room="bed1"),
    dict(axis="y", c=4.8, a0=9.0, a1=10.2, sill=0.8, head=2.4, room="bed2"),
    dict(axis="x", c=12.6, a0=1.0, a1=1.6, sill=1.6, head=2.2, room="bath"),
]
FURNITURE = {
    "family": [(4.4, 0.3, 6.3, 1.2, 0, .8, "مبل ال"), (5.4, 1.2, 6.3, 3.6, 0, .8, ""), (4.2, 1.6, 5.2, 2.6, 0, .45, "میز"),
               (1.8, 3.4, 2.6, 4.1, 0, .9, "مبل"), (2.2, 0.0, 2.8, 2.0, 0, 1.05, "پیشخوان"), (6.0, 3.6, 6.35, 4.1, 0, .8, "بخاری")],
    "kitchen": [(1.7, -3.0, 6.3, -2.4, 0, .9, "کابینت"), (1.7, -3.0, 6.3, -2.65, 1.5, 2.3, ""), (1.7, -1.4, 2.4, -0.7, 0, 1.85, "یخچال"),
                (4.6, -1.6, 5.4, -0.8, 0, .75, "میز")],
    "salon": [(2.2, 8.0, 5.8, 8.6, 0, .5, "میز تلویزیون"), (1.7, 5.4, 2.5, 7.6, 0, .85, "کاناپه"), (5.5, 5.4, 6.3, 7.6, 0, .85, "کاناپه"),
              (3.0, 6.0, 3.8, 6.6, 0, .45, ""), (4.2, 6.6, 5.0, 7.2, 0, .45, ""), (1.7, 4.4, 2.5, 5.1, 0, .9, "مبل")],
    "vest": [(0.0, 1.6, 0.4, 2.2, 0, 1.9, "جالباسی")],
    "wc": [(-1.3, 0.1, -0.8, 0.6, 0, .8, "روشویی"), (-0.6, 0.8, 0.0, 1.4, 0, .4, "توالت")],
    "bed1": [(-2.0, 10.4, -0.2, 12.4, 0, .5, "تخت"), (-3.2, 8.7, -2.6, 11.0, 0, 2.6, "کمد")],
    "bed2": [(3.4, 8.7, 4.7, 10.5, 0, .5, "تخت"), (1.7, 8.6, 3.2, 9.1, 0, 2.6, "کمد")],
    "bath": [(0.5, 10.7, 1.0, 11.6, 0, .9, "سکو"), (1.8, 11.6, 2.4, 12.5, 0, 0.02, "دوش")],
}
# 360 points: a = view direction (0 east, 90 south), refs = photos of that space
NODES = [
    dict(n=1, room="vest", x=0.8, y=1.3, a=0, refs=[6, 7, 3], cap="ورودی، رو به نشیمن"),
    dict(n=2, room="wc", x=-0.7, y=0.9, a=180, refs=[8, 3, 7], cap="سرویس"),
    dict(n=3, room="family", x=3.2, y=2.0, a=0, refs=[1, 20, 12, 2, 9], cap="نشیمن، رو به پنجره"),
    dict(n=4, room="kitchen", x=3.8, y=-1.2, a=-90, refs=[4, 10, 1], cap="آشپزخانه"),
    dict(n=5, room="salon", x=4.0, y=6.6, a=90, refs=[14, 15, 11, 13, 16], cap="پذیرایی، رو به دیوار تلویزیون"),
    dict(n=6, room="hall", x=1.0, y=7.2, a=90, refs=[18, 13, 23], cap="راهرو"),
    dict(n=7, room="bed1", x=-1.4, y=9.6, a=90, refs=[19], cap="اتاق خواب ۱"),
    dict(n=8, room="bath", x=1.4, y=11.3, a=90, refs=[21, 24, 26], cap="حمام"),
    dict(n=9, room="bed2", x=2.4, y=9.9, a=0, refs=[22, 25], cap="اتاق خواب ۲"),
]
for p in NODES:
    p["h"] = 1.5


def _mirror():
    """The layout above was first drawn mirrored (north/south swapped); the photos show the kitchen on the right of
    the window and the formal room on its left. Flip y once so the plan matches the photos."""
    for r in ROOMS:
        r["y0"], r["y1"] = -r["y1"], -r["y0"]
    for o in OPENINGS + WINDOWS:
        if o["axis"] == "x":
            o["c"] = -o["c"]
        else:
            o["a0"], o["a1"] = -o["a1"], -o["a0"]
    for k, fs in FURNITURE.items():
        FURNITURE[k] = [(f[0], -f[3], f[2], -f[1]) + tuple(f[4:]) for f in fs]
    for p in NODES:
        p["y"], p["a"] = -p["y"], -p["a"]


_mirror()

if __name__ == "__main__":
    data = dict(CEIL=CEIL, ROOMS=ROOMS, OPENINGS=OPENINGS, WINDOWS=WINDOWS,
                FURNITURE={k: [list(f) for f in v] for k, v in FURNITURE.items()}, NODES=NODES)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "home.js")
    open(out, "w").write("// generated by tools/home_data.py (metres; x east, y south)\nwindow.HOME = "
                         + json.dumps(data, ensure_ascii=False, indent=1) + ";\n")
    print("wrote", out)
