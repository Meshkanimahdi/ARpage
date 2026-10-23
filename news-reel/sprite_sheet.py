#!/usr/bin/env python3
"""Make a reel's visual elements in at most 3 generated collage sheets, then cut them out.

  python3 news-reel/sprite_sheet.py --dir work/reel [--sheets 1,2,3] [--only-split]

Reads <dir>/elements.json:
  {"style": "photorealistic studio product photos, soft natural light ...",
   "sheets": [{"name": "s1", "items": [{"id": "cow", "desc": "Holstein dairy cow, full body, facing left"}, ...]}]}
Up to 9 items per sheet (3x3 grid), at most 3 sheets (user rule: one image call per sheet, never one
call per element). Each sheet is generated once with a transparent background through
meshkani-pro/scripts/gen_image.py (OpenRouter), then split into its grid cells; every cut-out is
trimmed to its alpha and saved as <dir>/el/<id>.png (plus <dir>/el/_sheet-<name>.jpg previews).
Cells whose background came out opaque are keyed out (near-uniform corner colour) as a fallback.
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageFilter

REPO = Path(__file__).resolve().parent.parent
GEN = REPO / "meshkani-pro/scripts/gen_image.py"
MAX_SHEETS, MAX_ITEMS = 3, 9


def prompt_for(sheet, style, cols, rows):
    # premium, realistic product-photography language (user rule 2026-10-23: realistic, stylish, professional
    # elements, never flat or simple icons) — STORY_SPEC §8.2
    lines = [f"High-end commercial product photography sprite sheet for a premium motion-graphics video: a {cols}x{rows} grid "
             f"of {len(sheet['items'])} separate, isolated hero objects. Look for every object: {style}. Shot like a luxury "
             "advertising campaign: medium-format camera, 100mm macro lens, f/8 so every object is tack sharp, eye-level "
             "three-quarter view, large softbox key light from upper left, soft fill, crisp rim light tracing the edges, "
             "accurate physically based materials (brushed metal, frosted glass, glossy ceramic, fine fabric weave, soft "
             "leather, micro-scratches), true-to-life proportions, clean high-dynamic-range colour, no film grain. Each object "
             "is complete (nothing cut off), centred in its own equal grid cell and fills about 70% of it, with wide empty "
             "margins; objects never touch or overlap; no grid lines, frames, labels, text, numbers, watermarks, or logos "
             "except where the description asks for a real product's own design. Not cartoon, not clipart, not flat icon, "
             "not low-poly, not plastic toy-like. Fully transparent background, no floor, no cast shadow outside the object. "
             "Cells, left to right, top to bottom:"]
    for i, it in enumerate(sheet["items"], 1):
        lines.append(f"{i}. {it['desc']}")
    return "\n".join(lines)


def key_out(cell):
    """Fallback when the model ignored the transparent background: remove the corner colour."""
    rgb = cell.convert("RGB")
    w, h = rgb.size
    corners = [rgb.getpixel(p) for p in [(2, 2), (w - 3, 2), (2, h - 3), (w - 3, h - 3)]]
    bg = tuple(sum(c[i] for c in corners) // 4 for i in range(3))
    px = rgb.load()
    a = Image.new("L", (w, h), 0)
    ap = a.load()
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            d = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            ap[x, y] = 0 if d < 24 else (255 if d > 60 else int((d - 24) * 255 / 36))
    out = rgb.convert("RGBA")
    out.putalpha(a.filter(ImageFilter.GaussianBlur(0.8)))
    return out


def drop_specks(cell, keep_frac=0.03, k=4):
    """Remove small disconnected bits (stray dots, fragments of a neighbour) from a cut-out."""
    a = cell.getchannel("A")
    sw, sh = max(1, a.width // k), max(1, a.height // k)
    small = a.resize((sw, sh), Image.BILINEAR).point(lambda v: 1 if v > 24 else 0)
    px = small.load()
    lab = [[0] * sw for _ in range(sh)]
    sizes = {}
    n = 0
    for y in range(sh):
        for x in range(sw):
            if px[x, y] and not lab[y][x]:
                n += 1
                stack, cnt = [(x, y)], 0
                lab[y][x] = n
                while stack:
                    cx, cy = stack.pop()
                    cnt += 1
                    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
                        if 0 <= nx < sw and 0 <= ny < sh and px[nx, ny] and not lab[ny][nx]:
                            lab[ny][nx] = n
                            stack.append((nx, ny))
                sizes[n] = cnt
    if len(sizes) <= 1:
        return cell
    big = max(sizes.values())
    keep = {i for i, c in sizes.items() if c >= big * keep_frac}
    m = Image.new("L", (sw, sh), 0)
    mp = m.load()
    for y in range(sh):
        for x in range(sw):
            if lab[y][x] in keep:
                mp[x, y] = 255
    m = m.filter(ImageFilter.MaxFilter(3)).resize(a.size, Image.NEAREST)
    out = cell.copy()
    out.putalpha(Image.composite(a, Image.new("L", a.size, 0), m))
    return out


def split(sheet_png, items, out_dir, cols, rows):
    im = Image.open(sheet_png).convert("RGBA")
    W, H = im.size
    report = []
    for i, it in enumerate(items):
        c, r = i % cols, i // cols
        cell = im.crop((c * W // cols, r * H // rows, (c + 1) * W // cols, (r + 1) * H // rows))
        alpha = cell.getchannel("A")
        if alpha.getextrema()[0] > 200:          # opaque cell -> key it out
            cell = key_out(cell)
            alpha = cell.getchannel("A")
        cell = drop_specks(cell)
        alpha = cell.getchannel("A")
        bbox = alpha.point(lambda v: 255 if v > 24 else 0).getbbox()
        if not bbox:
            report.append({"id": it["id"], "ok": False, "why": "empty cell"})
            continue
        pad = 6
        bbox = (max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(cell.width, bbox[2] + pad), min(cell.height, bbox[3] + pad))
        piece = cell.crop(bbox)
        touches = bbox[0] == 0 or bbox[1] == 0 or bbox[2] == cell.width or bbox[3] == cell.height
        f = out_dir / f"{it['id']}.png"
        piece.save(f)
        report.append({"id": it["id"], "ok": True, "file": str(f), "size": piece.size, "touches_cell_edge": touches})
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--sheets", default="")
    ap.add_argument("--only-split", action="store_true")
    a = ap.parse_args()
    d = Path(a.dir).resolve()
    spec = json.loads((d / "elements.json").read_text())
    sheets = spec["sheets"]
    if len(sheets) > MAX_SHEETS or any(len(s["items"]) > MAX_ITEMS for s in sheets):
        sys.exit(f"at most {MAX_SHEETS} sheets of {MAX_ITEMS} items")
    want = set(a.sheets.split(",")) if a.sheets else None
    el = d / "el"
    el.mkdir(exist_ok=True)
    out, cost = [], 0.0
    for s in sheets:
        if want and s["name"] not in want:
            continue
        n = len(s["items"])
        cols = 3 if n > 4 else 2
        rows = (n + cols - 1) // cols
        png = el / f"_sheet-{s['name']}.png"
        if not a.only_split:
            pf = el / f"_sheet-{s['name']}.txt"
            pf.write_text(prompt_for(s, spec.get("style", "photorealistic premium studio product photo, refined materials, soft key light with crisp rim light"), cols, rows))
            cmd = [sys.executable, str(GEN), "--kind", "sheet", "--prompt-file", str(pf), "--out", str(png)]
            for ref in s.get("refs", []):
                cmd += ["--ref", str(d / ref)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode:
                sys.exit(f"sheet {s['name']} failed: {r.stdout[-400:]} {r.stderr[-400:]}")
            cost += json.loads((png.parent / (png.name + ".json")).read_text()).get("cost_usd", 0)
        prev = Image.new("RGB", Image.open(png).size, (238, 234, 228))
        prev.paste(Image.open(png).convert("RGBA"), mask=Image.open(png).convert("RGBA"))
        prev.save(el / f"_sheet-{s['name']}.jpg", quality=85)
        out += split(png, s["items"], el, cols, rows)
    (el / "elements_report.json").write_text(json.dumps({"cost_usd": round(cost, 4), "items": out}, indent=1))
    print(json.dumps({"cost_usd": round(cost, 4), "items": out}, indent=1))


if __name__ == "__main__":
    main()
