"""A plain 3D render of every tour point in 360 (equirectangular), ray-cast from home.json.

  python3 guides.py HOME.json OUT_DIR [width=2048]      (use 4096 for the copy that fix_pano.py zooms into)

Per point N it writes
  guideNN.png  the render, turned so that its left/right edge falls on a plain wall (the image model paints the two
               edges separately, so nothing important may sit there); rollNN.txt says by how much it was turned
  sidNN.npy    which surface each pixel shows (not turned), for checking the result
  dirsNN.txt   what stands in which direction, for the prompt
  risksNN.txt  features that are far away, narrow or seen at a grazing angle: the image model gets exactly these wrong,
               so each one has to be looked at under zoom after rendering (check_pano.py risks)

The image model turns the render into a photo; the render fixes where every wall, door and window is. Rays pass through
open doorways into the next room, so the render shows what is really visible from the point.
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home as homelib  # noqa: E402

# plain versions of typical finishes; home.json "palette" overrides any of them with "#rrggbb"
PALETTE = {"floor": "#e6dbcb", "joint": "#c6bbac", "ceiling": "#f8f8f7", "wall": "#ede4d5", "base": "#f5f5f4", "frame": "#f2f1f0",
           "glass_top": "#d6ecff", "glass_low": "#e2e8ec", "front": "#764e34", "leaf": "#f4f4f3", "leaf_panel": "#eae9e8",
           "cab": "#ebeae9", "counter": "#f2ece2", "stone": "#989492", "island": "#8a8684", "wardrobe": "#f0efee", "niche": "#ded4c8",
           "rad": "#f6f6f6", "fix": "#fcfcfc", "furn": "#b9ad9e", "slab": "#ebeae9", "slab_dark": "#686462", "slab_floor": "#d3d2d0"}


def bgr(h):
    h = h.lstrip("#")
    return (int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16))


def cast(H_, node, W):
    """Per pixel: the surface id, the distance, and a plain shaded colour."""
    C = {k: bgr(v) for k, v in dict(PALETTE, **H_.PALETTE).items()}
    C["col"] = C["wall"]
    TILE = H_.TILE
    H = W // 2
    u, v = np.meshgrid((np.arange(W) + .5) / W, (np.arange(H) + .5) / H)
    lon, lat = (u - .5) * 2 * np.pi, (.5 - v) * np.pi
    dx, dy, dz = np.sin(lon) * np.cos(lat), -np.cos(lon) * np.cos(lat), np.sin(lat)
    ox, oy, oz = node["x"], node["y"], node["h"]
    best = np.full((H, W), np.inf)
    sid = np.zeros((H, W), np.int32)
    rgb = np.zeros((H, W, 3), np.float32)
    kinds, labels = ["none"], [None]

    rooms = [None]

    def new(kind, label=None, room=None):
        kinds.append(kind); labels.append(label); rooms.append(room)
        return len(kinds) - 1

    def in_boxes(px, py, boxes):
        m = np.zeros(px.shape, bool)
        for x0, y0, x1, y1 in boxes:
            m |= (px > x0) & (px < x1) & (py > y0) & (py < y1)
        return m

    wet = [(min(q[0] for q in H_.ROOMS[k]["poly"]), min(q[1] for q in H_.ROOMS[k]["poly"]),
            max(q[0] for q in H_.ROOMS[k]["poly"]), max(q[1] for q in H_.ROOMS[k]["poly"])) for k in H_.SLAB_ROOMS]

    def put(ok, t, i, colour, shade=1.0):
        best[ok], sid[ok] = t[ok], i
        c = np.asarray(colour, np.float32)
        rgb[ok] = (c if c.ndim == 1 else c[ok]) * (np.asarray(shade, np.float32)[ok, None] if np.ndim(shade) else shade)

    with np.errstate(divide="ignore", invalid="ignore"):
        # floor with its tile joints (they fade with distance), ceiling
        t = (0.0 - oz) / dz
        ok = (t > 1e-4) & (t < best)
        px, py = ox + t * dx, oy + t * dy
        jw = 0.004 + 0.002 * np.clip(t, 0, 8)
        joint = ((np.abs((px / TILE + .5) % 1 - .5) * TILE < jw) | (np.abs((py / TILE + .5) % 1 - .5) * TILE < jw)) & (t < 7)
        col = np.where(joint[..., None], np.float32(C["joint"]), np.float32(C["floor"]))
        col[in_boxes(px, py, wet) & ~joint] = C["slab_floor"]
        put(ok, t, new("floor"), col, 1 - .10 * np.clip(t / 9, 0, 1))
        t = (H_.CEIL - oz) / dz
        ok = (t > 1e-4) & (t < best)
        put(ok, t, new("ceil"), C["ceiling"], 1 - .05 * np.clip(t / 9, 0, 1))

        for ax, ay, bx, by, room, holes in H_.segments():
            ex, ey = bx - ax, by - ay
            L = float(np.hypot(ex, ey))
            den = dx * ey - dy * ex
            t = ((ax - ox) * ey - (ay - oy) * ex) / den
            s = ((ax - ox) * dy - (ay - oy) * dx) / den
            z = oz + t * dz
            hit = (t > 1e-4) & (s >= 0) & (s <= 1) & (z >= 0) & (z <= H_.CEIL)
            shade = (1.0 if abs(ey) < 1e-6 else .94 if abs(ex) < 1e-6 else .9) * (1 - .08 * np.clip(t / 9, 0, 1))
            wall = new("wall")
            solid = hit.copy()
            if room in H_.SLAB_ROOMS:              # slabs to the floor, dark where the plan says so
                col = np.broadcast_to(np.float32(C["slab"]), rgb.shape).copy()
                col[in_boxes(ox + t * dx, oy + t * dy, H_.DARK)] = C["slab_dark"]
            else:
                col = np.broadcast_to(np.float32(C["wall"]), rgb.shape).copy()
                col[z < 0.09] = C["base"]
            for s0, s1, z0, z1, kind, label in holes:
                inh = hit & (s >= s0) & (s <= s1) & (z >= z0) & (z <= z1)
                solid &= ~inh
                if kind in ("door", "front"):      # the frame around a door
                    f = 0.07 / L
                    col[(s >= s0 - f) & (s <= s1 + f) & (z <= z1 + 0.07)] = C["frame"]
                if kind in ("door", "open"):
                    continue                      # the ray goes on into the next room
                ok = inh & (t < best)
                i = new(kind, label, room)
                if kind == "window":
                    k = np.clip((z - z0) / (z1 - z0), 0, 1)[..., None]
                    c = np.float32(C["glass_low"]) * (1 - k) + np.float32(C["glass_top"]) * k
                    d = 0.06 / L                  # frame and middle post
                    fr = (s < s0 + d) | (s > s1 - d) | (z < z0 + 0.06) | (z > z1 - 0.06)
                    if z0 > 0.3:                  # a window has a middle post; a glazed door is one leaf
                        fr |= np.abs(s - (s0 + s1) / 2) < d / 2
                    c = np.where(fr[..., None], np.float32((250, 250, 250)), c)
                    put(ok, t, i, c)
                elif kind == "front":
                    put(ok, t, i, C["front"], shade)
                else:                             # flush wardrobe front: two doors
                    c = np.broadcast_to(np.float32(C["wardrobe"]), rgb.shape).copy()
                    c[np.abs(s - (s0 + s1) / 2) < 0.012 / L] = (150, 150, 150)
                    put(ok, t, i, c, shade)
            ok = solid & (t < best)
            put(ok, t, wall, col, shade)

        for (ax, ay), (bx, by) in H_.LEAVES:   # door leaves standing open
            ex, ey = bx - ax, by - ay
            den = dx * ey - dy * ex
            t = ((ax - ox) * ey - (ay - oy) * ex) / den
            s = ((ax - ox) * dy - (ay - oy) * dx) / den
            z = oz + t * dz
            ok = (t > 1e-4) & (s >= 0) & (s <= 1) & (z >= 0.01) & (z <= H_.LEAF_H) & (t < best)
            c = np.broadcast_to(np.float32(C["leaf"]), rgb.shape).copy()
            inset = (np.abs(s - .5) < .34) & (((z > .25) & (z < .95)) | ((z > 1.1) & (z < 1.9)))   # the two raised panels
            c[inset] = C["leaf_panel"]
            put(ok, t, new("leaf", H_.STYLE["door_leaf"] + ", standing open",
                           H_.room_at((ax + bx) / 2, (ay + by) / 2)), c,
                (.96 if abs(ey) < abs(ex) else .9) * (1 - .08 * np.clip(t / 9, 0, 1)))

        for x0, y0, x1, y1, z0, z1, kind, label in H_.BOXES:
            tn, tf = np.full((H, W), -np.inf), np.full((H, W), np.inf)
            face = np.zeros((H, W), np.int8)
            for k, (o, d, lo, hi) in enumerate(((ox, dx, x0, x1), (oy, dy, y0, y1), (oz, dz, z0, z1))):
                a, b = (lo - o) / d, (hi - o) / d
                near = np.minimum(a, b)
                face[near > tn] = k
                tn, tf = np.maximum(tn, near), np.minimum(tf, np.maximum(a, b))
            ok = (tn < tf) & (tn > 1e-4) & (tn < best)
            c = np.broadcast_to(np.float32(C.get(kind, C["furn"])), rgb.shape).copy()
            if kind == "cab" and z0 == 0 and z1 < 1.2:
                c[face == 2] = C["counter"]
            shade = np.choose(face, [.9, .82, 1.0]).astype(np.float32) * (1 - .08 * np.clip(tn / 9, 0, 1))
            put(ok, tn, new(kind, label, H_.room_at((x0 + x1) / 2, (y0 + y1) / 2)), c, shade)
    return sid, best, rgb, kinds, labels, rooms


def draw(H_, node, W=2048):
    """The render, turned so that its left/right edge falls on the plainest stretch of wall, and the lists that go with it."""
    sid0, depth, rgb, kinds, labels, rooms = cast(H_, node, W)
    img = rgb.clip(0, 255).astype(np.uint8)
    # a soft line where the surface changes, like the edges in a clay render
    e = np.zeros(sid0.shape, bool)
    e[:, 1:] |= sid0[:, 1:] != sid0[:, :-1]
    e[1:, :] |= sid0[1:, :] != sid0[:-1, :]
    img[e] = (img[e] * .55).astype(np.uint8)
    img = cv2.GaussianBlur(img, (0, 0), 0.6)
    # the seam: the column with the least going on around it (the model paints the two edges separately)
    Hh = sid0.shape[0]
    busy = e[int(Hh * .2):int(Hh * .85)].sum(0).astype(np.float32)
    plain = np.array([kinds[i] == "wall" for i in sid0[Hh // 2]]) & np.array([kinds[i] == "wall" for i in sid0[int(Hh * .62)]])
    busy += np.where(plain, 0, Hh)             # a door, window or cabinet across the edge is worse than any corner
    win = int(W * .07)
    score = np.convolve(np.concatenate([busy[-win:], busy, busy[:win]]), np.ones(2 * win + 1), "valid")
    shift = int(np.argmin(score))
    depth0 = depth
    img, sid, depth = np.roll(img, -shift, 1), np.roll(sid0, -shift, 1), np.roll(depth, -shift, 1)
    # where things are in the turned image: share of its width, 0 = left edge
    cols = (np.arange(W) + .5) / W * 2 * np.pi
    found = []
    for i, lab in enumerate(labels):
        m = sid == i
        if lab is None or m.sum() < W * W / 2 * 0.0012:
            continue
        c = m.sum(0)
        ang = np.arctan2((np.sin(cols) * c).sum(), (np.cos(cols) * c).sum()) % (2 * np.pi)
        if rooms[i] and rooms[i] != node["room"]:   # not in this room: say so, or it gets painted on this room's wall
            lab += " (NOT in this room: inside the %s, seen through the doorway)" % H_.ROOM_EN[rooms[i]]
        found.append((ang / (2 * np.pi) * 100, lab, depth[m].mean()))
    # doorways of this room: the render shows the next room through them, so name them too
    grazing = []
    for o in H_.OPENINGS:
        if node["room"] not in o["rooms"] or o["kind"] == "front":
            continue
        mx, my = (o["a"][0] + o["b"][0]) / 2, (o["a"][1] + o["b"][1]) / 2
        other = [r for r in o["rooms"] if r != node["room"]][0]
        # name it only if it is really in view from here: a ray to its middle must get that far
        seen = False
        for k in (.25, .5, .75):
            qx, qy = o["a"][0] + (o["b"][0] - o["a"][0]) * k, o["a"][1] + (o["b"][1] - o["a"][1]) * k
            d = float(np.hypot(qx - node["x"], qy - node["y"]))
            col = int(((np.arctan2(qx - node["x"], -(qy - node["y"])) / (2 * np.pi) + .5) % 1) * W) % W
            row = int((.5 - np.arctan2(1.0 - node["h"], d) / np.pi) * Hh)
            # ... and not at a grazing angle, where it is only a sliver the model would blow up into a door
            wx, wy = o["b"][0] - o["a"][0], o["b"][1] - o["a"][1]
            square = abs((qx - node["x"]) * wy - (qy - node["y"]) * wx) / (d * float(np.hypot(wx, wy)))
            seen |= bool(depth0[row, col] > float(np.hypot(d, 1.0 - node["h"])) - 0.05 and square > 0.25)
        lon = np.arctan2(mx - node["x"], -(my - node["y"]))
        if not seen:
            if depth0[Hh // 2, int(((lon / (2 * np.pi) + .5) % 1) * W) % W] > float(np.hypot(mx - node["x"], my - node["y"])) - 0.3:
                grazing.append(((lon / (2 * np.pi) + .5) % 1 * 100, o["label"]))
            continue
        what = ("a wide opening without a door, through it " if o["kind"] == "open" else "an open doorway with %s, through it " % H_.STYLE["door_frame"]) + H_.THROUGH[other]
        found.append((((lon / (2 * np.pi) + .5) - shift / W) % 1 * 100, what, float(np.hypot(mx - node["x"], my - node["y"]))))
    found.sort()
    lines = ["%2.0f%%: %s, about %.1f m away" % (x, lab, d) for x, lab, d in found]
    # four directions a quarter turn apart, so the model spreads the room over the full circle
    row = sid.shape[0] // 2
    main = []
    for name, x in (("0% and 100% (one and the same direction: the image wraps around)", 0), ("25%", .25), ("50% (image centre)", .5), ("75%", .75)):
        i = sid[row, int(x * (W - 1))]
        what = labels[i] or ("a plain wall" if kinds[i] == "wall" else kinds[i])
        main.append("%s: %s, %.1f m away" % (name, what, depth[row, int(x * (W - 1))]))
    # what the image model is likely to get wrong: labelled things that take up very little of the picture
    risks = []
    for i, lab in enumerate(labels):
        m = sid0 == i
        if lab is None or not m.any():
            continue
        c = m.any(0)
        wide = c.sum() / W * 100
        if wide >= 2.2 or m.sum() < 40:
            continue
        ang = np.arctan2((np.sin(cols) * c).sum(), (np.cos(cols) * c).sum()) % (2 * np.pi)
        cx = ang / (2 * np.pi) * 100
        rows = np.nonzero(m.any(1))[0]
        risks.append("%.1f %.1f %.1f %.1f | %s | %.1f%% wide, %.1f m away" % (
            (cx - wide / 2 - 1.5) % 100, (cx + wide / 2 + 1.5) % 100, max(0, rows.min() / Hh * 100 - 3), min(100, rows.max() / Hh * 100 + 3),
            lab, wide, depth0[m].mean()))
    for x, lab in grazing:
        risks.append("%.1f %.1f 38.0 64.0 | %s, seen at a grazing angle: make sure no door or opening was invented here | sliver" % ((x - 2.5) % 100, (x + 2.5) % 100, lab))
    return img, lines, main, sid0, shift / W, risks


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    H_ = homelib.load(sys.argv[1])
    out = sys.argv[2]
    W = int(sys.argv[3]) if len(sys.argv) > 3 else 2048
    os.makedirs(out, exist_ok=True)
    for node in H_.NODES:
        img, lines, main, sid, roll, risks = draw(H_, node, W)
        n = node["n"]
        open(os.path.join(out, "roll%02d.txt" % n), "w").write("%.6f\n" % roll)
        cv2.imwrite(os.path.join(out, "guide%02d.png" % n), img)
        np.save(os.path.join(out, "sid%02d.npy" % n), sid.astype(np.int16))
        open(os.path.join(out, "dirs%02d.txt" % n), "w").write(
            "At eye level, a quarter turn apart:\n" + "\n".join(main) + "\nFeatures, left to right:\n" + "\n".join(lines) + "\n")
        open(os.path.join(out, "risks%02d.txt" % n), "w").write("\n".join(risks) + ("\n" if risks else ""))
        print("point %s: %d features listed, %d risk spots" % (n, len(lines), len(risks)))
