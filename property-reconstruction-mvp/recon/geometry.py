"""Engine C: geometric reconstruction (camera poses + sparse 3D points) with COLMAP.

Matching strategy follows the capture:
  photos only      -> exhaustive (every photo against every photo)
  video only       -> sequential (each keyframe against its next N neighbours)
  video + photos   -> sequential for the video, plus every photo against everything

Mapping is incremental by default. Global mapping (GLOMAP) is available as an experiment: on the test
walk-through it registered 99% of frames in one model, but most camera positions were wrong (median error
about 6 m against the reference), while incremental kept 71% of frames with a 1.8 cm median error.
Registration counts alone are not trusted; see evaluate.py.
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
                focal_factor: float | None = None, overlap: int = 10, max_features: int = 4096,
                mapper: str = "incremental") -> dict:
    """Run feature extraction, matching and mapping. Returns stats + the largest model."""
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

    res = map_database(db, frames_dir, work_dir, names, mapper)
    res["pairs"] = n_pairs
    res["seconds"] = {"features": round(t_feat - t0, 1), "matching": round(t_match - t_feat, 1), **res["seconds"]}
    res["seconds"]["total"] = round(sum(res["seconds"].values()), 1)
    return res


def map_database(db: str, frames_dir: str, work_dir: str, names: list[str], mapper: str = "incremental") -> dict:
    """Poses + points from an already matched database; keeps the largest model in work_dir/model."""
    t0 = time.time()
    out = os.path.join(work_dir, "sparse")
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out)
    models = {}
    if mapper == "global":
        models = pycolmap.global_mapping(db, frames_dir, out)
    if not models:
        mapper = "incremental"
        opts = pycolmap.IncrementalPipelineOptions()
        opts.num_threads = os.cpu_count() or 4
        opts.ba_refine_focal_length = True
        opts.ba_refine_extra_params = True
        models = pycolmap.incremental_mapping(db, frames_dir, out, options=opts)
    t_map = time.time()

    if not models:
        return {"ok": False, "inputs": len(names), "registered": 0, "models": 0, "mapper": mapper,
                "seconds": {"mapping": round(t_map - t0, 1)}}
    best_id = max(models, key=lambda k: models[k].num_reg_images())
    rec = models[best_id]
    best_dir = os.path.join(work_dir, "model")
    os.makedirs(best_dir, exist_ok=True)
    rec.write(best_dir)
    return {
        "ok": True,
        "mapper": mapper,
        "inputs": len(names),
        "registered": rec.num_reg_images(),
        "registered_names": sorted(img.name for img in rec.images.values() if img.has_pose),
        "models": len(models),
        "other_models_images": sorted(m.num_reg_images() for k, m in models.items() if k != best_id),
        "points3D": rec.num_points3D(),
        "mean_reprojection_error": rec.compute_mean_reprojection_error(),
        "cameras": {cid: str(c) for cid, c in rec.cameras.items()},
        "seconds": {"mapping": round(t_map - t0, 1)},
        "model_dir": best_dir,
    }
