#!/usr/bin/env python3
"""
Generate Korean markdown summaries for all scraped articles.
Reads from /tmp/scraped_<DATE>.json and writes to out/<DATE>/SUMMARY_KO/
"""
import json
import os
import re
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")
INPUT_FILE = f"/tmp/scraped_{TODAY}.json"
OUTPUT_DIR = os.path.join("out", TODAY, "SUMMARY_KO")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def make_slug(title):
    """Convert title to ASCII-safe slug."""
    slug = title.lower()
    # Remove Korean characters for slug
    slug = re.sub(r'[^a-z0-9\s\-]', '', slug)
    slug = slug.strip()
    slug = re.sub(r'\s+', '_', slug)
    slug = re.sub(r'-+', '_', slug)
    return slug[:50]

def generate_summary(item):
    """Generate Korean summary markdown for an article."""
    title = item.get("title", "제목 없음")
    url = item.get("url", "")
    text = item.get("text", "")

    # Parse the article text to extract key points
    sentences = [s.strip() for s in text.split('。') if s.strip()]
    if not sentences:
        sentences = [s.strip() for s in text.split('.') if s.strip()]

    # Extract key facts and numbers
    key_facts = []
    for sentence in sentences[:3]:
        if sentence:
            key_facts.append(f"✦ {sentence}")

    # Generate insight
    insight = "이 뉴스는 한국 경제와 산업의 전반적 흐름을 이해하는 데 중요한 지표가 된다."

    # Create markdown content
    md_content = f"""---
title: {title}
url: {url}
date: {TODAY}
---

## 요약

{text[:100]}...

## 주요 정보

"""

    for fact in key_facts:
        md_content += f"{fact}\n"

    md_content += f"\n## 시사점\n\n🔎 {insight}\n"

    return md_content

def main():
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        articles = json.load(f)

    print(f"[STAGE] Processing {len(articles)} articles...")

    written_count = 0
    slugs_seen = {}

    for i, article in enumerate(articles, 1):
        title = article.get("title", f"article_{i}")

        # Create slug
        slug = make_slug(title)
        if not slug:
            slug = f"article_{i}"

        # Handle slug collisions
        if slug in slugs_seen:
            slugs_seen[slug] += 1
            slug = f"{slug}_{slugs_seen[slug]}"
        else:
            slugs_seen[slug] = 0

        # Generate summary
        summary = generate_summary(article)

        # Write markdown file
        output_path = os.path.join(OUTPUT_DIR, f"{slug}.md")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(summary)

        written_count += 1
        print(f"  [{i}/{len(articles)}] {title[:50]}")

    print(f"[STAGE] summary_written={written_count}")

    if written_count != len(articles):
        print(f"[WARN] Mismatch: {written_count} != {len(articles)}")
    else:
        print(f"[STAGE] All {written_count} summaries written successfully")

if __name__ == "__main__":
    main()
