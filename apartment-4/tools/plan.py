"""Draft floor plan of the fourth apartment, read from 40 photos and a narrated 73-second walk-through.

  python3 tools/plan.py OUT.svg

Coordinates in metres: x to the right, y down. The window wall of the living room is the top edge; the front door is on
the bottom side. All sizes are ESTIMATES (floor tiles of about 80 cm, door widths, radiators); nothing was measured.
"""
import sys

XE, W, HS = 10.0, 4.7, 3.6            # living room length, depth; south edge of the corridor
T = 0.16                               # wall thickness as drawn

# rooms: name, polygon (inner outline), label position
ROOMS = [
    ("living", "پذیرایی و نشیمن", [(0, 0), (XE, 0), (XE, 2.4), (XE, HS), (9.8, HS), (8.8, 4.6), (8.8, 6.4), (7.0, 6.4), (7.0, W), (0, W)], (5.6, 1.9)),
    ("kitchen", "آشپزخانه (اپن)", None, (2.2, 2.2)),
    ("entry", "ورودی", None, (7.9, 5.2)),
    ("wc", "سرویس مهمان", [(4.8, 4.86), (6.84, 4.86), (6.84, 6.4), (4.8, 6.4)], (6.0, 5.3)),
    ("hall", "راهرو", [(XE, 2.4), (12.3, 2.4), (12.3, HS), (XE, HS)], (11.5, 2.95)),
    ("bath", "حمام و سرویس", [(10.16, 0.2), (12.1, 0.2), (12.1, 2.24), (10.16, 2.24)], (10.95, 1.2)),
    ("bed1", "اتاق خواب ۱", [(9.95, 3.76), (12.9, 3.76), (12.9, 7.6), (8.96, 7.6), (8.96, 4.75)], (10.6, 5.9)),
    ("bed2", "اتاق خواب ۲", [(12.3, 2.4), (13.1, 2.4), (13.1, 1.1), (16.5, 1.1), (16.5, 4.6), (16.9, 4.6), (16.9, 5.6), (13.1, 5.6), (13.1, HS), (12.3, HS)], (14.9, 3.2)),
]
# openings cut into the drawn walls: (x0, y0, x1, y1, kind)
DOORS = [
    (7.45, 6.4, 8.45, 6.4, "front"),          # front door, bottom wall of the entry
    (7.0, 5.1, 7.0, 5.9, "door"),             # guest WC
    (10.25, 2.4, 11.05, 2.4, "door"),         # bathroom
    (10.15, HS, 11.05, HS, "door"),           # bedroom 1
    (12.3, 2.55, 12.3, 3.45, "door"),         # bedroom 2
    (XE, 2.4, XE, HS, "open"),                # living room -> corridor
    (0.55, 0, 1.4, 0, "door"),                # terrace door
]
WINDOWS = [(2.3, 0, 4.0, 0), (5.0, 0, 6.7, 0), (7.6, 0, 9.3, 0), (12.9, 6.0, 12.9, 7.2), (13.4, 5.6, 14.8, 5.6)]
FIXTURES = [   # (x0, y0, x1, y1, label)
    (0.06, 4.1, 4.5, 4.64, "کابینت و گاز"), (0.06, 2.9, 0.66, 4.1, "یخچال"), (1.5, 2.75, 3.1, 3.45, "جزیره"),
    (12.3, 3.86, 12.84, 5.6, "کمد"), (12.5, 1.2, 13.04, 2.3, "کمد"),
    (10.26, 0.26, 10.86, 0.7, "روشویی"), (11.5, 0.3, 12.04, 0.95, "توالت"), (11.25, 1.45, 12.04, 2.18, "دوش"),
    (5.0, 5.9, 5.5, 6.34, "روشویی"), (4.9, 5.0, 5.4, 5.5, "توالت"),
]
# the corner between the corridor and the entry is cut diagonally (confirmed by the owner); size is an estimate
CHAMFER = ((9.8, HS), (8.8, 4.6))
COLUMNS = [(9.62, 0, 10.0, 0.36), (0, 0, 0.34, 0.4)]
RADIATORS = [(8.8, 4.85, 8.8, 6.15), (5.1, W, 6.5, W), (0, 1.3, 0, 2.6)]
STEPS = [(7.95, 5.95, "۱", "در ورودی"), (6.5, 6.1, "۲", "سرویس مهمان، سمت چپ"), (6.0, 0.9, "۳", "پنجره‌ها"),
         (1.0, 0.9, "۴", "در تراس"), (3.7, 3.1, "۵", "آشپزخانه"), (10.45, 3.0, "۶", "راهرو"),
         (10.6, 4.6, "۷", "خواب اول، سمت راست"), (14.2, 2.0, "۸", "خواب بعدی، مستقیم"), (10.55, 1.9, "۹", "حمام، روبه‌روی خواب اول")]


def fa(v):
    return str(v).translate(str.maketrans("0123456789.", "۰۱۲۳۴۵۶۷۸۹٫"))


def area(p):
    return abs(sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))) / 2


def main(out):
    o = []
    add = o.append
    add('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1.4 -2.6 20 12.6" font-family="Vazirmatn, Tahoma, sans-serif">')
    add('<rect x="-1.4" y="-2.6" width="20" height="12.6" fill="#ffffff"/>')
    # light well and terrace (outside the flat, sizes unknown)
    add('<rect x="13.1" y="5.76" width="3.4" height="1.84" fill="#eef3f8" stroke="#9db2c8" stroke-width="0.03" stroke-dasharray="0.12 0.08"/>')
    add('<text x="14.8" y="6.8" font-size="0.26" text-anchor="middle" fill="#5d7388">نورگیر (برآورد)</text>')
    add('<rect x="0" y="-1.3" width="2.2" height="1.14" fill="#eef3f8" stroke="#9db2c8" stroke-width="0.03" stroke-dasharray="0.12 0.08"/>')
    add('<text x="1.1" y="-0.62" font-size="0.26" text-anchor="middle" fill="#5d7388">تراس (ابعاد نامعلوم)</text>')
    for _, _, poly, _ in ROOMS:
        if poly:
            add('<polygon points="%s" fill="#fbfaf7" stroke="#222725" stroke-width="%s" stroke-linejoin="miter"/>' % (" ".join("%g,%g" % p for p in poly), T))
    for x0, y0, x1, y1, lab in FIXTURES:
        add('<rect x="%g" y="%g" width="%g" height="%g" fill="#eeece6" stroke="#8a8f8c" stroke-width="0.025"/>' % (x0, y0, x1 - x0, y1 - y0))
        add('<text x="%g" y="%g" font-size="0.17" text-anchor="middle" fill="#6a6f6c">%s</text>' % ((x0 + x1) / 2, (y0 + y1) / 2 + 0.06, lab))
    for x0, y0, x1, y1 in COLUMNS:
        add('<rect x="%g" y="%g" width="%g" height="%g" fill="#222725"/>' % (x0, y0, x1 - x0, y1 - y0))
    for x0, y0, x1, y1 in RADIATORS:
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#c2703d" stroke-width="0.09" transform="translate(%g %g)"/>' % (x0, y0, x1, y1, 0.12 if x0 == x1 and x0 < 5 else (-0.12 if x0 == x1 else 0), -0.12 if y0 == y1 else 0))
    for x0, y0, x1, y1, kind in DOORS:
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#fbfaf7" stroke-width="%g"/>' % (x0, y0, x1, y1, T + 0.04))
        if kind == "open":
            add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#8a8f8c" stroke-width="0.02" stroke-dasharray="0.1 0.07"/>' % (x0, y0, x1, y1))
        else:
            add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" stroke-width="0.07"/>' % (x0, y0, x1, y1, "#7a4a22" if kind == "front" else "#8a8f8c"))
    for x0, y0, x1, y1 in WINDOWS:
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#ffffff" stroke-width="%g"/>' % (x0, y0, x1, y1, T + 0.02))
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#3f7fd0" stroke-width="0.06"/>' % (x0, y0, x1, y1))
    (cx0, cy0), (cx1, cy1) = CHAMFER
    add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#d23b2a" stroke-width="0.05"/>' % (cx0, cy0, cx1, cy1))
    add('<text x="8.75" y="3.95" font-size="0.2" text-anchor="end" fill="#d23b2a">برش مورب</text>')
    total = 0
    for key, name, poly, (lx, ly) in ROOMS:
        small = key in ("wc", "hall", "bath", "entry")
        add('<text x="%g" y="%g" font-size="%g" font-weight="700" text-anchor="middle" fill="#1f2321">%s</text>' % (lx, ly, 0.25 if small else 0.36, name))
        if poly:
            a = area(poly) - (1.8 * 1.7 if key == "living" else 0)
            total += area(poly)
            add('<text x="%g" y="%g" font-size="%g" text-anchor="middle" fill="#6a6f6c">≈ %s م²</text>' % (lx, ly + (0.3 if small else 0.42), 0.2 if small else 0.26, fa(round(a, 1))))
    # walk-through order from the narration
    for x, y, n, _ in STEPS:
        add('<circle cx="%g" cy="%g" r="0.24" fill="#2e58c4"/><text x="%g" y="%g" font-size="0.28" font-weight="700" text-anchor="middle" fill="#fff">%s</text>' % (x, y, x, y + 0.1, n))
    # dimensions
    def dim(x0, y0, x1, y1, txt, off):
        add('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="#9a9f9c" stroke-width="0.02"/>' % (x0, y0, x1, y1))
        if y0 == y1:
            add('<text x="%g" y="%g" font-size="0.24" text-anchor="middle" fill="#6a6f6c">%s</text>' % ((x0 + x1) / 2, y0 + off, txt))
        else:
            add('<text x="%g" y="%g" font-size="0.24" text-anchor="middle" fill="#6a6f6c" transform="rotate(-90 %g %g)">%s</text>' % (x0 + off, (y0 + y1) / 2, x0 + off, (y0 + y1) / 2, txt))
    dim(0, -1.75, XE, -1.75, "≈ %s متر" % fa(XE), -0.12)
    dim(-0.7, 0, -0.7, W, "≈ %s متر" % fa(W), -0.12)
    add('<text x="18.4" y="-2.0" font-size="0.42" font-weight="700" text-anchor="end" fill="#1f2321">پلان پیش‌نویس — برای تأیید</text>')
    add('<text x="18.4" y="-1.5" font-size="0.25" text-anchor="end" fill="#6a6f6c">ابعاد تخمینی است · جمع تقریبی %s متر مربع · دایره‌های آبی: ترتیب مسیر در ویدئو</text>' % fa(round(total)))
    add('<line x1="0" y1="8.6" x2="2" y2="8.6" stroke="#1f2321" stroke-width="0.04"/><text x="1" y="9.0" font-size="0.24" text-anchor="middle" fill="#6a6f6c">۲ متر</text>')
    add('<text x="18.4" y="8.7" font-size="0.24" text-anchor="end" fill="#6a6f6c">آبی: پنجره · قهوه‌ای: در ورودی · نارنجی: رادیاتور · خط‌چین: بازشو بدون در</text>')
    add("</svg>")
    open(out, "w", encoding="utf-8").write("\n".join(o))
    print(out, "total", round(total, 1))


if __name__ == "__main__":
    main(sys.argv[1])
