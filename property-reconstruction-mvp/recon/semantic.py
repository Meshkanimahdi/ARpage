"""Engine E: room labels from the captured frames (vision model via OpenRouter).

For each room a few of its own frames (spread across its cameras) are sent to a vision model, which must
answer from what is visible only. The answer is stored with its confidence and the frames it was based on,
so every label can be checked against the pictures. Nothing here changes geometry or appearance.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.request

import cv2

MODEL = os.environ.get("SEMANTIC_MODEL", "google/gemini-2.5-flash")
PER_ROOM = 3
LABELS = ["living room", "bedroom", "kitchen", "dining", "bathroom", "hallway", "office", "storage", "other"]

PROMPT = (
    "These photos were all taken inside the same room of an apartment. Using only what is visible, "
    f"classify the room as one of: {', '.join(LABELS)}. Also list up to 8 clearly visible fixed or large "
    "items (e.g. sofa, bed, sink, stove, desk, piano, window, door). Do not guess anything not visible. "
    'Reply with JSON only: {"label": "...", "confidence": 0.0-1.0, "items": ["..."], "reason": "short"}'
)


def _encode(path, side=640):
    img = cv2.imread(path)
    s = side / max(img.shape[:2])
    img = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode()


def _ask(images):
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": [{"type": "text", "text": PROMPT}] +
                      [{"type": "image_url", "image_url": {"url": u}} for u in images]}],
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
        {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=120))
    text = res["choices"][0]["message"]["content"].strip()
    text = text[text.find("{"): text.rfind("}") + 1]
    return json.loads(text), res.get("usage", {})


def build(out_dir: str, frames_dir: str) -> dict:
    path = os.path.join(out_dir, "scene.json")
    scene = json.load(open(path))
    tokens = 0
    for r in scene["rooms"]:
        cams = [c for c in scene["cameras"] if c["room"] == r["id"]]
        if not cams:
            continue
        pick = [cams[round(i * (len(cams) - 1) / max(1, PER_ROOM - 1))]["name"] for i in range(min(PER_ROOM, len(cams)))]
        pick = list(dict.fromkeys(pick))
        try:
            ans, usage = _ask([_encode(os.path.join(frames_dir, n)) for n in pick])
            tokens += usage.get("total_tokens", 0)
            label = ans.get("label") if ans.get("label") in LABELS else "other"
            r["semantic"] = {"label": label, "confidence": float(ans.get("confidence", 0)),
                             "items": ans.get("items", [])[:8], "reason": ans.get("reason", ""),
                             "evidence_images": pick, "model": MODEL}
        except Exception as e:  # a failed label never blocks the rest of the pipeline
            r["semantic"] = {"label": None, "error": str(e)[:200], "evidence_images": pick}
    scene["semantic"] = {"model": MODEL, "tokens": tokens}
    json.dump(scene, open(path, "w"), indent=1)
    return {r["id"]: r.get("semantic", {}).get("label") for r in scene["rooms"]}
