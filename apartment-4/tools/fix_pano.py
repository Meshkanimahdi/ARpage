"""Correct one spot of a finished panorama without touching the rest.

  OPENROUTER_API_KEY=... python3 tools/fix_pano.py IN.jpg OUT.jpg X0 X1 Y0 Y1 "what to change"

X and Y are the box to correct, in percent of the panorama (X0 > X1 means the box crosses the left/right edge). A 16:9
window around the box goes to the image model with the instruction; only the box, feathered, is pasted back, so nothing
outside it can change.
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


def main(src, dst, x0, x1, y0, y1, what):
    im = np.asarray(Image.open(src).convert("RGB")); H, W = im.shape[:2]
    if x0 > x1:
        x1 += 100
    shift = int(round(W / 2 - (x0 + x1) / 200 * W))          # turn the panorama so the box sits in the middle
    im = np.roll(im, shift, 1)
    bw, bh = (x1 - x0) / 100 * W, (y1 - y0) / 100 * H
    cw = int(min(W, H * 16 / 9, max(bw * 2.4, bh * 2.4 * 16 / 9, 1100))) // 2 * 2; ch = int(cw * 9 / 16)
    cx, cy = W // 2, int(np.clip((y0 + y1) / 200 * H, ch / 2, H - ch / 2))
    L, T = cx - cw // 2, cy - ch // 2
    crop = im[T:T + ch, L:L + cw]
    buf = io.BytesIO(); Image.fromarray(crop).save(buf, "JPEG", quality=95)
    body = {"model": "google/gemini-3.1-flash-image", "modalities": ["image", "text"],
            "image_config": {"aspect_ratio": "16:9", "image_size": os.environ.get("SIZE", "2K")},
            "messages": [{"role": "user", "content": [
                {"type": "text", "text": PROMPT.format(what=what)},
                {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}]}]}
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
