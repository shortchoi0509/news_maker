"""Fail if a brief markdown is low-quality (encoding-corrupted or template-filled).

Checks three failure modes that have been observed in produced briefs:

1. Korean stripped — the encoding-loss bug where article data loses Korean
   characters while fixed labels survive. Detected by '## NN.' headers
   with no Korean.
2. 시사점 duplication — Claude falling back to a per-category cliché
   dictionary instead of writing article-specific takeaways. Detected by
   the same '### 시사점' line appearing in multiple articles.
3. 전망 totally empty — every '### 전망' set to '(원문에 명시된 전망 없음)'.
   Real Maeil Business articles almost always mention some forward
   schedule; 100% empty means the LLM skipped extraction.

Usage: python _verify_brief.py <brief.md> [<brief2.md> ...]
Exit 0 if all briefs pass, 1 if any fails a check, 2 on bad usage.
"""

from __future__ import annotations

import re
import sys
from collections import Counter

HANGUL = re.compile(r"[가-힣]")
ARTICLE_HEADER = re.compile(r"##\s+\d+[.\s]")
SECTION_HEADER = re.compile(r"###\s+(요약|전망|시사점)\s*$")
NO_OUTLOOK_TEXT = "(원문에 명시된 전망 없음)"

BROKEN_HEADER_RATIO_THRESHOLD = 0.3
INSIGHT_DUP_MAX = 1  # any 시사점 line repeated > this count fails
OUTLOOK_EMPTY_RATIO_THRESHOLD = 0.9  # >90% empty 전망 fails


def _next_nonblank(lines: list[str], start: int) -> str:
    for ln in lines[start:]:
        if ln.strip():
            return ln.strip()
    return ""


def extract_sections(text: str) -> dict[str, list[str]]:
    """Return {'요약': [...], '전망': [...], '시사점': [...]}.

    For each '### <label>' header, captures the next non-blank line as
    that section's value. Good enough for the current single-line format.
    """
    out: dict[str, list[str]] = {"요약": [], "전망": [], "시사점": []}
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = SECTION_HEADER.match(ln)
        if not m:
            continue
        label = m.group(1)
        out[label].append(_next_nonblank(lines, i + 1))
    return out


def check_korean_integrity(path: str, text: str) -> bool:
    headers = [ln for ln in text.splitlines() if ARTICLE_HEADER.match(ln)]
    if not headers:
        print(f"::warning::{path}: no '## NN.' article headers, skipping Korean check")
        return True
    broken = [h for h in headers if not HANGUL.search(h)]
    ratio = len(broken) / len(headers)
    if ratio > BROKEN_HEADER_RATIO_THRESHOLD:
        print(
            f"::error::{path}: {len(broken)}/{len(headers)} article headers "
            f"have no Korean ({ratio:.0%}) — content looks encoding-corrupted"
        )
        return False
    return True


def check_insight_uniqueness(path: str, insights: list[str]) -> bool:
    if not insights:
        return True
    counts = Counter(s for s in insights if s)
    top, top_n = counts.most_common(1)[0]
    if top_n > INSIGHT_DUP_MAX:
        print(
            f"::error::{path}: 시사점 duplicated {top_n} times across articles "
            f"— LLM fell back to a cliché template. Most repeated: {top!r}"
        )
        return False
    return True


def check_outlook_coverage(path: str, outlooks: list[str]) -> bool:
    if not outlooks:
        return True
    empty = sum(1 for s in outlooks if s == NO_OUTLOOK_TEXT)
    ratio = empty / len(outlooks)
    if ratio > OUTLOOK_EMPTY_RATIO_THRESHOLD:
        print(
            f"::error::{path}: 전망 is '{NO_OUTLOOK_TEXT}' in "
            f"{empty}/{len(outlooks)} articles ({ratio:.0%}) — LLM skipped "
            f"outlook extraction; real news has forward schedules"
        )
        return False
    return True


def check(path: str) -> bool:
    text = open(path, encoding="utf-8").read()
    ok = check_korean_integrity(path, text)
    sections = extract_sections(text)
    ok = check_insight_uniqueness(path, sections["시사점"]) and ok
    ok = check_outlook_coverage(path, sections["전망"]) and ok
    if ok:
        n_articles = len(sections["요약"])
        print(f"{path}: OK ({n_articles} articles checked)")
    return ok


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
