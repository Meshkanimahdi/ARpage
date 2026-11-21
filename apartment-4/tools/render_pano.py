"""Paint one tour point as a 360 panorama: its colour layout map plus the real photos go to the image model (4K).

  OPENROUTER_API_KEY=... python3 tools/render_pano.py N GUIDES_DIR PHOTOS_DIR OUT.jpg [extra instruction]

The render is padded to 21:9 with its own wrap-around, so the model paints across the left/right seam; the result is cut back
to 2:1 and the seam blended with what it painted past the edge.
"""
import base64
import io
import json
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scene  # noqa: E402

PROMPT = """IMAGE 1 is a plain, untextured 3D-model render of a real apartment in 360-degree equirectangular projection (the full sphere; its left and right edges meet directly behind the camera). It was ray-traced from the measured floor plan, from a camera at eye height (1.5 m) in the {room}.

Your task is an image-to-image edit: turn IMAGE 1 into a photorealistic photograph of the same scene, as a professional real-estate 360 camera would take it from that spot. Keep the geometry of IMAGE 1 exactly: every wall corner, doorway, window, cabinet block and fixture stays at the same place in the frame and at the same size, and the curved look that straight lines have in this projection stays as it is. Do not reframe, zoom, crop or turn it into a normal wide-angle photo; the result covers the full 360 degrees like IMAGE 1. Do not add doors, windows, openings or rooms that IMAGE 1 does not show, and do not leave out any that it shows. Only replace the flat surfaces with the real materials and add realistic light, soft shadows, floor reflections and the small real details: handles, switches, sockets, ceiling lights, window handles.

Door leaves: the render shows every open door leaf as a thin white panel standing inside its room. Paint a white classic raised-panel door with a brass handle exactly there, and no door leaf anywhere else. Kitchen cabinets, the island, wardrobes, radiators, sinks and toilets exist ONLY where the render shows their blocks; never add a second one. Rooms seen through doorways look as the render colours them: dark grey and pale grey = stone slabs of the bathroom or the toilet; cream = an empty painted room.

{dirs}

The OTHER images are phone photos of the real apartment. Use them for materials, colours and style only: door style, window frames, cabinet design, ceiling design and lights, radiators. Never copy their framing or perspective. {finish}

The apartment is empty and clean: no furniture, no people, no boxes, a spotless floor without any dirt, dust, stains or footprints, no photographer or reflection of one, no text, no logos. Surfaces that no photo shows stay plain in the same finishes. Window views: only pale hazy daylight sky and indistinct low rooftops, nothing recognizable. Do not keep the render's flat look or its edge lines. Each fixture appears exactly once. Even natural daylight, sharp detail.{extra}"""


def data_url(im, side):
    im = im.convert("RGB"); im.thumbnail((side, side)); buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main(n, guides, photos, dst, extra=""):
    node = next(p for p in scene.NODES if p["n"] == n)
    g = Image.open(os.path.join(guides, "guide%02d.png" % n)).convert("RGB"); W, H = g.size
    tw = int(H * 21 / 9); e = (tw - W) // 2
    wide = Image.new("RGB", (tw, H))
    wide.paste(g.crop((W - e, 0, W, H)), (0, 0)); wide.paste(g, (e, 0)); wide.paste(g.crop((0, 0, e, H)), (e + W, 0))
    prompt = PROMPT.format(room=scene.ROOM_EN[node["room"]], finish=scene.FINISH[node["room"]],
                           dirs="Positions are given as a share of the image width (0% = left edge, 50% = centre, 100% = right edge).\n"
                           + open(os.path.join(guides, "dirs%02d.txt" % n)).read().strip(),
                           extra=(" " + node["note"] if node.get("note") else "") + ((" " + extra) if extra else ""))
    content = [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": data_url(wide, 2400)}}]
    content += [{"type": "image_url", "image_url": {"url": data_url(Image.open(os.path.join(photos, r + ".jpg")), 1100)}}
                for r in node["refs"][:int(os.environ.get("NREF", "4"))]]
    body = {"model": "google/gemini-3.1-flash-image", "modalities": ["image", "text"],
            "image_config": {"aspect_ratio": "21:9", "image_size": os.environ.get("SIZE", "4K")}, "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=480))
    imgs = res["choices"][0]["message"].get("images") or []
    if not imgs:
        sys.exit("no image returned: " + json.dumps(res)[:400])
    out = Image.open(io.BytesIO(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))).convert("RGB")
    k = out.height / H
    out = np.asarray(out.resize((int(round(tw * k)), out.height), Image.LANCZOS), np.float32)
    e2, W2 = int(round(e * k)), int(round(W * k))
    mid, pad = out[:, e2:e2 + W2].copy(), out[:, e2 + W2:e2 + W2 + e2]
    b = min(e2, pad.shape[1], int(W2 * .035)); t = np.linspace(0, 1, b)[None, :, None]
    mid[:, :b] = pad[:, :b] * (1 - t) + mid[:, :b] * t
    out = np.asarray(Image.fromarray(mid.clip(0, 255).astype(np.uint8)).resize((4096, 2048), Image.LANCZOS))
    # the render was turned to put its edge on a plain wall: turn the result back, so the centre looks up the plan again
    roll = float(open(os.path.join(guides, "roll%02d.txt" % n)).read())
    Image.fromarray(np.roll(out, int(round(roll * 4096)), 1)).save(dst, quality=88)
    print(dst, res.get("usage", {}).get("cost"))


if __name__ == "__main__":
    main(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], " ".join(sys.argv[5:]))
