"""Turn panoramas whose content the image model placed off the plan's heading, so the rings and minimap line up.

  python3 tools/align.py PANO_DIR      (run once, after privacy.py)

Degrees measured by overlaying each layout guide on its panorama: the window of points 3 and 4 came out about
73 and 25 degrees to the left of where the plan puts it.
"""
import os
import sys

import cv2
import numpy as np

ROLL_DEG = {3: 73, 4: 25}

if __name__ == "__main__":
    for n, deg in ROLL_DEG.items():
        p = os.path.join(sys.argv[1], f"pano{n:02d}.jpg")
        img = cv2.imread(p)
        img = np.roll(img, int(round(deg / 360 * img.shape[1])), axis=1)
        cv2.imwrite(p, img, [cv2.IMWRITE_JPEG_QUALITY, 88])
        print("turned", p, deg)
