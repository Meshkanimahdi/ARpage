"""Turn one point's layout guide plus the real photos of that room into a 360° panorama (OpenRouter image model, 4K).

  OPENROUTER_API_KEY=... python3 tools/render_pano.py GUIDE.png OUT.jpg PHOTO.jpg [PHOTO.jpg ...]

The guide is padded to 21:9 with its own wrap-around, so the model paints across the left/right seam; the result is cropped
back to 2:1 and the seam blended with the continuation it painted past the edge.
"""
import base64, io, json, os, sys, urllib.request
import numpy as np
from PIL import Image

PROMPT = (
    "Make one photorealistic 360-degree equirectangular panorama (full sphere, 2:1 projection) of the room shown in the photos. "
    "The FIRST image is the layout guide in the same equirectangular projection: a line drawing seen from the camera position, "
    "with the walls, ceiling and floor edges, doors and windows in black and the main furniture in grey. Keep EXACTLY its "
    "projection, horizon, camera height, and the position and size of every wall corner, door and window. "
    "The OTHER images are real photos of this same room: copy from them the furniture, materials, colours, lighting, ceiling "
    "lights, curtains and decor, and place the furniture where the grey boxes are (the photos win on details the boxes do not show). "
    "Walls that no photo shows stay plain and in the style of the visible walls; do not invent artwork, logos or text. "
    "Windows show only soft bright daylight through their curtains or film, nothing recognizable outside. "
    "Never copy the guide's lines into the result: no outlines, arcs or wireframe lines anywhere. Each fixture (toilet, sink, "
    "shower, bed, sofa) appears exactly as often as in the photos, never duplicated. "
    "Look of a professional real-estate 360 camera: sharp, evenly lit, straight vertical lines, no people, no text.")


def data_url(im, side):
    im = im.convert("RGB"); im.thumbnail((side, side)); buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main(guide, dst, photos):
    g = Image.open(guide).convert("RGB"); W, H = g.size
    tw = int(H * 21 / 9); e = (tw - W) // 2
    wide = Image.new("RGB", (tw, H)); wide.paste(g.crop((W - e, 0, W, H)), (0, 0)); wide.paste(g, (e, 0)); wide.paste(g.crop((0, 0, e, H)), (e + W, 0))
    content = [{"type": "text", "text": PROMPT}, {"type": "image_url", "image_url": {"url": data_url(wide, 2048)}}]
    content += [{"type": "image_url", "image_url": {"url": data_url(Image.open(p), 1024)}} for p in photos]
    body = {"model": "google/gemini-3.1-flash-image", "modalities": ["image", "text"],
            "image_config": {"aspect_ratio": "21:9", "image_size": "4K"}, "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=480))
    imgs = res["choices"][0]["message"].get("images") or []
    if not imgs:
        sys.exit("no image returned")
    out = Image.open(io.BytesIO(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))).convert("RGB")
    k = out.height / H
    out = np.asarray(out.resize((int(round(tw * k)), out.height), Image.LANCZOS), np.float32)
    e2, W2 = int(round(e * k)), int(round(W * k))
    mid, pad = out[:, e2:e2 + W2].copy(), out[:, e2 + W2:e2 + W2 + e2]
    b = min(e2, pad.shape[1]); t = np.linspace(0, 1, b)[None, :, None]
    mid[:, :b] = pad[:, :b] * (1 - t) + mid[:, :b] * t
    Image.fromarray(mid.clip(0, 255).astype(np.uint8)).resize((4096, 2048), Image.LANCZOS).save(dst, quality=86)
    print(dst, res.get("usage", {}).get("cost"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3:])
