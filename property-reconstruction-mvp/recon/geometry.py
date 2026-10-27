"""Engine C: geometric reconstruction (camera poses + sparse 3D points) with COLMAP.

Matching strategy follows the capture:
  photos only      -> exhaustive (every photo against every photo)
  video only       -> sequential (each keyframe against its next N neighbours)
  video + photos   -> sequential for the video, plus every photo against everything
"""
from __future__ import annotations

import os
import shutil
import time

import pycolmap
from PIL import Image


def _write_pairs(path: str, video: list[str], photos: list[str], overlap: int) -> int:
    pairs = set()
    for i, a in enumerate(video):
        for b in video[i + 1:i + 1 + overlap]:
            pairs.add((a, b))
    for i, p in enumerate(photos):
        for q in photos[i + 1:]:
            pairs.add((p, q))
        for v in video:
            pairs.add((p, v))
    with open(path, "w") as fp:
        fp.writelines(f"{a} {b}\n" for a, b in sorted(pairs))
    return len(pairs)


def reconstruct(frames_dir: str, work_dir: str, video: list[str], photos: list[str],
                focal_factor: float | None = None, overlap: int = 10, max_features: int = 4096) -> dict:
    """Run feature extraction, matching and incremental mapping. Returns stats + the largest model."""
    t0 = time.time()
    if os.path.exists(work_dir):
        shutil.rmtree(work_dir)
    os.makedirs(work_dir)
    db = os.path.join(work_dir, "database.db")
    names = video + photos

    ext = pycolmap.FeatureExtractionOptions()
    ext.max_image_size = 1600
    ext.sift.max_num_features = max_features
    ext.num_threads = os.cpu_count() or 4

    # Phones write the focal length into EXIF; when it is missing we start from a prior and let BA refine it.
    def extract(group: list[str]) -> None:
        if not group:
            return
        reader = pycolmap.ImageReaderOptions()
        reader.camera_model = "SIMPLE_RADIAL"
        if focal_factor:
            w, h = Image.open(os.path.join(frames_dir, group[0])).size
            reader.camera_params = f"{focal_factor * w:.1f},{w / 2:.1f},{h / 2:.1f},0"
        pycolmap.extract_features(db, frames_dir, image_names=group, camera_mode=pycolmap.CameraMode.SINGLE,
                                  reader_options=reader, extraction_options=ext)
    extract(video)
    extract(photos)        # photos and video come from different capture modes: separate cameras
    t_feat = time.time()

    match = pycolmap.FeatureMatchingOptions()
    match.num_threads = os.cpu_count() or 4
    if video and not photos:
        seq = pycolmap.SequentialPairingOptions()
        seq.overlap = overlap
        seq.quadratic_overlap = True
        pycolmap.match_sequential(db, matching_options=match, pairing_options=seq)
        n_pairs = None
    elif photos and not video:
        pycolmap.match_exhaustive(db, matching_options=match)
        n_pairs = len(photos) * (len(photos) - 1) // 2
    else:
        pairs_path = os.path.join(work_dir, "pairs.txt")
        n_pairs = _write_pairs(pairs_path, video, photos, overlap)
        imp = pycolmap.ImportedPairingOptions()
        imp.match_list_path = pairs_path
        pycolmap.match_image_pairs(db, matching_options=match, pairing_options=imp)
    t_match = time.time()

    opts = pycolmap.IncrementalPipelineOptions()
    opts.num_threads = os.cpu_count() or 4
    opts.ba_refine_focal_length = True
    opts.ba_refine_extra_params = True
    models = pycolmap.incremental_mapping(db, frames_dir, os.path.join(work_dir, "sparse"), options=opts)
    t_map = time.time()

    if not models:
        return {"ok": False, "inputs": len(names), "registered": 0, "models": 0,
                "seconds": {"features": t_feat - t0, "matching": t_match - t_feat, "mapping": t_map - t_match}}
    best_id = max(models, key=lambda k: models[k].num_reg_images())
    rec = models[best_id]
    best_dir = os.path.join(work_dir, "model")
    os.makedirs(best_dir, exist_ok=True)
    rec.write(best_dir)
    return {
        "ok": True,
        "inputs": len(names),
        "registered": rec.num_reg_images(),
        "registered_names": sorted(img.name for img in rec.images.values() if img.has_pose),
        "models": len(models),
        "other_models_images": sorted(m.num_reg_images() for k, m in models.items() if k != best_id),
        "points3D": rec.num_points3D(),
        "mean_reprojection_error": rec.compute_mean_reprojection_error(),
        "pairs": n_pairs,
        "cameras": {cid: str(c) for cid, c in rec.cameras.items()},
        "seconds": {"features": round(t_feat - t0, 1), "matching": round(t_match - t_feat, 1),
                    "mapping": round(t_map - t_match, 1), "total": round(t_map - t0, 1)},
        "model_dir": best_dir,
    }
