"""Get the owner's photos and video into a shape that can be studied.

  python3 media.py convert SRC_DIR OUT_DIR [--prefix p]     any image type -> p01.jpg, p02.jpg ... in file-name order
  python3 media.py frames VIDEO OUT_DIR --every 2           one frame every 2 s -> v000.jpg, v002.jpg ... (name = second)
  python3 media.py frames VIDEO OUT_DIR --at 1,17.5,30      frames at chosen seconds
  python3 media.py sheet OUT.jpg IMAGE [IMAGE ...] [--height 420] [--cols 6]    labelled contact sheet for reading many at once
  OPENROUTER_API_KEY=... python3 media.py transcribe VIDEO_OR_AUDIO [--language Persian]    the narration, with timestamps

Photos are numbered in the order they were taken because that order is evidence: people start at the front door and
walk on, so photo 7 was taken near photos 6 and 8. Keep the numbers when files go missing rather than renumbering.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import tempfile
import urllib.request


def convert(a):
    from PIL import Image, ImageOps
    os.makedirs(a.out, exist_ok=True)
    files = sorted(f for f in os.listdir(a.src) if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic", ".heif", ".bmp", ".tif", ".tiff")))
    for i, f in enumerate(files, 1):
        src, dst = os.path.join(a.src, f), os.path.join(a.out, "%s%02d.jpg" % (a.prefix, i))
        try:
            ImageOps.exif_transpose(Image.open(src)).convert("RGB").save(dst, quality=93)
        except Exception:                                   # formats Pillow cannot read here (AVIF, HEIC): let ffmpeg try
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", src, "-q:v", "2", dst], check=True)
        print(f, "->", os.path.basename(dst))
    print(len(files), "photos. Check this count against what the owner says they sent.")


def frames(a):
    import cv2
    os.makedirs(a.out, exist_ok=True)
    cap = cv2.VideoCapture(a.video)
    length = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    times = [float(t) for t in a.at.split(",")] if a.at else [t * a.every for t in range(int(length / a.every) + 1)]
    for t in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if ok:
            name = "v%03d.jpg" % t if float(t).is_integer() else "v%05.1f.jpg" % t
            cv2.imwrite(os.path.join(a.out, name), f, [cv2.IMWRITE_JPEG_QUALITY, 93])
    print("%.0f s of video, %d frames in %s (%dx%d)" % (length, len(times), a.out, cap.get(3), cap.get(4)))


def sheet(a):
    import cv2
    import numpy as np
    cells = []
    for p in a.images:
        im = cv2.imread(p)
        if im is None:
            continue
        im = cv2.resize(im, (int(im.shape[1] * a.height / im.shape[0]), a.height), interpolation=cv2.INTER_AREA)
        name = os.path.splitext(os.path.basename(p))[0]
        cv2.rectangle(im, (0, 0), (14 + 17 * len(name), 34), (255, 255, 255), -1)
        cv2.putText(im, name, (6, 26), 0, .85, (0, 0, 220), 2, cv2.LINE_AA)
        cells.append(im)
    rows = []
    for i in range(0, len(cells), a.cols):
        rows.append(np.hstack(cells[i:i + a.cols]))
    w = max(r.shape[1] for r in rows)
    cv2.imwrite(a.out, np.vstack([cv2.copyMakeBorder(r, 0, 4, 0, w - r.shape[1], cv2.BORDER_CONSTANT, value=(255, 255, 255)) for r in rows]), [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(a.out, len(cells), "images")


def transcribe(a):
    with tempfile.TemporaryDirectory() as tmp:
        mp3 = os.path.join(tmp, "a.mp3")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", a.media, "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", mp3], check=True)
        audio = base64.b64encode(open(mp3, "rb").read()).decode()
    text = ("This is the audio of a walk-through video of a home, spoken in %s. Transcribe everything that is said, word for word, in "
            "%s, with a timestamp [mm:ss] at the start of each sentence. Do not add or guess anything that is not said. If a part is "
            "unclear, mark it as [unclear]." % (a.language, a.language))
    body = {"model": os.environ.get("AUDIO_MODEL", "google/gemini-2.5-flash"), "temperature": 0, "messages": [{"role": "user", "content": [
        {"type": "text", "text": text}, {"type": "input_audio", "input_audio": {"data": audio, "format": "mp3"}}]}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", json.dumps(body).encode(),
                                 {"Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    res = json.load(urllib.request.urlopen(req, timeout=300))
    print(res["choices"][0]["message"]["content"])
    print("cost $%s" % res.get("usage", {}).get("cost"), file=sys.stderr)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("convert"); p.add_argument("src"); p.add_argument("out"); p.add_argument("--prefix", default="p"); p.set_defaults(f=convert)
    p = sub.add_parser("frames"); p.add_argument("video"); p.add_argument("out"); p.add_argument("--every", type=float, default=2); p.add_argument("--at", default=""); p.set_defaults(f=frames)
    p = sub.add_parser("sheet"); p.add_argument("out"); p.add_argument("images", nargs="+"); p.add_argument("--height", type=int, default=420); p.add_argument("--cols", type=int, default=6); p.set_defaults(f=sheet)
    p = sub.add_parser("transcribe"); p.add_argument("media"); p.add_argument("--language", default="Persian"); p.set_defaults(f=transcribe)
    a = ap.parse_args()
    a.f(a)
