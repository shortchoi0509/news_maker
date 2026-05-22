"""Fail if a brief markdown has encoding-corrupted (Korean-stripped) content.

Detects the bug where article data loses all Korean characters while fixed
labels (목차/요약/전망) survive. A Korean news brief must have Korean in
essentially every '## NN.' article header; if most headers have none, the
file is corrupted and must not be emailed.

Usage: python _verify_brief.py <brief.md> [<brief2.md> ...]
Exit 0 if all briefs pass, 1 if any looks corrupted, 2 on bad usage.
"""

from __future__ import annotations

import re
import sys

HANGUL = re.compile(r"[가-힣]")
ARTICLE_HEADER = re.compile(r"##\s+\d+[.\s]")
BROKEN_RATIO_THRESHOLD = 0.3


def check(path: str) -> bool:
    text = open(path, encoding="utf-8").read()
    headers = [ln for ln in text.splitlines() if ARTICLE_HEADER.match(ln)]
    if not headers:
        print(f"::warning::{path}: no '## NN.' article headers, skipping check")
        return True
    broken = [h for h in headers if not HANGUL.search(h)]
    ratio = len(broken) / len(headers)
    if ratio > BROKEN_RATIO_THRESHOLD:
        print(
            f"::error::{path}: {len(broken)}/{len(headers)} article headers "
            f"have no Korean ({ratio:.0%}) — content looks encoding-corrupted"
        )
        return False
    print(f"{path}: OK ({len(headers)} headers, {len(broken)} without Korean)")
    return True


def main() -> int:
    paths = sys.argv[1:]
    if not paths:
        print("::error::usage: python _verify_brief.py <brief.md> ...", file=sys.stderr)
        return 2
    ok = True
    for path in paths:
        try:
            if not check(path):
                ok = False
        except FileNotFoundError:
            print(f"::error::brief not found: {path}", file=sys.stderr)
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
