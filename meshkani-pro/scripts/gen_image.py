#!/usr/bin/env python3
"""Generate (or edit) one image through the OpenRouter Images API.

  gen_image.py --kind post|story|object --prompt-file P --out raw.png [--ref prev.png] [--model M]

Writes the raw model image to --out and a sidecar <out>.json with the model,
parameters, prompt hash, usage and reported cost. Reads OPENROUTER_API_KEY from
the environment and never prints it.
"""
import argparse
import base64
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

CONFIG = json.loads((Path(__file__).resolve().parent.parent / "config.json").read_text())
IMG = CONFIG["images"]


def call(body, timeout=300):
    req = urllib.request.Request(
        IMG["endpoint"],
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
            "Content-Type": "application/json",
            "HTTP-Referer": "https://www.instagram.com/meshkani.pro/",
            "X-Title": "meshkani.pro publisher",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def data_url(path):
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["post", "story", "object", "sheet"], required=True)
    ap.add_argument("--prompt-file", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", action="append", default=[], help="reference/edit-source image")
    ap.add_argument("--model", default=IMG["primary_model"])
    ap.add_argument("--quality", default=IMG["quality"])
    args = ap.parse_args()

    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set in this environment.", file=sys.stderr)
        return 5

    prompt = Path(args.prompt_file).read_text()
    spec = IMG[args.kind]
    base = {"model": args.model, "prompt": prompt, "n": 1, "quality": args.quality,
            "output_format": "png"}
    if spec.get("background"):          # reel cut-outs: transparent PNG
        base["background"] = spec["background"]
    if args.ref:
        base["input_references"] = [
            {"type": "image_url", "image_url": {"url": data_url(Path(p))}} for p in args.ref]

    # Exact pixel size first; if the provider rejects it, fall back to the
    # nearest supported aspect ratio (finalize.py crops to the exact ratio).
    attempts = [dict(base, size=spec["request_size"]),
                dict(base, aspect_ratio=spec["fallback_aspect_ratio"])]
    last_err = None
    resp = used = None
    for body in attempts:
        for retry in range(3):
            try:
                resp, used = call(body), body
                break
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:600]
                last_err = f"HTTP {e.code}: {detail}"
                if e.code in (429, 500, 502, 503, 524, 529):
                    time.sleep(10 * (retry + 1))
                    continue
                break
            except (urllib.error.URLError, TimeoutError) as e:
                last_err = f"network: {e}"
                time.sleep(10 * (retry + 1))
        if resp:
            break
    if not resp:
        print(json.dumps({"ok": False, "error": last_err}, ensure_ascii=False))
        return 1

    item = resp["data"][0]
    raw = base64.b64decode(item["b64_json"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(raw)
    meta = {
        "ok": True,
        "file": str(out),
        "model": used["model"],
        "params": {k: v for k, v in used.items() if k not in ("prompt", "input_references")},
        "references": args.ref,
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "media_type": item.get("media_type"),
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "usage": resp.get("usage"),
        "cost_usd": (resp.get("usage") or {}).get("cost"),
        "created": resp.get("created"),
    }
    Path(str(out) + ".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    print(json.dumps(meta, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
