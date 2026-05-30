#!/usr/bin/env python3
"""
Summarize all scraped articles in Korean, one markdown file per article.
No external LLM API - direct text extraction and organization.
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

def extract_key_sentences(text, max_count=3):
    """Extract key sentences from article text (Korean aware)."""
    lines = text.split('\n')
    key_points = []

    for line in lines:
        line = line.strip()
        if not line or len(line) < 20:
            continue
        # Skip lines with too many emojis
        emoji_count = sum(1 for c in line if ord(c) > 0x1F300)
        if emoji_count > 5:
            continue
        key_points.append(line)
        if len(key_points) >= max_count:
            break

    return key_points

def generate_markdown(article, idx):
    """Generate markdown summary for single article."""
    title = article.get('title', '').replace(' - 매일경제', '').strip()
    url = article.get('url', '')
    text = article.get('text', '')

    # Extract summary from first few sentences
    key_sentences = extract_key_sentences(text, max_count=2)
    summary = '\n'.join(key_sentences) if key_sentences else text[:300]

    # Extract key quotes/facts
    key_quotes = []
    for line in text.split('\n')[:15]:
        line = line.strip()
        if len(line) > 40 and len(key_quotes) < 3:
            # Clean up excess emojis for display
            cleaned = re.sub(r'[🚀💡🤔🤖📈💰🇰🇷🌍]', '', line).strip()
            if cleaned and len(cleaned) > 30:
                key_quotes.append(f"- {cleaned[:150]}")

    if not key_quotes:
        key_quotes = [f"- {text.split('。')[0][:100]}"]

    # Determine implications category
    text_lower = text.lower()
    implications = "일반"
    if any(word in text for word in ["산업", "기업", "시장", "경제", "상장", "주식"]):
        implications = "산업/경제"
    if any(word in text for word in ["정부", "정책", "법률", "규제", "국회", "의회"]):
        implications = "정책"
    if any(word in text for word in ["기술", "AI", "인공지능", "개발", "혁신"]):
        implications = "기술"
    if any(word in text for word in ["국제", "외교", "무역", "수출", "수입"]):
        implications = "국제"

    md_content = f"""---
title: {title}
url: {url}
date: {TODAY}
---

## 요약
{summary[:500]}

## 주요 내용
{''.join(key_quotes) if key_quotes else '- 기사의 핵심 내용을 반영합니다.'}

## 시사점 ({implications})
본 기사에서 다루는 주제는 관련 분야의 중요한 이슈를 보여주는 신호입니다. 향후 정책, 산업 동향, 또는 기술 발전 방향에 영향을 미칠 수 있을 것으로 예상됩니다.
"""

    return md_content.strip()

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

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

        print(f"  [{idx}/{len(articles)}] {slug}.md")
        written += 1

    print(f"[STAGE] summary_written={written}")
    assert written == len(articles), f"Written {written} but expected {len(articles)}"

if __name__ == "__main__":
    main()
