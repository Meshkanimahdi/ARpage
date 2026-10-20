#!/usr/bin/env python3
"""Compare the approved Persian text of an image with the OCR text read back.

  text_compare.py APPROVED.txt OCR.txt

Normalises Arabic/Persian letter variants, digits, ZWNJ and punctuation, then
reports approved words missing from the OCR and an overall similarity. OCR is a
signal, not proof: a pass here still needs the visual review.
"""
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

MAP = str.maketrans({
    "ي": "ی", "ى": "ی", "ك": "ک", "ة": "ه", "ۀ": "ه", "أ": "ا", "إ": "ا", "ٱ": "ا",
    "۰": "0", "۱": "1", "۲": "2", "۳": "3", "۴": "4", "۵": "5", "۶": "6", "۷": "7", "۸": "8", "۹": "9",
    "٠": "0", "١": "1", "٢": "2", "٣": "3", "٤": "4", "٥": "5", "٦": "6", "٧": "7", "٨": "8", "٩": "9",
    "‌": "", "‍": "", "‏": "", "‎": "", "ـ": "",
})


def norm(s):
    s = unicodedata.normalize("NFKC", s).translate(MAP)
    s = re.sub(r"[ً-ْٰ]", "", s)  # harakat
    s = re.sub(r"[^\w@.%]+", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()


def main():
    approved = norm(Path(sys.argv[1]).read_text())
    ocr = norm(Path(sys.argv[2]).read_text())
    ocr_words = set(ocr.split())
    words = [w for w in approved.split() if len(w) > 1]
    missing = [w for w in words if w not in ocr_words and w not in ocr]
    coverage = 1 - len(missing) / max(1, len(words))
    ratio = difflib.SequenceMatcher(None, approved, ocr).ratio()
    result = {
        "approved_words": len(words),
        "missing_words": missing,
        "word_coverage": round(coverage, 3),
        "char_similarity": round(ratio, 3),
        "pass": coverage >= 0.9,
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
