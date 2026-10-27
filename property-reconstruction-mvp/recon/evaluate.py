"""Compare a run against a reference reconstruction of the same place.

Metrics
  registration : share of input frames that got a camera pose
  ATE          : camera position error after a similarity alignment (metres, and % of the home's size)
  plan         : overlap (IoU), recall and precision of free floor area against the reference plan,
                 and room / door counts
"""
from __future__ import annotations

import json
import math
import os

import cv2
import numpy as np
import pycolmap

from recon.texture import plan_to_world


def umeyama(src, dst):
    """Similarity transform (s, R, t) with dst ~ s R src + t."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    xs, xd = src - mu_s, dst - mu_d
    U, S, Vt = np.linalg.svd(xd.T @ xs / len(src))
    D = np.eye(3)
    if np.linalg.det(U) * np.linalg.det(Vt) < 0:
        D[2, 2] = -1
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / xs.var(0).sum()
    return s, R, mu_d - s * R @ mu_s


def world_to_plan(scene, X):
    f, s = scene["frame"], scene["scale"]["meters_per_unit"]
    q = np.stack([X @ np.array(f["e1"]), X @ np.array(f["e2"])], -1) * s
    th = f["theta"]
    rot = np.array([[math.cos(th), math.sin(th)], [-math.sin(th), math.cos(th)]])
    return q @ rot.T


def evaluate(run_dir, ref_model_dir, ref_layout_dir, name_map) -> dict:
    sfm = json.load(open(os.path.join(run_dir, "sfm.json")))
    rep = json.load(open(os.path.join(run_dir, "quality_report.json")))
    inputs = len(rep["frames"])
    res = {"inputs": inputs, "registered": sfm.get("registered", 0),
           "registration_rate": round(sfm.get("registered", 0) / max(1, inputs), 3)}
    if not sfm.get("ok"):
        return res
    ref = pycolmap.Reconstruction(ref_model_dir)
    ref_c = {im.name: im.projection_center() for im in ref.images.values()}
    run = pycolmap.Reconstruction(sfm["model_dir"])
    a, b, names = [], [], []
    for im in run.images.values():
        if not im.has_pose:
            continue
        rn = name_map(im.name)
        if rn in ref_c:
            a.append(im.projection_center()); b.append(ref_c[rn]); names.append(im.name)
    a, b = np.array(a), np.array(b)
    if len(a) < 3:
        return res
    s, R, t = umeyama(a, b)
    err = np.linalg.norm((s * a @ R.T + t) - b, axis=1)
    ref_scene = json.load(open(os.path.join(ref_layout_dir, "scene.json")))
    m_per_ref = ref_scene["scale"]["meters_per_unit"]
    span = np.linalg.norm(np.array(ref_scene["bounds"]["max"]) - np.array(ref_scene["bounds"]["min"]))
    res["ate_m"] = round(float(np.sqrt((err ** 2).mean()) * m_per_ref), 3)
    res["ate_median_m"] = round(float(np.median(err) * m_per_ref), 3)
    res["ate_pct_of_home"] = round(float(np.sqrt((err ** 2).mean()) * m_per_ref / span * 100), 2)

    # plan overlap: move our free-space cells into the reference plan grid
    scene_path = os.path.join(run_dir, "scene.json")
    if os.path.exists(scene_path):
        scene = json.load(open(scene_path))
        free = np.load(os.path.join(run_dir, "free_mask.npy"))
        ref_free = np.load(os.path.join(ref_layout_dir, "free_mask.npy"))
        res_cell = 0.05
        ys, xs = np.nonzero(free)
        mn = np.array(scene["bounds"]["min"])
        px, py = mn[0] + (xs + 0.5) * res_cell, mn[1] + (ys + 0.5) * res_cell
        Xw = plan_to_world(scene, px, py, np.zeros(len(px)))
        Xr = s * Xw @ R.T + t
        q = world_to_plan(ref_scene, Xr)
        rmn = np.array(ref_scene["bounds"]["min"])
        ij = np.floor((q - rmn) / res_cell).astype(int)
        ok = (ij[:, 0] >= 0) & (ij[:, 0] < ref_free.shape[1]) & (ij[:, 1] >= 0) & (ij[:, 1] < ref_free.shape[0])
        ours = np.zeros_like(ref_free)
        ours[ij[ok, 1], ij[ok, 0]] = 1
        ours = cv2.morphologyEx(ours, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        inter = float((ours & ref_free).sum()); union = float((ours | ref_free).sum())
        res["plan_iou"] = round(inter / union, 3) if union else 0.0
        res["plan_recall"] = round(inter / max(1, ref_free.sum()), 3)
        res["plan_precision"] = round(inter / max(1, ours.sum()), 3)
        res["rooms"] = len(scene["rooms"]); res["rooms_reference"] = len(ref_scene["rooms"])
        res["doors"] = len(scene["doors"]); res["doors_reference"] = len(ref_scene["doors"])
        res["free_area_m2"] = scene["stats"]["free_area_m2"]
        res["free_area_reference_m2"] = ref_scene["stats"]["free_area_m2"]
        res["scale_ratio_vs_reference"] = round(float(scene["scale"]["meters_per_unit"] / (m_per_ref * s)), 3)
        if "appearance" in scene:
            res["floor_coverage"] = scene["appearance"]["floor_coverage"]
            res["wall_coverage"] = scene["appearance"]["wall_coverage"]
        overlay = np.zeros(ref_free.shape + (3,), np.uint8); overlay[:] = 255
        overlay[ref_free > 0] = (200, 200, 200)
        overlay[(ours > 0) & (ref_free > 0)] = (90, 160, 90)
        overlay[(ours > 0) & (ref_free == 0)] = (60, 60, 220)
        cv2.imwrite(os.path.join(run_dir, "plan_vs_reference.png"), cv2.flip(overlay, 0))
    return res
