"""Paint one tour point as a 360 panorama: its plain 3D render plus real photos of the place go to the image model.

  OPENROUTER_API_KEY=... python3 render_pano.py HOME.json N GUIDES_DIR PHOTOS_DIR OUT.jpg [--refs 4] [--size 4K] [--extra "..."]

The photos are the point's "refs" in home.json (file names without .jpg, in PHOTOS_DIR), most useful first.
The render is padded to 21:9 with its own wrap-around, so the model paints across the left/right seam; the result is cut
back to 2:1, the seam blended with what it painted past the edge, and the picture turned back so that its centre looks
toward the top of the plan. Prints the cost in dollars. IMAGE_MODEL overrides the model.
"""
import argparse
import base64
import io
import json
import os
import sys
import urllib.request

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home as homelib  # noqa: E402

MODEL = os.environ.get("IMAGE_MODEL", "google/gemini-3.1-flash-image")

PROMPT = """IMAGE 1 is a plain, untextured 3D-model render of a real home in 360-degree equirectangular projection (the full sphere; its left and right edges meet directly behind the camera). It was ray-traced from the measured floor plan, from a camera at eye height ({eye} m) in the {room}.

Your task is an image-to-image edit: turn IMAGE 1 into a photorealistic photograph of the same scene, as a professional real-estate 360 camera would take it from that spot. Keep the geometry of IMAGE 1 exactly: every wall corner, doorway, window, cabinet block and fixture stays at the same place in the frame and at the same size, and the curved look that straight lines have in this projection stays as it is. Do not reframe, zoom, crop or turn it into a normal wide-angle photo; the result covers the full 360 degrees like IMAGE 1. Do not add doors, windows, openings or rooms that IMAGE 1 does not show, and do not leave out any that it shows. Only replace the flat surfaces with the real materials and add realistic light, soft shadows, floor reflections and the small real details: handles, switches, sockets, ceiling lights, window handles.

Door leaves: the render shows every open door leaf as a thin pale panel standing inside its room. Paint {leaf} exactly there, and no door leaf anywhere else. Cabinets, wardrobes, radiators, sanitary fixtures and other blocks exist ONLY where the render shows them; never add a second one. Rooms seen through doorways look as the render colours them{legend}. Long plain walls are flat: paint each one evenly, with one smooth baseboard, no fold or joint in it.

Positions are given as a share of the image width (0% = left edge, 50% = centre, 100% = right edge).
{dirs}

The OTHER images are phone photos of the real place. Use them for materials, colours and style only: door style, window frames, cabinet design, ceiling design and lights, radiators. Never copy their framing or perspective. {finish}

{state} Surfaces that no photo shows stay plain in the same finishes. Window views: {view}. Do not keep the render's flat look or its edge lines. Each fixture appears exactly once. Even natural daylight, sharp detail.{extra}"""

STATE = {
    "empty": "The home is empty and clean: no furniture, no people, no boxes, a spotless floor without any dirt, dust, stains or footprints, no photographer or reflection of one, no text, no logos.",
    "furnished": "The home is furnished as in the photos: put each piece of furniture where the render shows its block and take its look from the photos; add no piece the render does not show. No people, no photographer or reflection of one, no personal photographs or documents, no text, no logos.",
}


def data_url(im, side):
    im = im.convert("RGB"); im.thumbnail((side, side)); buf = io.BytesIO(); im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("home"); ap.add_argument("n", type=int); ap.add_argument("guides"); ap.add_argument("photos"); ap.add_argument("out")
    ap.add_argument("--refs", type=int, default=4, help="how many of the point's photos to send (more than 5 dilutes the render)")
    ap.add_argument("--size", default="4K", help="4K for the real thing, 1K for a cheap trial of a prompt change")
    ap.add_argument("--extra", default="", help="one more instruction for this run only")
    a = ap.parse_args()
    H = homelib.load(a.home)
    node = H.node(a.n)
    g = Image.open(os.path.join(a.guides, "guide%02d.png" % a.n)).convert("RGB"); W, Hh = g.size
    tw = int(Hh * 21 / 9); e = (tw - W) // 2
    wide = Image.new("RGB", (tw, Hh))
    wide.paste(g.crop((W - e, 0, W, Hh)), (0, 0)); wide.paste(g, (e, 0)); wide.paste(g.crop((0, 0, e, Hh)), (e + W, 0))
    legend = H.STYLE["through_legend"] or ("; dark grey and pale grey = the stone or tile cladding of a bathroom or toilet, cream = a painted room" if H.SLAB_ROOMS else "")
    if legend and not legend.startswith((";", ":", ",")):
        legend = ": " + legend
    prompt = PROMPT.format(eye=H.EYE, room=H.ROOM_EN[node["room"]], leaf=H.STYLE["door_leaf"], legend=legend, finish=H.FINISH[node["room"]],
                           dirs=open(os.path.join(a.guides, "dirs%02d.txt" % a.n)).read().strip(), view=H.STYLE["window_view"],
                           state=STATE.get(H.STYLE["state"], H.STYLE["state"]),
                           extra=(" " + node["note"] if node.get("note") else "") + ((" " + a.extra) if a.extra else ""))
    refs = []
    for r in node["refs"][:a.refs]:
        p = os.path.join(a.photos, r if os.path.splitext(r)[1] else r + ".jpg")
        if not os.path.exists(p):
            sys.exit("reference photo missing: " + p)
        refs.append(p)
    if not refs:
        sys.exit("point %d has no reference photos (\"refs\" in home.json): without them the model invents the finishes" % a.n)
    content = [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": data_url(wide, 2400)}}]
    content += [{"type": "image_url", "image_url": {"url": data_url(Image.open(p), 1100)}} for p in refs]
    body = {"model": MODEL, "modalities": ["image", "text"], "image_config": {"aspect_ratio": "21:9", "image_size": a.size},
            "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=480))
    imgs = res["choices"][0]["message"].get("images") or []
    if not imgs:
        sys.exit("no image returned: " + json.dumps(res)[:400])
    out = Image.open(io.BytesIO(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))).convert("RGB")
    k = out.height / Hh
    out = np.asarray(out.resize((int(round(tw * k)), out.height), Image.LANCZOS), np.float32)
    e2, W2 = int(round(e * k)), int(round(W * k))
    mid, pad = out[:, e2:e2 + W2].copy(), out[:, e2 + W2:e2 + W2 + e2]
    b = min(e2, pad.shape[1], int(W2 * .035)); t = np.linspace(0, 1, b)[None, :, None]
    mid[:, :b] = pad[:, :b] * (1 - t) + mid[:, :b] * t
    out = np.asarray(Image.fromarray(mid.clip(0, 255).astype(np.uint8)).resize((4096, 2048), Image.LANCZOS))
    roll = float(open(os.path.join(a.guides, "roll%02d.txt" % a.n)).read())     # turn it back: centre looks up the plan again
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    Image.fromarray(np.roll(out, int(round(roll * 4096)), 1)).save(a.out, quality=88)
    print(a.out, "cost $%s" % res.get("usage", {}).get("cost"))


if __name__ == "__main__":
    main()
