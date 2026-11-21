"""Look at a rendered panorama against the plan before anyone else does. Costs nothing; skipping it cost the most.

  python3 check_pano.py overlay GUIDES N PANO OUT.jpg                the panorama, and the plan's edges drawn over it in red
  python3 check_pano.py risks   GUIDES N PANO OUT.jpg                every far / narrow / grazing feature, zoomed, beside the render
  python3 check_pano.py zoom    GUIDES N PANO OUT.jpg X0 X1 Y0 Y1    one box (percent), zoomed, beside the render
  python3 check_pano.py seam    GUIDES N PANO OUT.jpg                the stretch where the image model's left and right edges met
  python3 check_pano.py compare A.jpg B.jpg OUT.jpg X0 X1 Y0 Y1      before / after of one box

Open every OUT.jpg and actually look: the red edges should sit on the photo's corners, door frames and windows; each
zoomed pair should show the same things in the same places; plain walls must not have folds, ghost outlines or blur.
"""
import os
import sys

import cv2
import numpy as np


def guide(guides, n, W, H):
    g = cv2.imread(os.path.join(guides, "guide%02d.png" % n))
    roll = float(open(os.path.join(guides, "roll%02d.txt" % n)).read())
    return cv2.resize(np.roll(g, int(round(roll * g.shape[1])), 1), (W, H), interpolation=cv2.INTER_CUBIC), roll


def box(im, x0, x1, y0, y1, margin=0.6):
    """Cut a percent box (plus some surrounding) out of a panorama; x may run across the edge."""
    H, W = im.shape[:2]
    if x0 > x1:
        x1 += 100
    w = (x1 - x0) * margin + 2
    a, b = int((x0 - w) / 100 * W), int((x1 + w) / 100 * W)
    hh = (y1 - y0) * margin + 2
    t, u = max(0, int((y0 - hh) / 100 * H)), min(H, int((y1 + hh) / 100 * H))
    return np.take(im, range(a, b), axis=1, mode="wrap")[t:u]


def fit(im, w):
    return cv2.resize(im, (w, max(1, int(w * im.shape[0] / im.shape[1]))), interpolation=cv2.INTER_CUBIC)


def pair(pano, g, x0, x1, y0, y1, label="", w=900):
    a, b = fit(box(pano, x0, x1, y0, y1), w), fit(box(g, x0, x1, y0, y1), w)
    out = np.hstack([a, b])
    if label:
        cv2.rectangle(out, (0, 0), (out.shape[1], 30), (255, 255, 255), -1)
        cv2.putText(out, label[:150], (8, 21), 0, .55, (0, 0, 200), 1, cv2.LINE_AA)
    return out


def main(a):
    cmd = a[0]
    if cmd == "compare":
        A, B = cv2.imread(a[1]), cv2.imread(a[2]); x = [float(v) for v in a[4:8]]
        cv2.imwrite(a[3], np.hstack([fit(box(A, *x), 900), fit(box(B, *x), 900)]), [cv2.IMWRITE_JPEG_QUALITY, 88]); return
    guides, n, pano, out = a[1], int(a[2]), cv2.imread(a[3]), a[4]
    H, W = pano.shape[:2]
    if cmd == "overlay":
        p = cv2.resize(pano, (1600, 800), interpolation=cv2.INTER_AREA)
        sid = np.load(os.path.join(guides, "sid%02d.npy" % n)); e = np.zeros(sid.shape, bool)
        e[:, 1:] |= sid[:, 1:] != sid[:, :-1]; e[1:, :] |= sid[1:, :] != sid[:-1, :]
        e = cv2.resize(cv2.dilate(e.astype(np.uint8), np.ones((3, 3), np.uint8)), (1600, 800), interpolation=cv2.INTER_NEAREST) > 0
        o = p.copy(); o[e] = (0, 0, 255)
        for k in range(0, 101, 10):
            cv2.putText(o, "%d" % k, (min(int(k / 100 * 1599) + 3, 1560), 18), 0, .5, (0, 255, 255), 1)
        cv2.imwrite(out, np.vstack([p, o]), [cv2.IMWRITE_JPEG_QUALITY, 88])
    elif cmd == "zoom":
        g, _ = guide(guides, n, W, H)
        cv2.imwrite(out, pair(pano, g, *[float(v) for v in a[5:9]]), [cv2.IMWRITE_JPEG_QUALITY, 90])
    elif cmd == "risks":
        g, _ = guide(guides, n, W, H)
        rows = []
        for line in open(os.path.join(guides, "risks%02d.txt" % n)):
            if line.strip():
                nums, label = line.split("|")[0].split(), " | ".join(s.strip() for s in line.split("|")[1:])
                rows.append(pair(pano, g, *[float(v) for v in nums], label="%s  [%s]" % (label, " ".join(nums)), w=700))
        if not rows:
            print("point %d has no risk spots" % n); return
        w = max(r.shape[1] for r in rows)
        cv2.imwrite(out, np.vstack([cv2.copyMakeBorder(r, 0, 6, 0, w - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in rows]), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(out, len(rows), "risk spots: look at each pair")
    elif cmd == "seam":
        _, roll = guide(guides, n, 64, 32)
        x = roll * 100
        cv2.imwrite(out, fit(box(pano, x - 9, x + 9, 15, 85, margin=0), 1300), [cv2.IMWRITE_JPEG_QUALITY, 90])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    main(sys.argv[1:])
