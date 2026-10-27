"""Package one run for the web viewer.

  python export_web.py RUN_DIR OUT_DIR [--stations 40] [--metrics results.json --metrics-key B]

Copies scene.json, the real-pixel textures and the point cloud, and picks a spread-out set of camera
stations whose original frames are saved as viewer photos (the viewer shows these as they were captured).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil

import cv2
import numpy as np


def pick_stations(cams, n, min_gap=0.9):
    """Greedy farthest-point choice over camera positions, so stations cover every room."""
    pos = np.array([c["pos"] for c in cams])
    chosen = [0]
    d = np.linalg.norm(pos - pos[0], axis=1)
    while len(chosen) < n:
        k = int(d.argmax())
        if d[k] < min_gap:
            break
        chosen.append(k)
        d = np.minimum(d, np.linalg.norm(pos - pos[k], axis=1))
    return sorted(chosen)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("out")
    ap.add_argument("--stations", type=int, default=40)
    ap.add_argument("--metrics")
    ap.add_argument("--metrics-key")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "photos"), exist_ok=True)
    scene = json.load(open(os.path.join(a.run, "scene.json")))
    for r in scene["rooms"]:
        r["evidence_images"] = r["evidence_images"][:5]
    st = pick_stations(scene["cameras"], a.stations)
    for k in st:
        c = scene["cameras"][k]
        img = cv2.imread(os.path.join(a.run, "frames", c["name"]))
        s = 960 / max(img.shape[:2])
        img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        cv2.imwrite(os.path.join(a.out, "photos", c["name"]), img, [cv2.IMWRITE_JPEG_QUALITY, 80])
        c["station"] = True
    if a.metrics:
        scene["metrics"] = json.load(open(a.metrics))[a.metrics_key]
    json.dump(scene, open(os.path.join(a.out, "scene.json"), "w"), separators=(",", ":"))
    if os.path.isdir(os.path.join(a.out, "tex")):
        shutil.rmtree(os.path.join(a.out, "tex"))
    shutil.copytree(os.path.join(a.run, "tex"), os.path.join(a.out, "tex"))
    shutil.copy(os.path.join(a.run, "points.f32"), a.out)
    print(f"{len(st)} stations -> {a.out}")


if __name__ == "__main__":
    main()
