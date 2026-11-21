"""Correct one spot of a finished panorama without touching the rest.

  OPENROUTER_API_KEY=... [REFS=photo.jpg,photo.jpg] python3 tools/fix_pano.py IN.jpg OUT.jpg X0 X1 Y0 Y1 "what to change"

X and Y are the box to correct, in percent of the panorama (X0 > X1 means the box crosses the left/right edge). A 16:9
window around the box goes to the image model with the instruction; only the box, feathered, is pasted back, so nothing
outside it can change. REFS are real photos of the same place for the model to match. GUIDE is the point's plain 3D render
(guideNN.png, with rollNN.txt beside it): the same window of it is sent too, so the correction follows the plan.
"""
import base64
import io
import json
import os
import sys
import urllib.request

import cv2
import numpy as np
from PIL import Image

PROMPT = ("This is a crop from a 360-degree equirectangular panorama of an empty apartment, so straight lines look slightly curved; "
          "keep that. Make exactly one change: {what} Fill the freed area with what is naturally there (the same wall paint and white "
          "baseboard, the same floor tiles with their reflections), matching the surroundings seamlessly. Keep everything else exactly "
          "as it is: same framing, same geometry, same colours and lighting. Return the whole image.")
WITH_GUIDE = (" The SECOND image is a plain untextured 3D render of exactly the same crop, ray-traced from the measured floor plan: it "
              "shows where each wall corner, door, window, radiator and cabinet really is (pale blue = glass). The changed area must "
              "agree with it; do not copy its flat look.")
WITH_REFS = (" The LAST {n} image(s) are real photos of this same place, taken from other spots: they show what the things in the "
             "changed area really look like. The first image stays the one you edit.")


def main(src, dst, x0, x1, y0, y1, what):
    im = np.asarray(Image.open(src).convert("RGB")); H, W = im.shape[:2]
    if x0 > x1:
        x1 += 100
    shift = int(round(W / 2 - (x0 + x1) / 200 * W))          # turn the panorama so the box sits in the middle
    im = np.roll(im, shift, 1)
    bw, bh = (x1 - x0) / 100 * W, (y1 - y0) / 100 * H
    k = float(os.environ.get("CONTEXT", "2.4"))          # how much surrounding the model sees; less = more magnification
    cw = int(min(W, H * 16 / 9, max(bw * k, bh * k * 16 / 9, 1100))) // 2 * 2; ch = int(cw * 9 / 16)
    cx, cy = W // 2, int(np.clip((y0 + y1) / 200 * H, ch / 2, H - ch / 2))
    L, T = cx - cw // 2, cy - ch // 2
    crop = im[T:T + ch, L:L + cw]
    buf = io.BytesIO(); Image.fromarray(crop).save(buf, "JPEG", quality=95)
    def url(b):
        return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b).decode()}}
    extra, text = [], PROMPT.format(what=what)
    if os.environ.get("GUIDE"):
        g = np.asarray(Image.open(os.environ["GUIDE"]).convert("RGB").resize((W, H), Image.LANCZOS))
        roll = float(open(os.environ["GUIDE"].replace("guide", "roll").replace(".png", ".txt")).read())
        g = np.roll(np.roll(g, int(round(roll * W)), 1), shift, 1)[T:T + ch, L:L + cw]
        b = io.BytesIO(); Image.fromarray(g).save(b, "JPEG", quality=95); extra.append(url(b.getvalue())); text += WITH_GUIDE
        if os.environ.get("DEBUG"):
            Image.fromarray(np.hstack([crop, g])).save(os.environ["DEBUG"], quality=88)
            return
    refs = [r for r in os.environ.get("REFS", "").split(",") if r]
    if refs:
        extra += [url(open(r, "rb").read()) for r in refs]; text += WITH_REFS.format(n=len(refs))
    body = {"model": "google/gemini-3.1-flash-image", "modalities": ["image", "text"],
            "image_config": {"aspect_ratio": "16:9", "image_size": os.environ.get("SIZE", "2K")},
            "messages": [{"role": "user", "content": [{"type": "text", "text": text}, url(buf.getvalue())] + extra}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=480))
    imgs = res["choices"][0]["message"].get("images") or []
    if not imgs:
        sys.exit("no image returned: " + json.dumps(res)[:400])
    new = Image.open(io.BytesIO(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))).convert("RGB")
    new = np.asarray(new.resize((cw, ch), Image.LANCZOS), np.float32)
    # the box inside the crop, with a soft edge
    mask = np.zeros((ch, cw), np.float32)
    bx0, bx1 = int(cw / 2 - bw / 2), int(cw / 2 + bw / 2)
    by0, by1 = int(y0 / 100 * H - T), int(y1 / 100 * H - T)
    mask[max(by0, 0):by1, max(bx0, 0):bx1] = 1
    soft = cv2.GaussianBlur(mask, (0, 0), 14)
    # the model may shift the tone slightly: bring the ring just outside the box back to the original
    ring = (cv2.dilate(mask, np.ones((61, 61), np.uint8)) - mask) > 0
    new += (crop[ring].astype(np.float32).mean(0) - new[ring].mean(0))
    out = im.copy()
    out[T:T + ch, L:L + cw] = (crop * (1 - soft[..., None]) + new * soft[..., None]).clip(0, 255).astype(np.uint8)
    Image.fromarray(np.roll(out, -shift, 1)).save(dst, quality=90)
    print(dst, res.get("usage", {}).get("cost"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], *[float(v) for v in sys.argv[3:7]], " ".join(sys.argv[7:]))
