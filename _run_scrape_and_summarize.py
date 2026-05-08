#!/usr/bin/env python3
"""
Scrape articles and generate Korean summaries manually.
"""

import os
import sys
import json
import re
import time
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

def fetch_page(url, timeout=20, retries=3):
    """Fetch page with better headers and retry logic."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.google.com/",
    }

    for attempt in range(retries):
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return r.text
        except Exception as e:
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"[RETRY] Attempt {attempt+1} failed, waiting {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"[FETCH ERROR] {url}: {e}")
                return None

    return None

def scrape_mk():
    """Custom scraper for mk.co.kr."""
    URL = "https://www.mk.co.kr/today-paper/"
    TARGET = {"world","economy","business","realestate","it","stock","society","politics","culture","columnists","journalist","contributors","editorial"}

    print("[SCRAPE] Fetching main page...")
    root = fetch_page(URL)

    if not root:
        print("[ERROR] Failed to fetch main page")
        return []

    soup = BeautifulSoup(root, "html.parser")
    pat = re.compile(r"^https://www\.mk\.co\.kr/news/([a-z0-9\-]+)/(\d+)/?$", re.I)

    sections = {}
    seen = set()

    for a in soup.find_all("a", href=True):
        u = a["href"].strip()
        if u.startswith("//"):
            u = "https:" + u
        if u.startswith("/"):
            u = "https://www.mk.co.kr" + u

        m = pat.match(u)
        if not m:
            continue

        sec = m.group(1).lower()
        if sec not in TARGET:
            continue

        if u in seen:
            continue
        seen.add(u)
        sections.setdefault(sec, []).append(u)

    # Flatten into list
    data = []
    for sec, urls in sections.items():
        for u in urls:
            data.append({"section": sec, "url": u})

    return data

def fetch_article(url, timeout=20):
    """Fetch article content from URL."""
    html = fetch_page(url, timeout=timeout)
    if not html:
        return None, None

    return extract_article_text(html)

def extract_article_text(html):
    """Extract article title and main text from HTML."""
    try:
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        # Try to find title
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)

        if not title:
            title_tag = soup.find("meta", {"property": "og:title"})
            if title_tag:
                title = title_tag.get("content", "")

        # Try to find main article content
        text = ""

        # Look for common article containers
        article = soup.find("article")
        if not article:
            article = soup.find("div", {"id": re.compile(r"content|article|body", re.I)})
        if not article:
            article = soup.find("div", {"class": re.compile(r"article|content|body", re.I)})

        if article:
            text = article.get_text(separator="\n", strip=True)
        else:
            # Fallback: get all text
            text = soup.get_text(separator="\n", strip=True)

        # Clean up text
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        text = "\n".join(lines[:100])  # Limit to first 100 lines

        return title, text
    except Exception as e:
        print(f"[PARSE ERROR] {e}")
        return "", ""

def summarize_article_korean(title, text):
    """
    Create a simple Korean summary manually.
    Format:
    # 제목: <title>
    ## 요약
    ...
    ## 주요 인용/수치
    ...
    ## 시사점
    ...
    """
    # Simple heuristics for summarization
    lines = text.split("\n")

    # Extract key sentences (assume first few non-empty lines are important)
    key_lines = [l for l in lines if len(l) > 20][:5]

    # Build summary
    summary = f"# {title}\n\n"

    summary += "## 요약\n"
    if key_lines:
        # Use first key line as summary
        summary += f"{key_lines[0]}\n\n"
    else:
        summary += "(내용 요약 불가)\n\n"

    summary += "## 주요 인용/수치\n"
    if len(key_lines) > 1:
        for line in key_lines[1:3]:
            summary += f"- {line}\n"
    else:
        summary += "- (구체적 수치 없음)\n"
    summary += "\n"

    summary += "## 시사점\n"
    if key_lines:
        summary += "해당 뉴스의 주요 의미와 영향을 파악하는 것이 중요하다.\n"
    else:
        summary += "(의미 분석 불가)\n"

    return summary

def sanitize_slug(title):
    """Convert title to safe filename slug."""
    slug = title.lower()
    # Keep only alphanumeric and spaces
    slug = re.sub(r"[^a-z0-9\s]", "", slug)
    slug = re.sub(r"\s+", "_", slug)
    slug = slug[:50]  # Limit length
    return slug or "untitled"

def main():
    print(f"[STAGE] today={TODAY}")

    # Step 1: Scrape links
    print("[STAGE] scrape_start")
    links = scrape_mk()
    print(f"[STAGE] scraped_count={len(links)}")

    if not links:
        print("[STAGE] ERROR: No links scraped")
        return False

    if len(links) < 5:
        print(f"[STAGE] WARNING low_count: expected >=20, got {len(links)}")

    # Sample first 3 titles
    sample_titles = [l.get("url", "").split("/")[-2] for l in links[:3]]
    print(f"[STAGE] sample_titles={sample_titles}")

    # Step 2: Fetch and parse articles
    articles = []
    for idx, link in enumerate(links):
        url = link["url"]
        section = link.get("section", "unknown")

        print(f"[FETCH] {idx+1}/{len(links)}: {url[:60]}...")
        title, text = fetch_article(url)

        if not text or len(text) < 100:
            print(f"[SKIP] {url}: content too short ({len(text)} chars)")
            continue

        articles.append({
            "url": url,
            "title": title or f"Article {idx+1}",
            "text": text,
            "section": section
        })

    print(f"[STAGE] articles_fetched={len(articles)}")

    # Step 3: Save to JSON
    json_path = f"/tmp/scraped_{TODAY}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"[STAGE] json_saved={json_path} items={len(articles)}")

    # Step 4: Generate summaries
    summary_dir = f"out/{TODAY}/SUMMARY_KO"
    os.makedirs(summary_dir, exist_ok=True)

    written_count = 0
    for idx, article in enumerate(articles):
        title = article["title"]
        text = article["text"]
        url = article["url"]

        # Create summary
        summary = summarize_article_korean(title, text)

        # Add metadata
        summary = f"---\ntitle: {title}\nurl: {url}\ndate: {TODAY}\n---\n\n" + summary

        # Save to file
        slug = sanitize_slug(title)
        # Handle collisions
        filepath = f"{summary_dir}/{slug}.md"
        counter = 1
        while os.path.exists(filepath):
            filepath = f"{summary_dir}/{slug}_{counter}.md"
            counter += 1

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(summary)

        written_count += 1
        print(f"[SUMMARY] {idx+1}/{len(articles)}: {filepath}")

    print(f"[STAGE] summary_written={written_count}")

    # Verify count
    if written_count != len(articles):
        print(f"[WARN] Written count mismatch: {written_count} != {len(articles)}")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
