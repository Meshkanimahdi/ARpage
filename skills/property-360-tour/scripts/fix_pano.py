"""Correct one spot of a finished panorama without touching the rest.

  OPENROUTER_API_KEY=... python3 fix_pano.py IN.jpg OUT.jpg X0 X1 Y0 Y1 "what to change"
        [--guide GUIDES_DIR --node N] [--refs a.jpg,b.jpg] [--context 2.4] [--minw 1100] [--size 2K]

X and Y are the box to correct, in percent of the panorama (X0 > X1 means the box crosses the left/right edge;
home.py span and guides' risksNN.txt give such boxes). A 16:9 window around the box goes to the image model with the
instruction; only the box, feathered, is pasted back, so nothing outside it can change.

--guide/--node  send the same window of the point's 3D render too, so the correction lands where the plan puts things.
                Use a 4096-wide guide set for this. Almost always worth it; without it the model guesses positions.
--refs          real photos that show this spot.
--context/--minw  how much surrounding the model sees. For something small and far away use --context 1.3 --minw 800:
                the model then works on it magnified. For removing a large object keep the defaults.
Write the instruction as: what is wrong now, what is really there, what must stay.
"""
import argparse
import base64
import io
import json
import os
import sys
import urllib.request

import cv2
import numpy as np
from PIL import Image

MODEL = os.environ.get("IMAGE_MODEL", "google/gemini-3.1-flash-image")
PROMPT = ("This is a crop from a 360-degree equirectangular panorama of a real home interior, so straight lines look slightly curved; "
          "keep that. Make exactly one change: {what} Fill any freed area with what is naturally there (the same wall finish and "
          "baseboard, the same floor with its reflections), matching the surroundings seamlessly, leaving no outline or ghost of what "
          "was removed. Keep everything else exactly as it is: same framing, same geometry, same colours and lighting. Return the whole image.")
WITH_GUIDE = (" The SECOND image is a plain untextured 3D render of exactly the same crop, ray-traced from the measured floor plan: it "
              "shows where each wall corner, door, window, radiator and cabinet really is (pale blue = glass). The changed area must "
              "agree with it; do not copy its flat look.")
WITH_REFS = (" The LAST {n} image(s) are real photos of this same place, taken from other spots: they show what the things in the "
             "changed area really look like. The first image stays the one you edit.")


def window(W, H, x0, x1, y0, y1, context, minw):
    """The roll that centres the box, and the 16:9 crop around it."""
    if x0 > x1:
        x1 += 100
    shift = int(round(W / 2 - (x0 + x1) / 200 * W))
    bw, bh = (x1 - x0) / 100 * W, (y1 - y0) / 100 * H
    cw = int(min(W, H * 16 / 9, max(bw * context, bh * context * 16 / 9, minw))) // 2 * 2; ch = int(cw * 9 / 16)
    cy = int(np.clip((y0 + y1) / 200 * H, ch / 2, H - ch / 2))
    return shift, W // 2 - cw // 2, cy - ch // 2, cw, ch, bw


def guide_crop(guides, n, W, H, shift, L, T, cw, ch):
    g = np.asarray(Image.open(os.path.join(guides, "guide%02d.png" % n)).convert("RGB").resize((W, H), Image.LANCZOS))
    roll = float(open(os.path.join(guides, "roll%02d.txt" % n)).read())
    return np.roll(np.roll(g, int(round(roll * W)), 1), shift, 1)[T:T + ch, L:L + cw]


def url(b):
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}}


def jpeg(arr):
    b = io.BytesIO(); Image.fromarray(arr).save(b, "JPEG", quality=95)
    return b.getvalue()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("dst")
    for k in ("x0", "x1", "y0", "y1"):
        ap.add_argument(k, type=float)
    ap.add_argument("what")
    ap.add_argument("--guide"); ap.add_argument("--node", type=int); ap.add_argument("--refs", default="")
    ap.add_argument("--context", type=float, default=2.4); ap.add_argument("--minw", type=float, default=1100); ap.add_argument("--size", default="2K")
    a = ap.parse_args()
    im = np.asarray(Image.open(a.src).convert("RGB")); H, W = im.shape[:2]
    shift, L, T, cw, ch, bw = window(W, H, a.x0, a.x1, a.y0, a.y1, a.context, a.minw)
    im = np.roll(im, shift, 1)
    crop = im[T:T + ch, L:L + cw]
    extra, text = [], PROMPT.format(what=a.what)
    if a.guide:
        if a.node is None:
            sys.exit("--guide needs --node")
        extra.append(url(jpeg(guide_crop(a.guide, a.node, W, H, shift, L, T, cw, ch)))); text += WITH_GUIDE
    refs = [r for r in a.refs.split(",") if r]
    if refs:
        extra += [url(open(r, "rb").read()) for r in refs]; text += WITH_REFS.format(n=len(refs))
    body = {"model": MODEL, "modalities": ["image", "text"], "image_config": {"aspect_ratio": "16:9", "image_size": a.size},
            "messages": [{"role": "user", "content": [{"type": "text", "text": text}, url(jpeg(crop))] + extra}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=480))
    imgs = res["choices"][0]["message"].get("images") or []
    if not imgs:
        sys.exit("no image returned: " + json.dumps(res)[:400])
    new = Image.open(io.BytesIO(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))).convert("RGB")
    new = np.asarray(new.resize((cw, ch), Image.LANCZOS), np.float32)
    mask = np.zeros((ch, cw), np.float32)                      # the box inside the crop, with a soft edge
    bx0, bx1 = int(cw / 2 - bw / 2), int(cw / 2 + bw / 2)
    by0, by1 = int(a.y0 / 100 * H - T), int(a.y1 / 100 * H - T)
    mask[max(by0, 0):by1, max(bx0, 0):bx1] = 1
    soft = cv2.GaussianBlur(mask, (0, 0), 14)
    ring = (cv2.dilate(mask, np.ones((61, 61), np.uint8)) - mask) > 0     # the model may shift the tone: match the ring outside the box
    new += (crop[ring].astype(np.float32).mean(0) - new[ring].mean(0))
    out = im.copy()
    out[T:T + ch, L:L + cw] = (crop * (1 - soft[..., None]) + new * soft[..., None]).clip(0, 255).astype(np.uint8)
    Image.fromarray(np.roll(out, -shift, 1)).save(a.dst, quality=90)
    print(a.dst, "cost $%s" % res.get("usage", {}).get("cost"))


if __name__ == "__main__":
    main()
