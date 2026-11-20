"""Remove people from finished panoramas: personal photos and posters become plain frames, a reflection is inpainted.

  python3 tools/privacy.py PANO_DIR

Boxes are pixel rectangles on the 4096x2048 panoramas, found by eye for this apartment.
"""
import os
import sys

import cv2
import numpy as np

FRAMES = {   # pano number -> rectangles (x0, y0, x1, y1) of pictures that show people
    7: [(1868, 830, 1928, 916), (2158, 830, 2214, 910)],
    9: [(2528, 745, 2705, 965), (2680, 742, 2862, 882), (2750, 885, 2812, 930),
        (3212, 700, 3358, 928), (3165, 722, 3202, 788), (3162, 888, 3198, 948), (3372, 862, 3418, 932),
        (3380, 684, 3424, 766)],
}
INPAINT = {  # pano number -> rectangles to inpaint (a reflection in a mirror)
    1: [(1902, 858, 1990, 1112)],
}


def plain_frame(img, x0, y0, x1, y1):
    """Keep the outer edge as a dark frame, fill the picture with plain paper."""
    b = max(3, (x1 - x0) // 14)
    img[y0:y1, x0:x1] = (38, 42, 46)
    inner = img[y0 + b:y1 - b, x0 + b:x1 - b]
    h, w = inner.shape[:2]
    shade = np.linspace(0, 1, h)[:, None, None]
    inner[:] = (np.array([226, 232, 236]) * (1 - .06 * shade)).astype(np.uint8)


def main(d):
    for n in sorted(set(FRAMES) | set(INPAINT)):
        p = os.path.join(d, f"pano{n:02d}.jpg")
        img = cv2.imread(p)
        for r in FRAMES.get(n, []):
            plain_frame(img, *r)
        if n in INPAINT:
            mask = np.zeros(img.shape[:2], np.uint8)
            for x0, y0, x1, y1 in INPAINT[n]:
                mask[y0:y1, x0:x1] = 255
            img = cv2.inpaint(img, mask, 9, cv2.INPAINT_TELEA)
        cv2.imwrite(p, img, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print("cleaned", p)


if __name__ == "__main__":
    main(sys.argv[1])
