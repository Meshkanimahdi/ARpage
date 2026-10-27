"""Which wall faces of the sketch model do the 12 listing photos see, and which extra camera poses fill the gaps."""
import json, math, re, sys
import numpy as np

src = open(sys.argv[1]).read()
def arr(name):
    m = re.search(r"const %s = \[(.*?)\n  \];" % name, src, re.S)
    return m.group(1)
ROOMS = [dict(id=r[0], x=float(r[1]), y=float(r[2]), w=float(r[3]), h=float(r[4])) for r in
         re.findall(r'id: "(\w+)".*?x: ([\d.]+), y: ([\d.]+), w: ([\d.]+), h: ([\d.]+)', arr("ROOMS"))]
WALLS = [list(map(float, w)) for w in re.findall(r"\[([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+), ([\d.]+)\]", arr("WALLS"))]
PHOTOS = [dict(n=int(n), room=r, x=float(x), y=float(y), a=float(a)) for n, r, x, y, a in
          re.findall(r'n: (\d+), room: "(\w+)", x: ([\d.]+), y: ([\d.]+), a: (-?[\d.]+)', arr("PHOTOS")) if "ai: true" not in next(l for l in arr("PHOTOS").splitlines() if f"n: {n}," in l)]
rects = []
for x1, y1, x2, y2, t in WALLS:
    h = t / 2
    rects.append((min(x1, x2) - (h if x1 == x2 else 0), min(y1, y2) - (h if y1 == y2 else 0),
                  max(x1, x2) + (h if x1 == x2 else 0), max(y1, y2) + (h if y1 == y2 else 0)))
TALL = [(2.92, .25, 3.3, 1.65), (3.1, 6.1, 3.72, 6.72)]              # shelving, fridge: block the view at eye level
FURN = [(3.9, .14, 5.5, 2.16), (6.27, 2.25, 7.05, 5.05), (4.5, 2.25, 6.27, 3.1), (5.3, 3.45, 6.02, 4.5),
        (2.47, 3.95, 3.1, 6.25), (5.6, 7.7, 6.65, 8.35), (2.46, 8.31, 4.38, 8.93), (1.45, 2.2, 2.3, 2.56)] + TALL
HFOV = math.radians(77)

def in_room(x, y):
    return next((r["id"] for r in ROOMS if r["x"] < x < r["x"] + r["w"] and r["y"] < y < r["y"] + r["h"]), None)

# samples on wall faces that face a room
samples = []   # (x, y, nx, ny, room)
for (x0, y0, x1, y1) in rects:
    for (ax, ay, bx, by, nx, ny) in [(x0, y0, x1, y0, 0, -1), (x0, y1, x1, y1, 0, 1), (x0, y0, x0, y1, -1, 0), (x1, y0, x1, y1, 1, 0)]:
        L = math.hypot(bx - ax, by - ay); n = int(L / .1)
        for i in range(n):
            t = (i + .5) / n; px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            r = in_room(px + nx * .05, py + ny * .05)
            inside_wall = any(a < px + nx * .05 < c and b < py + ny * .05 < d for a, b, c, d in rects)
            if r and not inside_wall:
                samples.append((px + nx * .02, py + ny * .02, nx, ny, r))
S = np.array([s[:4] for s in samples]); SR = [s[4] for s in samples]
print("wall face samples", len(S), "=", round(len(S) * .1, 1), "m")

def seg_hits_rect(p, q, r):
    # Liang-Barsky
    (x0, y0, x1, y1) = r; dx, dy = q[0] - p[0], q[1] - p[1]; t0, t1 = 0., 1.
    for pv, qv in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if pv == 0:
            if qv < 0: return False
        else:
            t = qv / pv
            if pv < 0: t0 = max(t0, t)
            else: t1 = min(t1, t)
    return t0 < t1 - 1e-6

def visible(cx, cy, a_deg):
    a = math.radians(a_deg); f = np.array([math.cos(a), math.sin(a)])
    v = S[:, :2] - [cx, cy]; d = np.linalg.norm(v, axis=1)
    ang = np.arccos(np.clip((v @ f) / np.maximum(d, 1e-6), -1, 1))
    inc = -(v[:, 0] * S[:, 2] + v[:, 1] * S[:, 3]) / np.maximum(d, 1e-6)
    ok = (ang < HFOV / 2) & (d > .3) & (d < 7) & (inc > .2)
    for i in np.nonzero(ok)[0]:
        if any(seg_hits_rect((cx, cy), S[i, :2], r) for r in rects + TALL):
            ok[i] = False
    return ok

seen = np.zeros(len(S), bool)
for p in PHOTOS:
    seen |= visible(p["x"], p["y"], p["a"])
def report(tag):
    out = {}
    for r in ROOMS:
        m = np.array([x == r["id"] for x in SR])
        out[r["id"]] = round(float(seen[m].mean()), 2)
    print(tag, "coverage", round(float(seen.mean()), 3), out)
report("12 photos:")
before = seen.copy()

# candidate poses
cands = []
for r in ROOMS:
    for x in np.arange(r["x"] + .45, r["x"] + r["w"] - .44, .25):
        for y in np.arange(r["y"] + .45, r["y"] + r["h"] - .44, .25):
            if any(a - .15 < x < c + .15 and b - .15 < y < d + .15 for a, b, c, d in FURN): continue
            if any(a - .3 < x < c + .3 and b - .3 < y < d + .3 for a, b, c, d in rects): continue
            for yaw in range(-180, 180, 15):
                cands.append((r["id"], round(float(x), 2), round(float(y), 2), yaw))
def ray_depth(cx, cy, a_deg):
    a = math.radians(a_deg); dx, dy = math.cos(a), math.sin(a)
    d = 0.
    while d < 8:
        d += .05; x, y = cx + dx * d, cy + dy * d
        if any(a0 < x < c0 and b0 < y < e0 for a0, b0, c0, e0 in rects + TALL) or not in_room(x, y) and not any(a0 < x < c0 and b0 < y < e0 for a0, b0, c0, e0 in rects):
            # leaving every room through an opening keeps going; only walls stop the ray
            if any(a0 < x < c0 and b0 < y < e0 for a0, b0, c0, e0 in rects + TALL): return d
            if not in_room(x, y): return d
    return d
rd = {r["id"]: math.hypot(r["w"], r["h"]) for r in ROOMS}
def framed(c):
    # look across the room, not at a wall a metre away: the centre ray and both frame edges need depth
    need = min(2.0, .75 * rd[c[0]])
    return (ray_depth(c[1], c[2], c[3]) >= need and ray_depth(c[1], c[2], c[3] - 25) >= .6 * need
            and ray_depth(c[1], c[2], c[3] + 25) >= .6 * need)
cands = [c for c in cands if framed(c)]
print("candidates", len(cands))
vis = {}
new = []
target = .95
while seen.mean() < target and len(new) < 14:
    best, bg = None, 0
    for c in cands:
        if c not in vis: vis[c] = visible(c[1], c[2], c[3])
        g = int((vis[c] & ~seen).sum())
        if g > bg: best, bg = c, g
    if not best or bg < 6: break       # less than 60 cm of new wall
    seen |= vis[best]; new.append(dict(room=best[0], x=best[1], y=best[2], a=best[3], gain_m=round(bg * .1, 1)))
    print("add", new[-1], "->", round(float(seen.mean()), 3))
report("with new:")
# for each new pose, the reference photos that see the most of the same wall
for p in new:
    v = vis[(p["room"], p["x"], p["y"], p["a"])]
    sc = []
    for q in PHOTOS:
        o = int((visible(q["x"], q["y"], q["a"]) & v).sum())
        same = q["room"] == p["room"]
        sc.append((o + (3 if same else 0), q["n"]))
    sc.sort(reverse=True); p["refs"] = [n for s, n in sc[:2] if s > 0] or [sc[0][1]]
json.dump(dict(new=new, coverage_before=float(before.mean()), coverage_after=float(seen.mean())), open(sys.argv[2], "w"), indent=1)
# unseen segments for the plan image
json.dump([[float(a), float(b)] for a, b in S[~seen, :2]], open(sys.argv[2].replace(".json", "_unseen.json"), "w"))
json.dump([[float(a), float(b)] for a, b in S[~before, :2]], open(sys.argv[2].replace(".json", "_unseen_before.json"), "w"))
