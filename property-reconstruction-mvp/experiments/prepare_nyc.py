"""Build the test inputs from the Zip-NeRF "nyc" capture (990 photos taken while walking through an apartment).

  photos_14 / photos_30 : listing-style photo sets, evenly spread along the walk,
                          each nudged to the sharpest frame nearby (a photographer keeps the sharp shot)
  walkthrough.mp4       : the full continuous sequence encoded as an ordinary H.264 phone-style video
                          (1280 px wide, 15 fps, CRF 23), so the video path runs on a real compressed file

The reference reconstruction (all 990 photos) stays untouched for evaluation only.
"""
import json
import os
import subprocess
import sys

import cv2

src, out = sys.argv[1], sys.argv[2]          # .../nyc/images  , output dir
names = sorted(f for f in os.listdir(src) if f.lower().endswith(".jpg"))
os.makedirs(out, exist_ok=True)


def sharp(name):
    g = cv2.imread(os.path.join(src, name), cv2.IMREAD_GRAYSCALE)
    g = cv2.resize(g, (640, int(640 * g.shape[0] / g.shape[1])))
    return cv2.Laplacian(g, cv2.CV_64F).var()


def pick(n, window=8):
    step = len(names) / n
    chosen = []
    for k in range(n):
        c = int(step * (k + 0.5))
        cands = range(max(0, c - window), min(len(names), c + window + 1))
        chosen.append(max(cands, key=lambda i: sharp(names[i])))
    return chosen


sets = {}
for n in (14, 30):
    idx = pick(n)
    sets[f"photos_{n}"] = [names[i] for i in idx]
    d = os.path.join(out, f"photos_{n}")
    os.makedirs(d, exist_ok=True)
    for i in idx:
        dst = os.path.join(d, names[i])
        if not os.path.exists(dst):
            os.symlink(os.path.join(src, names[i]), dst)

listfile = os.path.join(out, "frames.txt")
with open(listfile, "w") as fp:
    fp.writelines(f"file '{os.path.join(src, n)}'\nduration {1/15:.6f}\n" for n in names)
video = os.path.join(out, "walkthrough.mp4")
if not os.path.exists(video):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", listfile,
                    "-vf", "scale=1280:-2,fps=15", "-c:v", "libx264", "-crf", "23", "-pix_fmt", "yuv420p", video], check=True)

json.dump({"sets": sets, "video_frame_to_image": names}, open(os.path.join(out, "inputs.json"), "w"), indent=1)
print({k: len(v) for k, v in sets.items()}, "video:", os.path.getsize(video) // 1_000_000, "MB")
