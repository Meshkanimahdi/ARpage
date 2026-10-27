"""Engine D: appearance from real pixels only (Reality First).

Every texel of the floor and of each wall is projected into the captured frames and takes its colour from
the single best real view: same room as the surface, in front of the camera, closest and most head-on.
No generated texture is used anywhere. Texels no camera saw stay neutral grey and are counted as
"not covered", so the viewer can label them instead of inventing them.
"""
from __future__ import annotations

import json
import math
import os

import cv2
import numpy as np
import pycolmap

FLOOR_RES = 0.02     # metres per floor texel
WALL_RES = 0.025     # metres per wall texel
UNCOVERED = (154, 154, 154)


class Frames:
    """Lazy cache of the captured frames used for projection."""
    def __init__(self, frames_dir):
        self.dir, self.cache = frames_dir, {}

    def get(self, name):
        if name not in self.cache:
            self.cache[name] = cv2.imread(os.path.join(self.dir, name))
        return self.cache[name]


def plan_to_world(scene, x, y, z):
    f, s = scene["frame"], scene["scale"]["meters_per_unit"]
    th = f["theta"]
    q0 = math.cos(th) * x - math.sin(th) * y
    q1 = math.sin(th) * x + math.cos(th) * y
    e1, e2, up = (np.array(f[k]) for k in ("e1", "e2", "up"))
    return (np.multiply.outer(q0, e1) + np.multiply.outer(q1, e2)) / s + np.multiply.outer(f["floor_h"] + z / s, up)


def _project(rec, im, Xw):
    T = im.cam_from_world()
    Xc = Xw @ T.rotation.matrix().T + T.translation
    cam = rec.cameras[im.camera_id]
    front = Xc[:, 2] > 0.05
    uv = np.full((len(Xw), 2), -1.0)
    if front.any():
        uv[front] = cam.img_from_cam(Xc[front])
    inside = front & (uv[:, 0] >= 1) & (uv[:, 1] >= 1) & (uv[:, 0] < cam.width - 2) & (uv[:, 1] < cam.height - 2)
    return Xc, uv, inside


def _bake(rec, imgs, frames, Xw, normal, eligible_cams, shape):
    """Pick, for every texel, the best eligible camera and sample its pixel."""
    n = len(Xw)
    best = np.full(n, np.inf)
    who = np.full(n, -1)
    uv_best = np.zeros((n, 2), np.float32)
    for k in eligible_cams:
        im = imgs[k]
        Xc, uv, inside = _project(rec, im, Xw)
        if not inside.any():
            continue
        C = im.projection_center()
        ray = Xw - C
        dist = np.linalg.norm(ray, axis=1)
        cosang = np.abs(ray @ normal) / np.maximum(dist, 1e-6)
        score = dist / np.maximum(cosang, 0.15)            # closer and more head-on is better
        better = inside & (score < best)
        best[better], who[better], uv_best[better] = score[better], k, uv[better]
    out = np.zeros((n, 3), np.uint8)
    out[:] = UNCOVERED
    for k in np.unique(who[who >= 0]):
        sel = who == k
        img = frames.get(imgs[k].name)
        cam = rec.cameras[imgs[k].camera_id]
        sx, sy = img.shape[1] / cam.width, img.shape[0] / cam.height
        m = uv_best[sel] * [sx, sy]
        out[sel] = cv2.remap(img, m[:, 0:1].astype(np.float32), m[:, 1:2].astype(np.float32),
                             cv2.INTER_LINEAR).reshape(-1, 3)
    return out.reshape(shape + (3,)), float((who >= 0).mean()), np.bincount(who[who >= 0], minlength=len(imgs))


def build(model_dir: str, out_dir: str, frames_dir: str) -> dict:
    scene = json.load(open(os.path.join(out_dir, "scene.json")))
    rec = pycolmap.Reconstruction(model_dir)
    imgs = [im for im in rec.images.values() if im.has_pose]
    name_to_k = {im.name: k for k, im in enumerate(imgs)}
    frames = Frames(frames_dir)
    tex_dir = os.path.join(out_dir, "tex")
    os.makedirs(tex_dir, exist_ok=True)
    up = np.array(scene["frame"]["up"])
    cams_by_room = {}
    for c in scene["cameras"]:
        cams_by_room.setdefault(c["room"], []).append(name_to_k[c["name"]])

    # floor: one top-down mosaic over the plan bounds, each texel from a camera in its own room
    room_lab = np.load(os.path.join(out_dir, "room_labels.npy"))
    mn, mx = np.array(scene["bounds"]["min"]), np.array(scene["bounds"]["max"])
    Wf, Hf = np.ceil((mx - mn) / FLOOR_RES).astype(int)
    xs = mn[0] + (np.arange(Wf) + 0.5) * FLOOR_RES
    ys = mn[1] + (np.arange(Hf) + 0.5) * FLOOR_RES
    gx, gy = np.meshgrid(xs, ys)
    lab_res = 0.05
    li = np.clip(((gy - mn[1]) / lab_res).astype(int), 0, room_lab.shape[0] - 1)
    lj = np.clip(((gx - mn[0]) / lab_res).astype(int), 0, room_lab.shape[1] - 1)
    tex_lab = room_lab[li, lj]
    floor_img = np.zeros((Hf, Wf, 3), np.uint8); floor_img[:] = UNCOVERED
    covered = np.zeros((Hf, Wf), bool)
    use = np.zeros(len(imgs))
    for r in scene["rooms"]:
        sel = tex_lab == r["label"]
        if not sel.any():
            continue
        Xw = plan_to_world(scene, gx[sel], gy[sel], np.zeros(sel.sum()))
        cams = cams_by_room.get(r["id"], [])
        colors, cov, u = _bake(rec, imgs, frames, Xw, up, cams, (int(sel.sum()),))
        floor_img[sel] = colors
        covered[sel] = np.any(colors != UNCOVERED, axis=1)
        use += u
    floor_img[tex_lab == 0] = (250, 250, 250)
    cv2.imwrite(os.path.join(tex_dir, "floor.jpg"), cv2.flip(floor_img, 0), [cv2.IMWRITE_JPEG_QUALITY, 88])
    floor_cov = float(covered[tex_lab > 0].mean()) if (tex_lab > 0).any() else 0.0

    # walls: one texture per wall segment, from cameras in the wall's room that face it
    wall_cov = []
    for w in scene["walls"]:
        a, b = np.array(w["a"]), np.array(w["b"])
        L = np.linalg.norm(b - a)
        nw, nh = max(2, int(L / WALL_RES)), max(2, int(w["height"] / WALL_RES))
        t = (np.arange(nw) + 0.5) / nw
        z = w["height"] - (np.arange(nh) + 0.5) * WALL_RES               # image row 0 = top of wall
        tx, tz = np.meshgrid(t, z)
        px = a[0] + (b[0] - a[0]) * tx
        py = a[1] + (b[1] - a[1]) * tx
        Xw = plan_to_world(scene, px.ravel(), py.ravel(), tz.ravel())
        n2 = np.array(w["normal"])
        th = scene["frame"]["theta"]
        q = np.array([math.cos(th) * n2[0] - math.sin(th) * n2[1], math.sin(th) * n2[0] + math.cos(th) * n2[1]])
        nworld = q[0] * np.array(scene["frame"]["e1"]) + q[1] * np.array(scene["frame"]["e2"])
        cams = []
        for k in cams_by_room.get(w["room"], []):
            c = next(c for c in scene["cameras"] if c["name"] == imgs[k].name)
            to_cam = np.array(c["pos"]) - (a + b) / 2
            if to_cam @ n2 > 0.1:                                  # camera is on the room side of the wall
                cams.append(k)
        img, cov, u = _bake(rec, imgs, frames, Xw, nworld, cams, (nh, nw))
        use += u
        name = f"{w['id']}.jpg"
        cv2.imwrite(os.path.join(tex_dir, name), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        w["texture"] = f"tex/{name}"
        w["coverage"] = round(cov, 3)
        wall_cov.append((cov, L))

    tot = sum(L for _, L in wall_cov) or 1
    scene["appearance"] = {
        "method": "per-texel projection of captured frames onto floor and wall planes",
        "floor_texture": "tex/floor.jpg", "floor_res": FLOOR_RES,
        "floor_coverage": round(floor_cov, 3),
        "wall_coverage": round(sum(c * L for c, L in wall_cov) / tot, 3),
        "frames_used": int((use > 0).sum()), "frames_available": len(imgs),
        "generated_pixels": 0,
    }
    json.dump(scene, open(os.path.join(out_dir, "scene.json"), "w"), indent=1)
    return scene["appearance"]
