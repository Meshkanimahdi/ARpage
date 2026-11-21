"""The property description (home.json) as one object that every other script reads.

  python3 home.py HOME.json validate          check the description before spending money on images
  python3 home.py HOME.json links             where each tour point can go
  python3 home.py HOME.json locate N X Y [Z]  where a plan point shows up in panorama N (percent of width / height)
  python3 home.py HOME.json span N X0 Y0 X1 Y1 [Z0 Z1]   the percent box of a wall stretch in panorama N (for fix_pano.py)

Plan coordinates are metres, x to the right, y DOWN (as drawn on the sheet). Heights are metres above the floor.
A panorama's centre column looks toward the top of the plan (-y); the left-to-right direction turns clockwise on the plan.
The format is described in references/home-schema.md.
"""
import json
import math
import sys

STYLE = {
    "state": "empty",   # or "furnished"
    "door_leaf": "a white interior door leaf with a handle",
    "door_frame": "a white frame",
    "window_view": "only pale hazy daylight sky and indistinct low rooftops, nothing recognizable",
    "through_legend": "",
}


class Home:
    def __init__(self, path):
        d = json.load(open(path, encoding="utf-8"))
        self.d, self.path = d, path
        self.TITLE = d.get("title", "")
        self.NOTE = d.get("note", "")
        self.CEIL = float(d.get("ceiling", 2.8))
        self.TILE = float(d.get("tile", 0.8))
        self.EYE = float(d.get("eye", 1.5))
        self.WALL_T = float(d.get("wall_thickness", 0.16))
        self.STYLE = dict(STYLE, **d.get("style", {}))
        self.PALETTE = d.get("palette", {})
        self.ALL_ROOMS = d["rooms"]                              # includes label-only zones (no "poly")
        self.ROOMS = {r["id"]: r for r in d["rooms"] if r.get("poly")}
        self.ROOM_EN = {k: r.get("name_en", k) for k, r in self.ROOMS.items()}
        self.THROUGH = {k: r.get("through", "the " + self.ROOM_EN[k]) for k, r in self.ROOMS.items()}
        self.FINISH = {k: r.get("finish", "") for k, r in self.ROOMS.items()}
        self.SLAB_ROOMS = tuple(k for k, r in self.ROOMS.items() if r.get("slab"))
        self.DARK = [tuple(b) for b in d.get("slab_dark", [])]
        kinds = {"front": "the front door (closed)", "open": "a wide opening without a door"}
        self.OPENINGS = [{"head": 2.1, "kind": "door", "label": kinds.get(o.get("kind"), "an open doorway"), **o} for o in d.get("openings", [])]
        self.WINDOWS = [{"sill": 1.0, "head": 2.25, "label": "a window", **w} for w in d.get("windows", [])]
        self.PANELS = [{"head": 2.6, "label": "a built-in wardrobe front", **p} for p in d.get("panels", [])]
        self.LEAVES = [(tuple(l["hinge"]), tuple(l["tip"])) for l in d.get("leaves", [])]
        self.LEAF_H = float(d.get("leaf_height", 2.05))
        self.BOXES = [tuple(b["box"]) + (b["kind"], b.get("label")) for b in d.get("boxes", [])]
        self.BOX_PLAN = [(tuple(b["box"][:4]), b["plan"]) for b in d.get("boxes", []) if b.get("plan")]
        self.NODES = [{"h": self.EYE, "refs": [], **p} for p in d.get("nodes", [])]

    # ---------- geometry ----------
    def segments(self):
        """Every wall as a segment with its holes: (ax, ay, bx, by, room, [(s0, s1, z0, z1, kind, label)])."""
        out = []
        for key, r in self.ROOMS.items():
            P = r["poly"]
            for i in range(len(P)):
                (ax, ay), (bx, by) = P[i], P[(i + 1) % len(P)]
                L = math.hypot(bx - ax, by - ay)
                if L < 1e-9:
                    continue
                ux, uy = (bx - ax) / L, (by - ay) / L
                holes = []
                for o in self.OPENINGS + self.WINDOWS + self.PANELS:
                    (px, py), (qx, qy) = o["a"], o["b"]
                    if abs((qx - px) * uy - (qy - py) * ux) > 1e-6:          # same direction ...
                        continue
                    if abs((px - ax) * uy - (py - ay) * ux) > 0.3:           # ... close to this wall line ...
                        continue
                    s0, s1 = sorted((((px - ax) * ux + (py - ay) * uy) / L, ((qx - ax) * ux + (qy - ay) * uy) / L))
                    if s1 <= 0.001 or s0 >= 0.999:                            # ... overlapping its span
                        continue
                    kind = "window" if "sill" in o else o.get("kind", "panel")
                    holes.append((max(0, s0), min(1, s1), o.get("sill", 0), o["head"], kind, o["label"]))
                out.append((ax, ay, bx, by, key, holes))
        return out

    @staticmethod
    def inside(poly, x, y):
        c = False
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0):
                c = not c
        return c

    def room_at(self, x, y):
        for key, r in self.ROOMS.items():
            if self.inside(r["poly"], x, y):
                return key
        return None

    def sight(self, ax, ay, bx, by, margin=0.12):
        """True when nothing solid stands between two floor points: every sample lies inside a room, off the tall boxes."""
        n = int(math.hypot(bx - ax, by - ay) / 0.05) + 2
        for i in range(n + 1):
            x, y = ax + (bx - ax) * i / n, ay + (by - ay) * i / n
            if self.room_at(x, y) is None:
                return False
            if any(b[0] - margin < x < b[2] + margin and b[1] - margin < y < b[3] + margin and b[5] > 1.0 and b[6] != "col" for b in self.BOXES):
                return False
        return True

    def links(self):
        """Where each point can go: another point of the same room in plain sight, or the room behind a door (ring at the door)."""
        out = {}
        for a in self.NODES:
            ls = []
            for b in self.NODES:
                if b is a:
                    continue
                if a["room"] == b["room"]:
                    if self.sight(a["x"], a["y"], b["x"], b["y"]):
                        ls.append(dict(n=b["n"], x=b["x"], y=b["y"]))
                    continue
                for o in self.OPENINGS:
                    if a["room"] in o.get("rooms", []) and b["room"] in o.get("rooms", []):
                        mx, my = (o["a"][0] + o["b"][0]) / 2, (o["a"][1] + o["b"][1]) / 2
                        d = math.hypot(a["x"] - mx, a["y"] - my)
                        rx, ry = mx + (a["x"] - mx) / d * 0.45, my + (a["y"] - my) / d * 0.45
                        if self.sight(a["x"], a["y"], rx, ry):
                            # the point of that room nearest to the door stands for the room
                            near = min((q for q in self.NODES if q["room"] == b["room"]), key=lambda q: math.hypot(q["x"] - mx, q["y"] - my))
                            if near is b:
                                ls.append(dict(n=b["n"], x=round(rx, 2), y=round(ry, 2), door=True))
            out[a["n"]] = ls
        return out

    @staticmethod
    def area(p):
        return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2

    def bounds(self):
        P = [q for r in self.ROOMS.values() for q in r["poly"]]
        return min(q[0] for q in P), min(q[1] for q in P), max(q[0] for q in P), max(q[1] for q in P)

    def node(self, n):
        return next(p for p in self.NODES if p["n"] == int(n))

    def locate(self, n, x, y, z=1.0):
        """Where a point of the plan shows up in panorama n: (percent of the width, percent of the height)."""
        p = self.node(n)
        u = (math.atan2(x - p["x"], -(y - p["y"])) / (2 * math.pi) + .5) % 1
        v = .5 - math.atan2(z - p["h"], math.hypot(x - p["x"], y - p["y"])) / math.pi
        return u * 100, v * 100

    def span(self, n, x0, y0, x1, y1, z0=0.0, z1=2.2, pad=0.6):
        """The percent box (X0, X1, Y0, Y1) that a stretch of wall or an object takes in panorama n; X0 > X1 = across the edge."""
        us, vs = [], []
        for i in range(21):
            x, y = x0 + (x1 - x0) * i / 20, y0 + (y1 - y0) * i / 20
            for z in (z0, z1):
                u, v = self.locate(n, x, y, z)
                us.append(u); vs.append(v)
        c = math.degrees(math.atan2(sum(math.sin(math.radians(u * 3.6)) for u in us), sum(math.cos(math.radians(u * 3.6)) for u in us))) / 3.6 % 100
        half = max(abs((u - c + 50) % 100 - 50) for u in us) + pad
        return (c - half) % 100, (c + half) % 100, max(0, min(vs) - pad), min(100, max(vs) + pad)

    # ---------- checks ----------
    def validate(self):
        err, warn = [], []
        segs = self.segments()
        for k, r in self.ROOMS.items():
            if len(r["poly"]) < 3 or self.area(r["poly"]) < 0.5:
                err.append("room %s: outline has no area" % k)
        for i, o in enumerate(self.OPENINGS):
            for k in o.get("rooms", []):
                if k not in self.ROOMS:
                    err.append("opening %d (%s): unknown room %s" % (i, o["label"], k))
                elif not any(s[4] == k and any(h[5] == o["label"] and h[4] == o.get("kind") for h in s[5]) for s in segs):
                    err.append("opening %d (%s) is not on a wall of room %s: its two ends must lie on that room's outline (within 0.3 m)" % (i, o["label"], k))
            if not o.get("rooms"):
                err.append("opening %d (%s): list the room(s) it belongs to" % (i, o["label"]))
        for kind, items in (("window", self.WINDOWS), ("panel", self.PANELS)):
            for i, o in enumerate(items):
                if not any(any(h[5] == o["label"] and h[4] == kind for h in s[5]) for s in segs):
                    err.append("%s %d (%s) is not on any wall" % (kind, i, o["label"]))
        seen = set()
        for p in self.NODES:
            if p["n"] in seen:
                err.append("tour point %s is defined twice" % p["n"])
            seen.add(p["n"])
            if p["room"] not in self.ROOMS:
                err.append("tour point %s: unknown room %s" % (p["n"], p["room"])); continue
            if not self.inside(self.ROOMS[p["room"]]["poly"], p["x"], p["y"]):
                err.append("tour point %s is outside its room %s" % (p["n"], p["room"])); continue
            near = min(self._dist(p["x"], p["y"], s) for s in segs if s[4] == p["room"])
            if near < 0.4:
                warn.append("tour point %s stands %.2f m from a wall: that wall will fill a quarter of the panorama; move it to 0.6 m or more" % (p["n"], near))
            if any(b[0] < p["x"] < b[2] and b[1] < p["y"] < b[3] and b[5] > 0.3 for b in self.BOXES):
                err.append("tour point %s stands inside a box" % p["n"])
        for k in self.ROOMS:
            if not any(p["room"] == k for p in self.NODES):
                warn.append("room %s has no tour point" % k)
        for b in self.BOXES:
            if self.room_at((b[0] + b[2]) / 2, (b[1] + b[3]) / 2) is None:
                warn.append("box %s is outside every room" % (b[7] or b[6]))
        for (hx, hy), _ in self.LEAVES:
            if not any(min(math.hypot(hx - o["a"][0], hy - o["a"][1]), math.hypot(hx - o["b"][0], hy - o["b"][1])) < 0.3 for o in self.OPENINGS if o.get("kind") == "door"):
                warn.append("door leaf at (%.2f, %.2f): its hinge is not at the end of any door opening" % (hx, hy))
        doors = [o for o in self.OPENINGS if o.get("kind") == "door"]
        if len(self.LEAVES) < len(doors):
            warn.append("%d door openings but %d door leaves: a doorway without a modelled leaf invites the image model to invent one" % (len(doors), len(self.LEAVES)))
        if self.NODES and not err:
            L, reach, todo = self.links(), set(), [self.NODES[0]["n"]]
            while todo:
                n = todo.pop()
                if n not in reach:
                    reach.add(n); todo += [l["n"] for l in L[n]]
            for p in self.NODES:
                if p["n"] not in reach:
                    err.append("tour point %s cannot be reached from point %s: no line of sight and no doorway link" % (p["n"], self.NODES[0]["n"]))
                if not L[p["n"]]:
                    err.append("tour point %s leads nowhere" % p["n"])
        return err, warn

    @staticmethod
    def _dist(x, y, s):
        ax, ay, bx, by = s[:4]
        L2 = (bx - ax) ** 2 + (by - ay) ** 2
        t = max(0, min(1, ((x - ax) * (bx - ax) + (y - ay) * (by - ay)) / L2))
        return math.hypot(x - ax - t * (bx - ax), y - ay - t * (by - ay))


def load(path):
    return Home(path)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    H, cmd, a = load(sys.argv[1]), sys.argv[2], sys.argv[3:]
    if cmd == "validate":
        err, warn = H.validate()
        for w in warn:
            print("warning:", w)
        for e in err:
            print("ERROR:", e)
        print("%d rooms, %d tour points, %.1f m2 in all, %d errors, %d warnings" % (
            len(H.ROOMS), len(H.NODES), sum(H.area(r["poly"]) for r in H.ROOMS.values()), len(err), len(warn)))
        sys.exit(1 if err else 0)
    elif cmd == "links":
        for n, ls in H.links().items():
            print(n, "->", ", ".join("%s%s" % (l["n"], " (door)" if l.get("door") else "") for l in ls))
    elif cmd == "locate":
        print("x = %.1f%%  y = %.1f%%" % H.locate(a[0], *[float(v) for v in a[1:]]))
    elif cmd == "span":
        print("%.1f %.1f %.1f %.1f" % H.span(a[0], *[float(v) for v in a[1:]]))
    else:
        sys.exit(__doc__)
