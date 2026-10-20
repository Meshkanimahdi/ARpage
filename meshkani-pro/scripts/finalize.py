#!/usr/bin/env python3
"""Turn a raw model image into the final Instagram JPEG and QA previews.

  finalize.py --kind post|story RAW OUT.jpg     final JPEG + JSON report
  finalize.py --sheet OUT.jpg IMG [IMG ...]      contact sheet for visual review

Post: center-crop to 4:5, resize to 1080x1350. Story: 9:16, 1080x1920; also
writes OUT.safezone.jpg with the top/bottom safe margins drawn, for review only.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

CONFIG = json.loads((Path(__file__).resolve().parent.parent / "config.json").read_text())
IMG = CONFIG["images"]


def crop_to_ratio(im, w, h):
    target = w / h
    cw, ch = im.size
    if abs(cw / ch - target) < 1e-3:
        return im
    if cw / ch > target:
        nw = round(ch * target)
        x = (cw - nw) // 2
        return im.crop((x, 0, x + nw, ch))
    nh = round(cw / target)
    y = (ch - nh) // 2
    return im.crop((0, y, cw, y + nh))


def finalize(kind, raw, out):
    spec = IMG[kind]
    w, h = spec["final"]
    src = Image.open(raw)
    src_size = src.size
    im = crop_to_ratio(src.convert("RGB"), w, h).resize((w, h), Image.LANCZOS)
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "JPEG", quality=IMG["jpeg_quality"], optimize=True, progressive=False)

    check = Image.open(out)
    check.verify()
    check = Image.open(out)
    data = out.read_bytes()
    report = {
        "kind": kind,
        "file": str(out),
        "source": str(raw),
        "source_size": list(src_size),
        "cropped_fraction": round(1 - (min(src_size[0] / src_size[1], w / h) / max(src_size[0] / src_size[1], w / h)), 4),
        "size": list(check.size),
        "format": check.format,
        "mode": check.mode,
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),
        "ok": check.size == (w, h) and check.format == "JPEG" and len(data) < 8_000_000,
    }
    if kind == "story":
        prev = im.copy()
        d = ImageDraw.Draw(prev)
        top, bottom = spec["safe_top_px"], h - spec["safe_bottom_px"]
        for y in (top, bottom):
            d.line([(0, y), (w, y)], fill=(255, 0, 0), width=6)
        prev.save(out.with_suffix(".safezone.jpg"), "JPEG", quality=80)
        report["safezone_preview"] = str(out.with_suffix(".safezone.jpg"))
        report["safe_zone"] = {"top_px": spec["safe_top_px"], "bottom_px": spec["safe_bottom_px"]}
    Path(str(out) + ".json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return report


def sheet(out, files, height=900):
    ims = [Image.open(f).convert("RGB") for f in files]
    ims = [i.resize((round(i.width * height / i.height), height), Image.LANCZOS) for i in ims]
    gap = 16
    canvas = Image.new("RGB", (sum(i.width for i in ims) + gap * (len(ims) + 1), height + 2 * gap), (240, 240, 240))
    x = gap
    for i in ims:
        canvas.paste(i, (x, gap))
        x += i.width + gap
    canvas.save(out, "JPEG", quality=85)
    return {"sheet": str(out), "count": len(ims)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["post", "story"])
    ap.add_argument("--sheet", action="store_true")
    ap.add_argument("paths", nargs="+")
    a = ap.parse_args()
    if a.sheet:
        print(json.dumps(sheet(a.paths[0], a.paths[1:])))
        return 0
    if not a.kind or len(a.paths) != 2:
        ap.error("--kind and RAW OUT are required")
    r = finalize(a.kind, a.paths[0], a.paths[1])
    print(json.dumps(r, ensure_ascii=False))
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
