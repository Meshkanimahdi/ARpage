"""Draw an equirectangular line drawing of each 360 point's room from the plan: the layout guide given to the image
model with the real photos of that room. Walls, doors and windows in black, furniture in grey.

  python3 tools/guides.py OUT_DIR [width]
"""
import math
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from home_data import CEIL, FURNITURE, NODES, OPENINGS, ROOMS, WINDOWS  # noqa: E402


def wall_rect(axis, c, a0, a1, z0, z1):
    P = (lambda a, z: (a, c, z)) if axis == "x" else (lambda a, z: (c, a, z))
    p = [P(a0, z0), P(a1, z0), P(a1, z1), P(a0, z1)]
    return [(p[i], p[(i + 1) % 4]) for i in range(4)]


def box(x0, y0, x1, y1, z0, z1):
    c = [(x, y, z) for z in (z0, z1) for (x, y) in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))]
    e = [(i, (i + 1) % 4) for i in range(4)] + [(4 + i, 4 + (i + 1) % 4) for i in range(4)] + [(i, i + 4) for i in range(4)]
    return [(c[a], c[b]) for a, b in e]


def segments(room_id):
    r = next(q for q in ROOMS if q["id"] == room_id)
    ink, grey = [], []
    ink += box(r["x0"], r["y0"], r["x1"], r["y1"], 0, CEIL)
    for o in OPENINGS:
        if room_id in o["rooms"]:
            ink += wall_rect(o["axis"], o["c"], o["a0"], o["a1"], 0, o["head"])
    for w in WINDOWS:
        if w["room"] == room_id:
            ink += wall_rect(w["axis"], w["c"], w["a0"], w["a1"], w["sill"], w["head"])
            m = (w["a0"] + w["a1"]) / 2
            ink += wall_rect(w["axis"], w["c"], m, m, w["sill"], w["head"])[:2]
    for f in FURNITURE.get(room_id, []):
        grey += box(*f[:6])
    return ink, grey


def draw(node, W=2048):
    H = W // 2
    img = np.full((H, W), 255, np.uint8)
    cx, cy, ch = node["x"], node["y"], node["h"]

    def proj(p):
        dx, dy, dz = p[0] - cx, p[1] - cy, p[2] - ch
        lon, lat = math.atan2(dx, -dy), math.atan2(dz, math.hypot(dx, dy))
        return (lon / (2 * math.pi) + .5) * W, (.5 - lat / math.pi) * H

    ink, grey = segments(node["room"])
    for segs, col, th in ((grey, 150, 2), (ink, 0, 3)):
        for a, b in segs:
            L = math.dist(a, b)
            if L < 1e-6:
                continue
            n = max(2, int(L * 120))
            pts = [proj([a[k] + (b[k] - a[k]) * t for k in range(3)]) for t in np.linspace(0, 1, n)]
            for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
                if abs(u1 - u0) > W / 2:
                    continue                      # crosses the wrap-around seam
                cv2.line(img, (int(u0), int(v0)), (int(u1), int(v1)), col, th, cv2.LINE_AA)
    return img


if __name__ == "__main__":
    out = sys.argv[1]
    W = int(sys.argv[2]) if len(sys.argv) > 2 else 2048
    os.makedirs(out, exist_ok=True)
    for node in NODES:
        cv2.imwrite(os.path.join(out, f"guide{node['n']:02d}.png"), draw(node, W))
    print(len(NODES), "guides")
