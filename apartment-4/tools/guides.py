"""A plain 3D render of every tour point in 360 (equirectangular), ray-cast from the confirmed plan.

  python3 tools/guides.py OUT_DIR [width]

For each point it writes guideNN.png (turned so that its left/right edge falls on a plain wall; rollNN.txt says by how much), sidNN.npy (which surface each pixel
shows, for checking the result) and dirsNN.txt, a list of what stands in which direction. The image model turns the
render into a photo; the render fixes where every wall, door and window is. Rays pass through open doorways into the
next room, so the render shows what is really visible from the point.
"""
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene  # noqa: E402

# BGR, 0..255: plain versions of the real finishes
FLOOR, JOINT, CEILING, WALL, BASE, FRAME = (203, 219, 230), (172, 187, 198), (247, 248, 248), (213, 228, 237), (244, 245, 245), (240, 241, 242)
GLASS_TOP, GLASS_LOW, DOOR_BROWN = (255, 236, 214), (236, 232, 226), (52, 78, 118)
BOX = {"cab": (233, 234, 235), "stone": (146, 148, 152), "island": (132, 134, 138), "wardrobe": (238, 239, 240),
       "rad": (246, 246, 246), "fix": (252, 252, 252), "col": WALL}
MARBLE, DARK, FLOOR_GREY = (233, 234, 235), (98, 100, 104), (208, 210, 211)
TILE = 0.8


def cast(node, W):
    """Per pixel: the surface id, the distance, and a plain shaded colour."""
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

    wet = [(min(q[0] for q in scene.ROOMS[k]["poly"]), min(q[1] for q in scene.ROOMS[k]["poly"]),
            max(q[0] for q in scene.ROOMS[k]["poly"]), max(q[1] for q in scene.ROOMS[k]["poly"])) for k in scene.SLAB_ROOMS]

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
        col = np.where(joint[..., None], np.float32(JOINT), np.float32(FLOOR))
        col[in_boxes(px, py, wet) & ~joint] = FLOOR_GREY
        put(ok, t, new("floor"), col, 1 - .10 * np.clip(t / 9, 0, 1))
        t = (scene.CEIL - oz) / dz
        ok = (t > 1e-4) & (t < best)
        put(ok, t, new("ceil"), CEILING, 1 - .05 * np.clip(t / 9, 0, 1))

        for ax, ay, bx, by, room, holes in scene.segments():
            ex, ey = bx - ax, by - ay
            L = float(np.hypot(ex, ey))
            den = dx * ey - dy * ex
            t = ((ax - ox) * ey - (ay - oy) * ex) / den
            s = ((ax - ox) * dy - (ay - oy) * dx) / den
            z = oz + t * dz
            hit = (t > 1e-4) & (s >= 0) & (s <= 1) & (z >= 0) & (z <= scene.CEIL)
            shade = (1.0 if abs(ey) < 1e-6 else .94 if abs(ex) < 1e-6 else .9) * (1 - .08 * np.clip(t / 9, 0, 1))
            wall = new("wall")
            solid = hit.copy()
            if room in scene.SLAB_ROOMS:              # slabs to the floor, dark where the plan says so
                col = np.broadcast_to(np.float32(MARBLE), rgb.shape).copy()
                col[in_boxes(ox + t * dx, oy + t * dy, scene.DARK)] = DARK
            else:
                col = np.broadcast_to(np.float32(WALL), rgb.shape).copy()
                col[z < 0.09] = BASE
            for s0, s1, z0, z1, kind, label in holes:
                inh = hit & (s >= s0) & (s <= s1) & (z >= z0) & (z <= z1)
                solid &= ~inh
                if kind in ("door", "front"):      # the frame around a door
                    f = 0.07 / L
                    col[(s >= s0 - f) & (s <= s1 + f) & (z <= z1 + 0.07)] = FRAME
                if kind in ("door", "open"):
                    continue                      # the ray goes on into the next room
                ok = inh & (t < best)
                i = new(kind, label, room)
                if kind == "window":
                    k = np.clip((z - z0) / (z1 - z0), 0, 1)[..., None]
                    c = np.float32(GLASS_LOW) * (1 - k) + np.float32(GLASS_TOP) * k
                    d = 0.06 / L                  # frame and middle post
                    fr = (s < s0 + d) | (s > s1 - d) | (z < z0 + 0.06) | (z > z1 - 0.06) | (np.abs(s - (s0 + s1) / 2) < d / 2)
                    c = np.where(fr[..., None], np.float32((250, 250, 250)), c)
                    put(ok, t, i, c)
                elif kind == "front":
                    put(ok, t, i, DOOR_BROWN, shade)
                else:                             # flush wardrobe front: two doors
                    c = np.broadcast_to(np.float32(BOX["wardrobe"]), rgb.shape).copy()
                    c[np.abs(s - (s0 + s1) / 2) < 0.012 / L] = (150, 150, 150)
                    put(ok, t, i, c, shade)
            ok = solid & (t < best)
            put(ok, t, wall, col, shade)

        for (ax, ay), (bx, by) in scene.LEAVES:   # door leaves standing open
            ex, ey = bx - ax, by - ay
            den = dx * ey - dy * ex
            t = ((ax - ox) * ey - (ay - oy) * ex) / den
            s = ((ax - ox) * dy - (ay - oy) * dx) / den
            z = oz + t * dz
            ok = (t > 1e-4) & (s >= 0) & (s <= 1) & (z >= 0.01) & (z <= scene.LEAF_H) & (t < best)
            c = np.broadcast_to(np.float32((243, 244, 244)), rgb.shape).copy()
            inset = (np.abs(s - .5) < .34) & (((z > .25) & (z < .95)) | ((z > 1.1) & (z < 1.9)))   # the two raised panels
            c[inset] = (232, 233, 234)
            put(ok, t, new("leaf", "a white door leaf standing open (classic raised panels, brass handle)",
                           scene.room_at((ax + bx) / 2, (ay + by) / 2)), c,
                (.96 if abs(ey) < abs(ex) else .9) * (1 - .08 * np.clip(t / 9, 0, 1)))

        for x0, y0, x1, y1, z0, z1, kind, label in scene.BOXES:
            tn, tf = np.full((H, W), -np.inf), np.full((H, W), np.inf)
            face = np.zeros((H, W), np.int8)
            for k, (o, d, lo, hi) in enumerate(((ox, dx, x0, x1), (oy, dy, y0, y1), (oz, dz, z0, z1))):
                a, b = (lo - o) / d, (hi - o) / d
                near = np.minimum(a, b)
                face[near > tn] = k
                tn, tf = np.maximum(tn, near), np.minimum(tf, np.maximum(a, b))
            ok = (tn < tf) & (tn > 1e-4) & (tn < best)
            look = kind
            if kind == "cab" and (z0 > 1.2 or (x1 - x0) < 0.2):
                look = "stone"                    # upper cabinets and the end panel are grey stone-look
            c = np.broadcast_to(np.float32(BOX[look]), rgb.shape).copy()
            if kind in ("cab", "island") and z0 == 0 and z1 < 1.2:
                c[face == 2] = BOX["stone"]       # counter top
            shade = np.choose(face, [.9, .82, 1.0]).astype(np.float32) * (1 - .08 * np.clip(tn / 9, 0, 1))
            put(ok, tn, new(kind, label, scene.room_at((x0 + x1) / 2, (y0 + y1) / 2)), c, shade)
    return sid, best, rgb, kinds, labels, rooms


def draw(node, W=2048):
    """The render, turned so that its left/right edge falls on the plainest stretch of wall, and the lists that go with it."""
    sid0, depth, rgb, kinds, labels, rooms = cast(node, W)
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
            lab += " (NOT in this room: inside the %s, seen through the doorway)" % scene.ROOM_EN[rooms[i]]
        found.append((ang / (2 * np.pi) * 100, lab, depth[m].mean()))
    # doorways of this room: the render shows the next room through them, so name them too
    for o in scene.OPENINGS:
        if node["room"] not in o["rooms"] or o["kind"] == "front":
            continue
        mx, my = (o["a"][0] + o["b"][0]) / 2, (o["a"][1] + o["b"][1]) / 2
        other = [r for r in o["rooms"] if r != node["room"]][0]
        what = ("a wide opening without a door, through it " if o["kind"] == "open" else "an open doorway with a white frame, through it ") + scene.THROUGH[other]
        lon = np.arctan2(mx - node["x"], -(my - node["y"]))
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
    return img, lines, main, sid0, shift / W


if __name__ == "__main__":
    out = sys.argv[1]
    W = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
    os.makedirs(out, exist_ok=True)
    for node in scene.NODES:
        img, lines, main, sid, roll = draw(node, W)
        open(os.path.join(out, "roll%02d.txt" % node["n"]), "w").write("%.6f\n" % roll)
        cv2.imwrite(os.path.join(out, "guide%02d.png" % node["n"]), img)
        np.save(os.path.join(out, "sid%02d.npy" % node["n"]), sid.astype(np.int16))
        open(os.path.join(out, "dirs%02d.txt" % node["n"]), "w").write(
            "At eye level, a quarter turn apart:\n" + "\n".join(main) + "\nFeatures, left to right:\n" + "\n".join(lines) + "\n")
        print(node["n"], len(lines), "features")
