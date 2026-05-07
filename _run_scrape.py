#!/usr/bin/env python3
"""
Comprehensive news scraper for mk.co.kr
Extracts URLs, then fetches article content (title, text, url) for each.
Saves to /tmp/scraped_<DATE>.json
"""
import os
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from mk_scrape import scrape as scrape_links
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")
OUTPUT_FILE = f"/tmp/scraped_{TODAY}.json"
MAX_WORKERS = int(os.getenv("SCRAPE_WORKERS", "8"))

def extract_article(url, timeout=15):
    """
    Extract article title and text from mk.co.kr URL using BeautifulSoup.
    Returns dict with url, title, text, or None on failure.
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, 'lxml')

        # Extract title - look for og:title or h1
        title = ""
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            title = og_title.get("content")
        if not title:
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text().strip()

        # Extract article body text
        text_parts = []
        article_div = soup.find("div", class_=lambda x: x and "article-body" in x)
        if article_div:
            for p in article_div.find_all("p"):
                p_text = p.get_text().strip()
                if p_text and len(p_text) > 5:
                    text_parts.append(p_text)

        # Fallback: look for any content divs
        if not text_parts:
            for div in soup.find_all("div", class_=lambda x: x and ("content" in x or "body" in x)):
                for p in div.find_all("p"):
                    p_text = p.get_text().strip()
                    if p_text and len(p_text) > 5:
                        text_parts.append(p_text)

        text = "\n".join(text_parts[:20])  # Limit to first 20 paragraphs

        if not title or len(text) < 50:
            print(f"  [WARN] Incomplete content from {url}")
            return None

        return {
            "url": url,
            "title": title,
            "text": text
        }
    except Exception as e:
        print(f"  [ERROR] Failed to extract {url}: {e}")
        return None

def main():
    print(f"[STAGE] today={TODAY}")
    print(f"[STAGE] Starting comprehensive scrape...")

    # Step 1: Get all article links
    print("[STAGE] Fetching article links from mk.co.kr...")
    link_items = scrape_links()
    print(f"[STAGE] Found {len(link_items)} links")

    if not link_items:
        print("[STAGE] No links found, aborting")
        sys.exit(1)

    # Step 2: Extract article content in parallel
    articles = []
    total = len(link_items)
    print(f"[STAGE] Extracting content from {total} articles (workers={MAX_WORKERS})...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        future_to_url = {ex.submit(extract_article, item["url"]): item["url"] for item in link_items}
        done = 0
        for fut in as_completed(future_to_url):
            done += 1
            url = future_to_url[fut]
            try:
                article_data = fut.result()
            except Exception as e:
                print(f"  [{done}/{total}] [ERROR] {url}: {e}")
                continue
            if article_data:
                articles.append(article_data)
                print(f"  [{done}/{total}] OK  {url}")
            else:
                print(f"  [{done}/{total}] SKIP {url}")

    print(f"[STAGE] scraped_count={len(articles)}")
    if len(articles) > 0:
        print(f"[STAGE] sample_titles={json.dumps([a['title'][:60] for a in articles[:3]])}")

    # Step 3: Save to JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"[STAGE] Saved {len(articles)} articles to {OUTPUT_FILE}")

    if len(articles) < 5:
        print(f"[STAGE] WARNING low_count: expected >=20, got {len(articles)}")

if __name__ == "__main__":
    main()
