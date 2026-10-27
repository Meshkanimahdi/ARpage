"""Layout: from camera poses + sparse points to a floor plan and a spatial scene graph.

Everything here is computed from geometry; nothing is guessed by a language model.
  1. up direction  = average "up" of the cameras (people hold phones upright)
  2. floor height  = lowest dense layer of points below the cameras
  3. scale         = assumed eye height of the capture (labelled "estimated") unless a reference is given
  4. wall axes     = dominant line direction of mid-height points (Manhattan assumption)
  5. free space    = floor points + lines of sight from cameras to the floor points they observe
  6. rooms         = free space split at narrow passages (doorways) with a distance-transform watershed
"""
from __future__ import annotations

import json
import math
import os

import cv2
import numpy as np
import pycolmap

RES = 0.05            # metres per plan cell
EYE_HEIGHT = 1.5      # assumed lens height above the floor when no reference measurement exists
MIN_JOG = 0.35        # outline steps shorter than this are treated as noise, not as a wall corner
DOOR_HALF = 0.55      # half the narrowest passage kept inside one room; sweep on the reference (0.5-0.7) settled here


def load(model_dir: str):
    rec = pycolmap.Reconstruction(model_dir)
    imgs = [im for im in rec.images.values() if im.has_pose]
    pts = {pid: p for pid, p in rec.points3D.items() if p.error < 2.0 and p.track.length() >= 3}
    return rec, imgs, pts


def frame_from(imgs, pts):
    C = np.array([im.projection_center() for im in imgs])
    R = np.array([im.cam_from_world().rotation.matrix() for im in imgs])
    up = -R[:, 1, :].mean(axis=0)
    up /= np.linalg.norm(up)
    e1 = np.cross(up, [1.0, 0, 0]) if abs(up[0]) < 0.9 else np.cross(up, [0, 1.0, 0])
    e1 /= np.linalg.norm(e1)
    e2 = np.cross(up, e1)
    P = np.array([p.xyz for p in pts.values()])
    return C, R, up, e1, e2, P


def _lowest_peak(h, lo, hi, bins=90, frac=0.25):
    hist, edges = np.histogram(h[(h > lo) & (h < hi)], bins=bins, range=(lo, hi))
    if hist.max() == 0:
        return None
    sm = np.convolve(hist, [1, 2, 1], "same")
    for i in range(1, len(sm) - 1):
        if sm[i] >= frac * sm.max() and sm[i] >= sm[i - 1] and sm[i] >= sm[i + 1]:
            return 0.5 * (edges[i] + edges[i + 1])
    return None


def build(model_dir: str, out_dir: str, frames_dir: str | None = None, eye_height: float = EYE_HEIGHT,
          reference_scale: float | None = None) -> dict:
    rec, imgs, pts = load(model_dir)
    C, R, up, e1, e2, P = frame_from(imgs, pts)
    hP, hC = P @ up, C @ up
    cam_h = np.median(hC)
    spread = np.percentile(hC, 90) - np.percentile(hC, 10) + 1e-6
    lo = np.percentile(hP, 0.5)
    floor_h = _lowest_peak(hP, lo, cam_h - 0.2 * (cam_h - lo))
    if floor_h is None:
        floor_h = np.percentile(hP, 2)
    rel_eye = cam_h - floor_h
    if reference_scale:
        s, scale_src = reference_scale, "reference measurement"
    else:
        s, scale_src = eye_height / rel_eye, f"assumed lens height {eye_height} m"

    # ceiling: highest dense layer above the cameras (often missing: plain ceilings have no features)
    ceil_h = None
    up_pts = hP[hP > cam_h]
    if len(up_pts) > 200:
        hi = np.percentile(up_pts, 99.5)
        hist, edges = np.histogram(up_pts, bins=60, range=(cam_h, hi))
        sm = np.convolve(hist, [1, 2, 1], "same")
        for i in range(len(sm) - 2, 0, -1):
            if sm[i] >= 0.25 * sm.max() and sm[i] >= sm[i - 1] and sm[i] >= sm[i + 1]:
                ceil_h = 0.5 * (edges[i] + edges[i + 1]); break
    ceiling_m = (ceil_h - floor_h) * s if ceil_h is not None else None
    ceiling_src = "measured from points"
    if ceiling_m is None or not (2.2 <= ceiling_m <= 4.2):
        ceiling_m, ceiling_src = 2.7, "assumed (ceiling not reconstructed)"

    # plan coordinates (metres), before Manhattan rotation
    def to_q(X):
        return np.stack([X @ e1, X @ e2], axis=-1) * s
    zP = (hP - floor_h) * s
    qP, qC = to_q(P), to_q(C)

    # Manhattan rotation from mid-height points
    band = (zP > 0.5) & (zP < min(2.0, ceiling_m - 0.3))
    theta = _dominant_angle(qP[band])
    rot = np.array([[math.cos(theta), math.sin(theta)], [-math.sin(theta), math.cos(theta)]])
    xyP, xyC = qP @ rot.T, qC @ rot.T

    floor_band = np.abs(zP) < 0.12
    keep = np.concatenate([xyP[floor_band], xyC])
    mn = np.percentile(keep, 0.5, axis=0) - 0.6
    mx = np.percentile(keep, 99.5, axis=0) + 0.6
    W, H = (np.ceil((mx - mn) / RES)).astype(int)
    to_px = lambda xy: np.floor((xy - mn) / RES).astype(int)

    # 1) floor points
    floor_occ = np.zeros((H, W), np.uint8)
    fp = to_px(xyP[floor_band])
    ok = (fp[:, 0] >= 0) & (fp[:, 0] < W) & (fp[:, 1] >= 0) & (fp[:, 1] < H)
    floor_occ[fp[ok, 1], fp[ok, 0]] = 1
    # 2) lines of sight on the floor: camera ground position -> each floor point it observes
    pid_list = list(pts.keys())
    cam_px = to_px(xyC)
    id_to_k = {im.image_id: k for k, im in enumerate(imgs)}
    starts, ends = [], []
    for i, pid in enumerate(pid_list):
        if not floor_band[i]:
            continue
        for el in pts[pid].track.elements[:6]:
            k = id_to_k.get(el.image_id)
            if k is not None:
                starts.append(cam_px[k]); ends.append(i)
    rays = np.zeros((H, W), np.uint16)
    if len(starts) > 150_000:                      # cap the work on very large captures
        pick = np.random.default_rng(0).choice(len(starts), 150_000, replace=False)
        starts, ends = [starts[i] for i in pick], [ends[i] for i in pick]
    if starts:
        A = np.array(starts, float)
        B = to_px(xyP[np.array(ends)]).astype(float)
        n = np.maximum(1, np.ceil(np.abs(B - A).max(axis=1))).astype(int)
        seg = np.repeat(np.arange(len(n)), n)
        t = (np.arange(n.sum()) - np.repeat(np.cumsum(n) - n, n)) / np.repeat(n, n)
        px = np.round(A[seg] + (B[seg] - A[seg]) * t[:, None]).astype(int)
        ok = (px[:, 0] >= 0) & (px[:, 0] < W) & (px[:, 1] >= 0) & (px[:, 1] < H)
        # count each ray once per cell
        key = np.unique(np.stack([seg[ok], px[ok, 1] * W + px[ok, 0]], 1), axis=0)[:, 1]
        np.add.at(rays.reshape(-1), key, 1)
    walls_occ = np.zeros((H, W), np.uint16)
    wp = to_px(xyP[band])
    ok = (wp[:, 0] >= 0) & (wp[:, 0] < W) & (wp[:, 1] >= 0) & (wp[:, 1] < H)
    np.add.at(walls_occ, (wp[ok, 1], wp[ok, 0]), 1)
    walls = (cv2.GaussianBlur(walls_occ.astype(np.float32), (0, 0), 1.0) > 0.6).astype(np.uint8)

    free = ((rays >= 2) | (floor_occ > 0)).astype(np.uint8)
    for (cx, cy) in cam_px:
        cv2.circle(free, (int(cx), int(cy)), int(0.35 / RES), 1, -1)
    k3 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (int(0.3 / RES) | 1, int(0.3 / RES) | 1))
    free = cv2.morphologyEx(free, cv2.MORPH_CLOSE, k3)
    # walls cut the free space after closing, so a thin wall is never bridged
    free[cv2.dilate(walls, np.ones((3, 3), np.uint8)) > 0] = 0
    free = cv2.morphologyEx(free, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)))
    free = _fill_holes(free)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(free)
    cam_labels = {lab[cy, cx] for cx, cy in cam_px if 0 <= cx < W and 0 <= cy < H}
    free = np.isin(lab, [l for l in cam_labels if l != 0]).astype(np.uint8)

    # rooms: split free space at doorway-width necks
    dist = cv2.distanceTransform(free, cv2.DIST_L2, 5) * RES
    seeds = (dist > DOOR_HALF).astype(np.uint8)
    n, seed_lab, st, _ = cv2.connectedComponentsWithStats(seeds)
    markers = np.zeros((H, W), np.int32)
    rid = 0
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] * RES * RES >= 1.0:
            rid += 1
            markers[seed_lab == i] = rid
    markers[free == 0] = -1 if rid else 0
    room_lab = np.zeros((H, W), np.int32)
    if rid:
        ws_img = cv2.cvtColor((255 * (1 - np.clip(dist / dist.max(), 0, 1))).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        mk = markers.copy(); mk[mk < 0] = 0
        mk[(free == 0)] = rid + 1          # background marker
        cv2.watershed(ws_img, mk)
        room_lab = np.where((mk >= 1) & (mk <= rid) & (free > 0), mk, 0)
        room_lab = _merge_small(room_lab, min_area=2.0 / (RES * RES))

    rooms, walls_out, doors = [], [], []
    labels = [l for l in np.unique(room_lab) if l > 0]
    cam_room = {}
    for k, (cx, cy) in enumerate(cam_px):
        if 0 <= cx < W and 0 <= cy < H:
            cam_room[k] = int(room_lab[cy, cx])
    to_m = lambda px: (np.asarray(px, float) + 0.5) * RES + mn
    for idx, l in enumerate(labels, 1):
        mask = (room_lab == l).astype(np.uint8)
        cs, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        c = max(cs, key=cv2.contourArea)
        poly = _rectilinear(cv2.approxPolyDP(c, 0.12 / RES, True).reshape(-1, 2).astype(float))
        poly_m = [list(map(lambda v: round(float(v), 3), to_m(p))) for p in poly]
        area = float(mask.sum()) * RES * RES
        ev = [imgs[k].name for k, r in cam_room.items() if r == l]
        rooms.append({"id": f"r{idx}", "label": int(l), "polygon": poly_m, "area_m2": round(area, 2),
                      "source": "computed", "confidence": round(min(1.0, len(ev) / 8), 2), "evidence_images": ev[:40],
                      "camera_count": len(ev)})
    lab_to_id = {r["label"]: r["id"] for r in rooms}

    # doors: where two rooms touch
    for a in labels:
        da = cv2.dilate((room_lab == a).astype(np.uint8), np.ones((3, 3), np.uint8))
        for b in labels:
            if b <= a:
                continue
            touch = np.argwhere((da > 0) & (room_lab == b))
            if len(touch) < 4:
                continue
            ys, xs = touch[:, 0], touch[:, 1]
            ext = max(np.ptp(xs), np.ptp(ys)) * RES
            ctr = to_m([xs.mean(), ys.mean()])
            doors.append({"id": f"d{len(doors) + 1}", "rooms": [lab_to_id[a], lab_to_id[b]],
                          "center": [round(float(v), 3) for v in ctr], "width": round(float(ext), 2),
                          "axis": "x" if np.ptp(xs) >= np.ptp(ys) else "y", "source": "computed"})

    # walls: room outline edges, normals pointing into the room, door gaps cut out
    for r in rooms:
        poly = np.array(r["polygon"])
        area_sign = np.sign(_signed_area(poly))
        for i in range(len(poly)):
            a, b = poly[i], poly[(i + 1) % len(poly)]
            d = b - a
            L = np.linalg.norm(d)
            if L < 0.2:
                continue
            n_ = np.array([-d[1], d[0]]) / L * area_sign      # left normal for CCW polygons = interior
            segs = _cut_doors(a, b, [dd for dd in doors if r["id"] in dd["rooms"]])
            for (sa, sb) in segs:
                if np.linalg.norm(sb - sa) < 0.15:
                    continue
                walls_out.append({"id": f"w{len(walls_out) + 1}", "room": r["id"],
                                  "a": [round(float(v), 3) for v in sa], "b": [round(float(v), 3) for v in sb],
                                  "normal": [round(float(v), 3) for v in n_], "height": ceiling_m, "source": "computed"})

    # cameras in plan coordinates
    cams = []
    for k, im in enumerate(imgs):
        Rk = R[k]
        fwd = Rk[2, :]
        f2 = np.array([fwd @ e1, fwd @ e2]) @ rot.T
        cam = rec.cameras[im.camera_id]
        fy = cam.params[0] if cam.model.name.startswith("SIMPLE") else cam.params[1]
        cams.append({"name": im.name, "pos": [round(float(v), 3) for v in xyC[k]], "height": round(float((hC[k] - floor_h) * s), 3),
                     "yaw": round(math.degrees(math.atan2(f2[1], f2[0])), 2),
                     "pitch": round(math.degrees(math.asin(float(np.clip(fwd @ up, -1, 1)))), 2),
                     "fov_y": round(math.degrees(2 * math.atan(cam.height / (2 * fy))), 2),
                     "aspect": round(cam.width / cam.height, 4),
                     "room": lab_to_id.get(cam_room.get(k, 0)), "kind": "video" if im.name.startswith("video_") else "photo"})

    scene = {
        "version": 1, "units": "m",
        "scale": {"meters_per_unit": s, "source": scale_src, "confidence": "estimated" if not reference_scale else "measured"},
        "frame": {"up": up.tolist(), "e1": e1.tolist(), "e2": e2.tolist(), "theta": theta, "floor_h": float(floor_h)},
        "ceiling": {"height": round(ceiling_m, 2), "source": ceiling_src},
        "bounds": {"min": mn.tolist(), "max": mx.tolist()},
        "rooms": rooms, "walls": walls_out, "doors": doors, "cameras": cams,
        "stats": {"points_used": int(len(P)), "floor_points": int(floor_band.sum()), "wall_points": int(band.sum()),
                  "free_area_m2": round(float(free.sum()) * RES * RES, 2)},
    }
    os.makedirs(out_dir, exist_ok=True)
    json.dump(scene, open(os.path.join(out_dir, "scene.json"), "w"), indent=1)
    np.save(os.path.join(out_dir, "free_mask.npy"), free)
    np.save(os.path.join(out_dir, "room_labels.npy"), room_lab)
    _export_points(xyP, zP, np.array([p.color for p in pts.values()]), out_dir)
    _debug_png(free, walls, room_lab, cam_px, rooms, doors, mn, os.path.join(out_dir, "plan_debug.png"))
    return scene


def _dominant_angle(xy: np.ndarray) -> float:
    if len(xy) < 50:
        return 0.0
    mn = xy.min(0)
    sz = np.ceil((xy.max(0) - mn) / RES).astype(int) + 1
    img = np.zeros((sz[1], sz[0]), np.float32)
    p = np.floor((xy - mn) / RES).astype(int)
    np.add.at(img, (p[:, 1], p[:, 0]), 1)
    img = cv2.GaussianBlur(img, (0, 0), 1.5)
    gx, gy = cv2.Sobel(img, cv2.CV_32F, 1, 0), cv2.Sobel(img, cv2.CV_32F, 0, 1)
    mag = np.hypot(gx, gy)
    ang = (np.arctan2(gy, gx) % (np.pi / 2))
    hist, edges = np.histogram(ang[mag > np.percentile(mag, 90)], bins=90, range=(0, np.pi / 2),
                               weights=mag[mag > np.percentile(mag, 90)])
    hist = np.convolve(np.r_[hist[-3:], hist, hist[:3]], np.ones(5) / 5, "same")[3:-3]
    return float(0.5 * (edges[hist.argmax()] + edges[hist.argmax() + 1]))


def _fill_holes(m):
    """Fill enclosed holes (furniture footprints). Pads first so the outside is always reachable."""
    pad = np.pad(m.astype(np.uint8) * 255, 1)
    mask = np.zeros((pad.shape[0] + 2, pad.shape[1] + 2), np.uint8)
    cv2.floodFill(pad, mask, (0, 0), 128)
    return (pad[1:-1, 1:-1] != 128).astype(np.uint8)


def _merge_small(lab, min_area):
    out = lab.copy()
    for l in np.unique(lab):
        if l <= 0:
            continue
        m = (out == l)
        if m.sum() >= min_area:
            continue
        ring = cv2.dilate(m.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        nb = out[ring & ~m]
        nb = nb[nb > 0]
        if len(nb):
            out[m] = np.bincount(nb).argmax()
    return out


def _signed_area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))


def _rectilinear(poly: np.ndarray) -> np.ndarray:
    """Snap a simplified outline to horizontal/vertical edges (rooms are mostly rectangular)."""
    if len(poly) < 4:
        return poly
    edges = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        d = b - a
        o = "h" if abs(d[0]) >= abs(d[1]) else "v"
        c = (a[1] + b[1]) / 2 if o == "h" else (a[0] + b[0]) / 2
        L = np.linalg.norm(d)
        if edges and edges[-1][0] == o:
            po, pc, pL = edges[-1]
            edges[-1] = (o, (pc * pL + c * L) / (pL + L), pL + L)
        else:
            edges.append((o, c, L))
    if len(edges) > 1 and edges[0][0] == edges[-1][0]:
        o, c, L = edges.pop()
        eo, ec, eL = edges[0]
        edges[0] = (eo, (ec * eL + c * L) / (eL + L), eL + L)
    if len(edges) < 4 or len(edges) % 2:
        return poly
    # drop short jogs: a short edge between two parallel neighbours folds into them (keeps walls straight)
    while len(edges) > 4:
        n = len(edges)
        real = [abs(edges[(i + 1) % n][1] - edges[i - 1][1]) for i in range(n)]   # snapped length of edge i
        k = min(range(n), key=real.__getitem__)
        if real[k] * RES >= MIN_JOG:                # outline is in plan pixels here
            break
        edges = edges[k - 1:] + edges[:k - 1] if k else edges[-1:] + edges[:-1]   # short edge now at index 1
        e0, e2 = edges[0], edges[2]
        edges = [(e0[0], (e0[1] * e0[2] + e2[1] * e2[2]) / (e0[2] + e2[2]), e0[2] + e2[2])] + edges[3:]
    verts = []
    for i in range(len(edges)):
        e, f = edges[i], edges[(i + 1) % len(edges)]
        x = e[1] if e[0] == "v" else f[1]
        y = e[1] if e[0] == "h" else f[1]
        verts.append([x, y])
    return np.array(verts)


def _cut_doors(a, b, doors):
    d = b - a
    L = np.linalg.norm(d)
    u = d / L
    cuts = []
    for dd in doors:
        c = np.array(dd["center"])
        t = (c - a) @ u
        v = c - a
        off = abs(u[0] * v[1] - u[1] * v[0])
        if off < 0.4 and -0.2 < t < L + 0.2:
            half = max(0.4, dd["width"] / 2)
            cuts.append((max(0, t - half), min(L, t + half)))
    segs, cur = [], 0.0
    for t0, t1 in sorted(cuts):
        if t0 > cur:
            segs.append((a + u * cur, a + u * t0))
        cur = max(cur, t1)
    if cur < L:
        segs.append((a + u * cur, b))
    return segs


def _export_points(xy, z, rgb, out_dir, max_n=120000):
    sel = np.arange(len(xy))
    if len(sel) > max_n:
        sel = np.random.default_rng(0).choice(sel, max_n, replace=False)
    arr = np.concatenate([xy[sel], z[sel, None], rgb[sel] / 255.0], axis=1).astype(np.float32)
    arr.tofile(os.path.join(out_dir, "points.f32"))


def _debug_png(free, walls, room_lab, cam_px, rooms, doors, mn, path):
    H, W = free.shape
    img = np.full((H, W, 3), 255, np.uint8)
    rng = np.random.default_rng(3)
    for l in np.unique(room_lab):
        if l > 0:
            img[room_lab == l] = rng.integers(140, 235, 3)
    img[(free > 0) & (room_lab == 0)] = (215, 215, 215)
    img[walls > 0] = (40, 40, 40)
    for (cx, cy) in cam_px:
        cv2.circle(img, (int(cx), int(cy)), 2, (200, 60, 30), -1)
    for r in rooms:
        p = ((np.array(r["polygon"]) - mn) / RES).astype(np.int32)
        cv2.polylines(img, [p], True, (0, 90, 200), 1)
    for d in doors:
        c = ((np.array(d["center"]) - mn) / RES).astype(int)
        cv2.circle(img, tuple(int(v) for v in c), 4, (0, 160, 0), -1)
    cv2.imwrite(path, cv2.flip(img, 0))
