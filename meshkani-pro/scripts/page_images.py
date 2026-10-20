#!/usr/bin/env python3
"""List the photos on a saved web page (HTML fetched through Drive, see RUNBOOK §1.5.1).

  page_images.py page.html [--base https://site/article] [--min 800]

Prints JSON: og/twitter image first, then <img>/<source> candidates (largest srcset entry),
each with alt text/caption and declared width when known. Icons, logos, avatars and
tracking pixels are filtered out.
"""
import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from urllib.parse import urljoin

SKIP = re.compile(r"(\.svg|logo|icon|avatar|sprite|favicon|pixel|badge|placeholder|blank|1x1|author|headshot)", re.I)


def best_from_srcset(srcset):
    best, bw = None, -1
    for part in srcset.split(","):
        bits = part.strip().split()
        if not bits:
            continue
        w = 0
        if len(bits) > 1 and bits[1].endswith("w"):
            try:
                w = int(bits[1][:-1])
            except ValueError:
                pass
        if w >= bw:
            best, bw = bits[0], w
    return best, (bw if bw > 0 else None)


class P(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta, self.imgs, self._fig = [], [], None

    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag == "meta" and (a.get("property") or a.get("name", "")).lower() in ("og:image", "og:image:secure_url", "twitter:image", "twitter:image:src"):
            if a.get("content"):
                self.meta.append(a["content"])
        elif tag in ("img", "source"):
            url, w = None, None
            for k in ("data-srcset", "srcset"):
                if a.get(k):
                    url, w = best_from_srcset(a[k])
                    break
            url = url or a.get("data-src") or a.get("data-original") or a.get("src")
            if url and not url.startswith("data:"):
                try:
                    w = w or (int(a["width"]) if a.get("width", "").isdigit() else None)
                except Exception:
                    pass
                self.imgs.append({"url": url, "w": w, "alt": a.get("alt", "")})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("page"); ap.add_argument("--base", default=""); ap.add_argument("--min", type=int, default=600)
    a = ap.parse_args()
    p = P(); p.feed(open(a.page, encoding="utf-8", errors="replace").read())
    seen, out = set(), []
    for u in p.meta:
        u = urljoin(a.base, html.unescape(u))
        if u not in seen:
            seen.add(u); out.append({"url": u, "w": None, "alt": "(page share image)"})
    for i in p.imgs:
        u = urljoin(a.base, html.unescape(i["url"]))
        if u in seen or SKIP.search(u) or (i["w"] and i["w"] < a.min):
            continue
        seen.add(u); out.append({**i, "url": u})
    json.dump(out, sys.stdout, ensure_ascii=False, indent=1)
    print()


if __name__ == "__main__":
    main()
