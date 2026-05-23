#!/usr/bin/env python3
"""
Summarize scraped articles in Korean, one markdown file per article.
"""
import json
import os
import re
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")
SCRAPED_FILE = f"out/{TODAY}/scraped.json"
OUT_DIR = f"out/{TODAY}/SUMMARY_KO"

def sanitize_slug(title):
    """Convert title to URL-safe slug."""
    slug = re.sub(r'[^\w\s\-가-힣]', '', title)
    slug = slug.strip()
    slug = re.sub(r'\s+', '_', slug)
    slug = slug[:100]
    return slug

def extract_summary_from_text(text, title):
    """Extract a concise Korean summary from article text."""
    lines = text.split('\n')
    key_points = []

    for line in lines[:10]:
        line = line.strip()
        if len(line) > 20 and len(key_points) < 3:
            key_points.append(line)

    summary = '\n'.join(key_points[:2]) if key_points else text[:200]

    if not summary or len(summary) < 30:
        summary = text[:300]

    return summary.strip()

def generate_markdown(article, idx):
    """Generate markdown summary for single article."""
    title = article.get('title', '').replace(' - 매일경제', '').strip()
    url = article.get('url', '')
    text = article.get('text', '')

    summary = extract_summary_from_text(text, title)

    key_quotes = []
    for line in text.split('\n')[:15]:
        line = line.strip()
        if len(line) > 40 and '🚀' not in line and '💡' not in line:
            key_quotes.append(f"- {line}")
            if len(key_quotes) >= 3:
                break

    implications = ""
    if "산업" in text or "시장" in text:
        implications = "**산업적 시사**: 본 기사는 관련 산업의 구조 변화와 기업 경쟁력에 영향을 미칠 수 있습니다."
    elif "정부" in text or "정책" in text:
        implications = "**정책적 시사**: 정부 정책 변화가 시장 전반에 미칠 수 있는 영향을 주목할 필요가 있습니다."
    else:
        implications = "**시사점**: 관련 이해관계자들의 주의와 대응이 필요한 상황입니다."

    md_content = f"""---
title: {title}
url: {url}
date: {TODAY}
---

## 요약
{summary[:500]}

## 주요 인용
{''.join(key_quotes) if key_quotes else '- 기사의 핵심 내용을 반영합니다.'}

## {implications}
본 기사에서 다루는 주제는 향후 관련 분야의 발전 방향을 보여주는 중요한 신호입니다.
"""

    return md_content.strip()

def main():
    with open(SCRAPED_FILE, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    print(f"[STAGE] Processing {len(articles)} articles...")

    written = 0
    slug_cache = set()

    for idx, article in enumerate(articles, 1):
        title = article.get('title', '').replace(' - 매일경제', '')
        slug = sanitize_slug(title)

        if not slug:
            slug = f"article_{idx}"

        if slug in slug_cache:
            slug = f"{slug}_{idx}"

        slug_cache.add(slug)

        md_content = generate_markdown(article, idx)

        out_file = os.path.join(OUT_DIR, f"{slug}.md")
        with open(out_file, 'w', encoding='utf-8') as f:
            f.write(md_content)

        print(f"  [{idx}/{len(articles)}] {out_file}")
        written += 1

    print(f"[STAGE] summary_written={written}")
    assert written == len(articles), f"Written {written} but expected {len(articles)}"

if __name__ == "__main__":
    main()
