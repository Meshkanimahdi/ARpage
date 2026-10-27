"""Engine A: media preprocessing.

Photos: fix orientation from EXIF, downscale, score quality, drop near-duplicates.
Video: decode with FFmpeg, then pick keyframes by sharpness and camera motion
(not a fixed time step), so the geometry engine gets views with parallax.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass, asdict, field

import cv2
import numpy as np
from PIL import Image, ImageOps

MAX_SIDE = 1600


@dataclass
class FrameInfo:
    name: str               # file name inside the frames dir
    source: str             # original file
    kind: str               # "photo" | "video"
    index: int              # frame index in the video, or photo order
    sharpness: float
    brightness: float
    flags: list = field(default_factory=list)


def _sharpness(gray: np.ndarray) -> float:
    small = cv2.resize(gray, (512, int(512 * gray.shape[0] / gray.shape[1])))
    return float(cv2.Laplacian(small, cv2.CV_64F).var())


def _dhash(gray: np.ndarray) -> int:
    small = cv2.resize(gray, (9, 8), interpolation=cv2.INTER_AREA)
    bits = (small[:, 1:] > small[:, :-1]).flatten()
    return int("".join("1" if b else "0" for b in bits), 2)


def _save(img: Image.Image, path: str) -> np.ndarray:
    img = img.convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)
    img.save(path, quality=92)
    return cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY)


def ingest_photos(paths: list[str], out_dir: str) -> list[FrameInfo]:
    os.makedirs(out_dir, exist_ok=True)
    frames, hashes = [], []
    for i, p in enumerate(paths):
        img = ImageOps.exif_transpose(Image.open(p))
        name = os.path.basename(p)
        gray = _save(img, os.path.join(out_dir, name))
        info = FrameInfo(name, p, "photo", i, _sharpness(gray), float(gray.mean()))
        h = _dhash(gray)
        if any(bin(h ^ o).count("1") <= 4 for o in hashes):
            info.flags.append("duplicate")
        hashes.append(h)
        frames.append(info)
    _flag_quality(frames)
    return frames


def _median_flow(prev: np.ndarray, cur: np.ndarray) -> tuple[float, float]:
    """Median optical-flow displacement (fraction of width) and tracked ratio."""
    pts = cv2.goodFeaturesToTrack(prev, 400, 0.01, 8)
    if pts is None or len(pts) < 20:
        return 1.0, 0.0
    nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, cur, pts, None, winSize=(21, 21), maxLevel=4)
    ok = st.flatten() == 1
    if ok.sum() < 10:
        return 1.0, float(ok.mean())
    d = np.linalg.norm((nxt - pts).reshape(-1, 2)[ok], axis=1)
    return float(np.median(d) / prev.shape[1]), float(ok.mean())


def ingest_video(path: str, out_dir: str, min_motion=0.06, max_motion=0.18, analysis_width=480) -> tuple[list[FrameInfo], dict]:
    """Decode every frame, keep a keyframe whenever the camera has moved enough.

    min_motion: keep a new keyframe once median flow since the last one exceeds this fraction of width.
    max_motion: if the jump between consecutive frames exceeds this, the video is moving too fast (flagged).
    """
    os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix="frames_")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-i", path, "-vsync", "0",
                    "-vf", f"scale='min({MAX_SIDE},iw)':-2", "-q:v", "2", os.path.join(tmp, "f_%05d.jpg")], check=True)
    files = sorted(os.listdir(tmp))
    grays, sharp = [], []
    for f in files:
        g = cv2.imread(os.path.join(tmp, f), cv2.IMREAD_GRAYSCALE)
        sharp.append(_sharpness(g))
        h = int(analysis_width * g.shape[0] / g.shape[1])
        grays.append(cv2.resize(g, (analysis_width, h)))
    sharp = np.array(sharp)
    blur_cut = 0.35 * np.median(sharp)

    keep, last, fast_jumps = [], None, 0
    window = []                       # candidates since the last keyframe
    for i in range(len(files)):
        if i > 0:
            jump, _ = _median_flow(grays[i - 1], grays[i])
            if jump > max_motion:
                fast_jumps += 1
        if sharp[i] < blur_cut:
            continue
        if last is None:
            keep.append(i); last = i; continue
        motion, tracked = _median_flow(grays[last], grays[i])
        window.append(i)
        if motion >= min_motion or tracked < 0.5:
            # pick the sharpest frame among recent candidates so we don't keep a blurred one
            best = max(window[-4:], key=lambda k: sharp[k])
            if best != last:
                keep.append(best); last = best
            window = []

    frames = []
    for i in keep:
        name = f"video_{i:05d}.jpg"
        os.replace(os.path.join(tmp, files[i]), os.path.join(out_dir, name))
        g = grays[i]
        frames.append(FrameInfo(name, path, "video", i, float(sharp[i]), float(g.mean())))
    for f in os.listdir(tmp):
        os.remove(os.path.join(tmp, f))
    os.rmdir(tmp)
    stats = {"decoded_frames": len(files), "keyframes": len(keep),
             "blurry_dropped": int((sharp < blur_cut).sum()), "too_fast_jumps": fast_jumps}
    _flag_quality(frames)
    return frames, stats


def _flag_quality(frames: list[FrameInfo]) -> None:
    if not frames:
        return
    med = np.median([f.sharpness for f in frames])
    for f in frames:
        if f.sharpness < 0.35 * med:
            f.flags.append("blurry")
        if f.brightness < 45:
            f.flags.append("dark")
        if f.brightness > 225:
            f.flags.append("overexposed")


def write_report(frames: list[FrameInfo], video_stats: dict | None, path: str) -> dict:
    rep = {
        "frames": [asdict(f) for f in frames],
        "counts": {
            "photos": sum(f.kind == "photo" for f in frames),
            "video_keyframes": sum(f.kind == "video" for f in frames),
            "flagged": {flag: sum(flag in f.flags for f in frames) for flag in ["blurry", "dark", "overexposed", "duplicate"]},
        },
        "video": video_stats,
    }
    with open(path, "w") as fp:
        json.dump(rep, fp, indent=1)
    return rep
