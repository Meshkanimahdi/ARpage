"""Repaint a baked panorama into one clean 360° image with an image model on OpenRouter.

  OPENROUTER_API_KEY=... python3 tools/repaint_pano.py panos_raw/pano05.jpg panos/pano05.jpg 5,9,3

The baked panorama is stitched from station renders, so it has seams, smears and untextured blocks. It is padded to
21:9 with its own wrap-around, repainted at 4K (layout kept, defects fixed, photos used for materials only), cropped
back to 2:1 and the left/right seam is blended with the continuation the model painted past the edge.
"""
import base64, io, json, os, sys, urllib.request
import numpy as np
from PIL import Image

PROMPT = ("The FIRST image is a 360-degree equirectangular panorama of one apartment interior, rough and patchy: it was stitched from several "
  "renders, so it has smeared or stretched areas, ghosted duplicate objects, hard seams, flat grey or cream untextured blocks, and blotchy ceiling. "
  "Repaint it into one clean, seamless, photorealistic 360-degree equirectangular panorama of the same room, as from a professional real-estate 360 camera. "
  "Keep EXACTLY the same equirectangular projection and framing, horizon line, the position, size and shape of every wall, door, arch, window, "
  "furniture piece and object: only fix the defects. Give untextured blocks the right material (wood furniture sides, painted walls, cabinet panels), "
  "remove ghost duplicates, smooth the ceiling into a plain cream ceiling, keep the floor continuous honey oak laminate where it is wood. "
  "Windows show only soft bright daylight through sheer white voile, nothing recognizable outside (no bridges, landscapes or famous places). "
  "Keep the content of framed pictures, the TV picture and the portrait exactly as in the first image; do not invent new faces. "
  "The OTHER images are real photos of this apartment: use them only for materials and colours. Same width and height ratio as the first image, no text, no people.")


def data_url(im, side):
    im = im.convert("RGB"); im.thumbnail((side, side)); buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main(src, dst, refs, photos="photos"):
    pano = Image.open(src).convert("RGB"); W, H = pano.size
    tw = int(H * 21 / 9); e = (tw - W) // 2
    wide = Image.new("RGB", (tw, H))
    wide.paste(pano.crop((W - e, 0, W, H)), (0, 0)); wide.paste(pano, (e, 0)); wide.paste(pano.crop((0, 0, e, H)), (e + W, 0))
    content = [{"type": "text", "text": PROMPT}, {"type": "image_url", "image_url": {"url": data_url(wide, 2048)}}]
    content += [{"type": "image_url", "image_url": {"url": data_url(Image.open(os.path.join(photos, f"p{r:02d}.jpg")), 900)}} for r in refs]
    body = {"model": "google/gemini-3.1-flash-image", "modalities": ["image", "text"],
            "image_config": {"aspect_ratio": "21:9", "image_size": "4K"}, "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=480))
    imgs = res["choices"][0]["message"].get("images") or []
    if not imgs:
        sys.exit("no image returned; try again or with other reference photos")
    out = np.asarray(Image.open(io.BytesIO(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))).convert("RGB"), np.float32)
    k = out.shape[0] / H
    out = np.asarray(Image.fromarray(out.astype(np.uint8)).resize((int(round(tw * k)), out.shape[0]), Image.LANCZOS), np.float32)
    e2, W2 = int(round(e * k)), int(round(W * k))
    mid, pad = out[:, e2:e2 + W2].copy(), out[:, e2 + W2:e2 + W2 + e2]
    b = min(e2, pad.shape[1]); t = np.linspace(0, 1, b)[None, :, None]
    mid[:, :b] = pad[:, :b] * (1 - t) + mid[:, :b] * t
    Image.fromarray(mid.clip(0, 255).astype(np.uint8)).resize((4096, 2048), Image.LANCZOS).save(dst, quality=86)
    print(dst, res.get("usage", {}).get("cost"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")])
