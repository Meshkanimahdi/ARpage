"""Run the reconstruction pipeline on one capture.

  python run.py --out OUT [--photos DIR] [--video FILE] [--focal-factor 0.45] [--stages pre,sfm,layout,texture,semantic]

Each stage writes its result into OUT and is skipped when its output already exists (use --force to redo),
so fixing a later stage never re-runs the expensive ones.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from recon import preprocess, geometry  # noqa: E402

IMG_EXT = (".jpg", ".jpeg", ".png", ".heic")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--photos")
    ap.add_argument("--video")
    ap.add_argument("--focal-factor", type=float, default=None)
    ap.add_argument("--stages", default="pre,sfm,layout,texture")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    stages = a.stages.split(",")
    frames_dir = os.path.join(a.out, "frames")
    log = {}

    rep_path = os.path.join(a.out, "quality_report.json")
    if "pre" in stages and (a.force or not os.path.exists(rep_path)):
        t = time.time()
        frames, vstats = [], None
        if a.photos:
            paths = sorted(os.path.join(a.photos, f) for f in os.listdir(a.photos) if f.lower().endswith(IMG_EXT))
            frames += preprocess.ingest_photos(paths, frames_dir)
        if a.video:
            vf, vstats = preprocess.ingest_video(a.video, frames_dir)
            frames += vf
        preprocess.write_report(frames, vstats, rep_path)
        log["pre_seconds"] = round(time.time() - t, 1)
    rep = json.load(open(rep_path))
    usable = [f for f in rep["frames"] if "duplicate" not in f["flags"]]
    video = [f["name"] for f in usable if f["kind"] == "video"]
    photos = [f["name"] for f in usable if f["kind"] == "photo"]

    sfm_path = os.path.join(a.out, "sfm.json")
    if "sfm" in stages and (a.force or not os.path.exists(sfm_path)):
        res = geometry.reconstruct(frames_dir, os.path.join(a.out, "colmap"), video, photos, a.focal_factor)
        json.dump(res, open(sfm_path, "w"), indent=1)
    sfm = json.load(open(sfm_path)) if os.path.exists(sfm_path) else None

    if "layout" in stages and sfm and sfm.get("ok"):
        from recon import layout
        layout.build(sfm["model_dir"], a.out, frames_dir)
    if "texture" in stages and sfm and sfm.get("ok"):
        from recon import texture
        texture.build(sfm["model_dir"], a.out, frames_dir)
    if "semantic" in stages and sfm and sfm.get("ok"):
        from recon import semantic
        semantic.build(a.out, frames_dir)

    print(json.dumps({"log": log, "frames": rep["counts"], "video": rep["video"],
                      "sfm": {k: v for k, v in (sfm or {}).items() if k in ("ok", "inputs", "registered", "models", "points3D", "mean_reprojection_error", "seconds")}},
                     indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
