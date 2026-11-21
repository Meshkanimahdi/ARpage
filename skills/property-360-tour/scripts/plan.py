"""Draw the 2D floor plan from home.json.

  python3 plan.py HOME.json OUT.svg            draft for the owner to confirm: walk order, open questions in red
  python3 plan.py HOME.json OUT.svg --final    the clean sheet that goes into the tour
  node svg2png.js OUT.svg OUT.png              a picture of it to send (needs Playwright)

Every size on the sheet is an estimate unless home.json says "measured": true.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import home as homelib  # noqa: E402

FA = str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫")


def fa(v):
    return str(v).translate(FA)


def svg(H, final=False):
    d, T = H.d, H.WALL_T
    x0, y0, x1, y1 = H.bounds()
    for o in d.get("outside", []):
        x0, y0 = min(x0, o["rect"][0]), min(y0, o["rect"][1])
        x1, y1 = max(x1, o["rect"][0] + o["rect"][2]), max(y1, o["rect"][1] + o["rect"][3])
    vx, vy, vw, vh = x0 - 1.5, y0 - (1.3 if final else 2.2), x1 - x0 + 3.0, y1 - y0 + (3.2 if final else 4.1)
    o = []
    add = o.append
    add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="%g %g %g %g" direction="rtl" font-family="Vazirmatn, Tahoma, sans-serif">' % (vx, vy, vw, vh))
    add('<rect x="%g" y="%g" width="%g" height="%g" fill="#ffffff"/>' % (vx, vy, vw, vh))
    for a in d.get("outside", []):                      # terraces, light wells: outside the flat, sizes usually unknown
        x, y, w, h = a["rect"]
        add('<rect x="%g" y="%g" width="%g" height="%g" fill="#eef3f8" stroke="#9db2c8" stroke-width="0.03" stroke-dasharray="0.12 0.08"/>' % (x, y, w, h))
        add('<text x="%g" y="%g" font-size="0.26" text-anchor="middle" fill="#5d7388">%s</text>' % (x + w / 2, y + h / 2 + 0.09, a["name"]))
    for r in H.ROOMS.values():
        add('<polygon points="%s" fill="#fbfaf7" stroke="#222725" stroke-width="%g" stroke-linejoin="miter"/>' % (" ".join("%g,%g" % tuple(p) for p in r["poly"]), T))
    marks = H.BOX_PLAN + [(tuple(m["rect"]), m["name"]) for m in d.get("plan_marks", [])]
    for (bx0, by0, bx1, by1), name in marks:
        add('<rect x="%g" y="%g" width="%g" height="%g" fill="#eeece6" stroke="#8a8f8c" stroke-width="0.025"/>' % (bx0, by0, bx1 - bx0, by1 - by0))
        add('<text x="%g" y="%g" font-size="0.17" text-anchor="middle" fill="#6a6f6c">%s</text>' % ((bx0 + bx1) / 2, (by0 + by1) / 2 + 0.06, name))
    for b in H.BOXES:
        if b[6] == "col":
            add('<rect x="%g" y="%g" width="%g" height="%g" fill="#222725"/>' % (b[0], b[1], b[2] - b[0], b[3] - b[1]))
        elif b[6] == "rad":
            add('<rect x="%g" y="%g" width="%g" height="%g" fill="#c2703d"/>' % (b[0], b[1], b[2] - b[0], b[3] - b[1]))
    for op in H.OPENINGS:
        (ax, ay), (bx, by) = op["a"], op["b"]
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#fbfaf7" stroke-width="%g"/>' % (ax, ay, bx, by, T + 0.04))
        if op.get("kind") == "open":
            add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#8a8f8c" stroke-width="0.02" stroke-dasharray="0.1 0.07"/>' % (ax, ay, bx, by))
        else:
            add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="0.07"/>' % (ax, ay, bx, by, "#7a4a22" if op.get("kind") == "front" else "#8a8f8c"))
    for w in H.WINDOWS:
        (ax, ay), (bx, by) = w["a"], w["b"]
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#ffffff" stroke-width="%g"/>' % (ax, ay, bx, by, T + 0.02))
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="0.06"/>' % (ax, ay, bx, by, "#8a8f8c" if w.get("door") else "#3f7fd0"))
    total = 0
    for r in H.ALL_ROOMS:
        poly = r.get("poly")
        a = H.area(poly) if poly else 0
        total += a
        small = r.get("small", bool(poly) and a < 6) or not poly and r.get("small", False)
        lx, ly = (r.get("label_tour") if final and r.get("label_tour") else r["label"])
        add('<text x="%g" y="%g" font-size="%g" font-weight="700" text-anchor="middle" fill="#1f2321">%s</text>' % (lx, ly, 0.25 if small else 0.36, r["name"]))
        if poly and not small:
            add('<text x="%g" y="%g" font-size="0.26" text-anchor="middle" fill="#6a6f6c">≈ %s م²</text>' % (lx, ly + 0.42, fa(round(a, 1))))
    if not final:
        for q in d.get("questions", []):                # what is assumed, not seen: shown in red so the owner looks at it
            if q.get("a"):
                add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#d23b2a" stroke-width="0.07"/>' % (q["a"][0], q["a"][1], q["b"][0], q["b"][1]))
            px, py = q.get("at") or [(q["a"][0] + q["b"][0]) / 2, (q["a"][1] + q["b"][1]) / 2]
            add('<circle cx="%g" cy="%g" r="0.2" fill="#d23b2a"/><text x="%g" y="%g" font-size="0.24" font-weight="700" text-anchor="middle" fill="#fff">%s</text>' % (px, py, px, py + 0.085, q.get("mark", "؟")))
        for s in d.get("steps", []):                    # the order of the walk-through
            add('<circle cx="%g" cy="%g" r="0.24" fill="#2e58c4"/><text x="%g" y="%g" font-size="0.28" font-weight="700" text-anchor="middle" fill="#fff">%s</text>' % (s["at"][0], s["at"][1], s["at"][0], s["at"][1] + 0.1, s["mark"]))
        add('<text x="%g" y="%g" font-size="0.42" font-weight="700" text-anchor="start" fill="#1f2321">پلان پیش‌نویس — برای تأیید</text>' % (vx + vw - 0.5, vy + 0.75))
        add('<text x="%g" y="%g" font-size="0.25" text-anchor="start" fill="#6a6f6c">%s · جمع تقریبی %s متر مربع · آبی: ترتیب مسیر · قرمز: فرض‌هایی که باید تأیید شوند</text>' % (
            vx + vw - 0.5, vy + 1.2, "ابعاد اندازه‌گیری‌شده" if d.get("measured") else "ابعاد تخمینی است", fa(round(total))))
    # overall sizes of the first room, scale bar, legend
    def dim(ax, ay, bx, by, txt):
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#9a9f9c" stroke-width="0.02"/>' % (ax, ay, bx, by))
        if ay == by:
            add('<text x="%g" y="%g" font-size="0.24" text-anchor="middle" fill="#6a6f6c">%s</text>' % ((ax + bx) / 2, ay - 0.12, txt))
        else:
            add('<text x="%g" y="%g" font-size="0.24" text-anchor="middle" fill="#6a6f6c" transform="rotate(-90 %g %g)">%s</text>' % (ax - 0.12, (ay + by) / 2, ax - 0.12, (ay + by) / 2, txt))
    for m in d.get("dims", []):
        (ax, ay), (bx, by) = m["a"], m["b"]
        import math
        dim(ax, ay, bx, by, ("%s متر" if d.get("measured") else "≈ %s متر") % fa(round(math.hypot(bx - ax, by - ay), 1)))
    add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#1f2321" stroke-width="0.04"/><text x="%g" y="%g" font-size="0.24" text-anchor="middle" fill="#6a6f6c">۲ متر</text>' % (
        x0, y1 + 1.0, x0 + 2, y1 + 1.0, x0 + 1, y1 + 1.4))
    add('<text x="%g" y="%g" font-size="0.24" text-anchor="start" fill="#6a6f6c">آبی: پنجره · قهوه‌ای: در ورودی · نارنجی: رادیاتور · خط‌چین: بازشو بدون در</text>' % (vx + vw - 0.5, y1 + 1.1))
    add("</svg>")
    return "\n".join(o), total


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    H = homelib.load(sys.argv[1])
    markup, total = svg(H, final="--final" in sys.argv)
    open(sys.argv[2], "w", encoding="utf-8").write(markup)
    print(sys.argv[2], "total %.1f m2" % total)
