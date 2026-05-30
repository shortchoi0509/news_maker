#!/usr/bin/env python3
"""
Comprehensive news scraper for mk.co.kr
Extracts URLs, then fetches article content (title, text, url) for each.
Saves to /tmp/scraped_<DATE>.json
"""
import os
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from mk_scrape import scrape as scrape_links
import requests
from bs4 import BeautifulSoup

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")
OUTPUT_FILE = f"/tmp/scraped_{TODAY}.json"
MAX_WORKERS = int(os.getenv("SCRAPE_WORKERS", "4"))

def extract_article(url, timeout=20, retry=3):
    """
    Extract article title and text from mk.co.kr URL using BeautifulSoup.
    Returns dict with url, title, text, or None on failure.
    """
    headers_list = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]

    for attempt in range(retry):
        try:
            headers = {
                "User-Agent": headers_list[attempt % len(headers_list)],
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
            if attempt > 0:
                time.sleep(1 + attempt)

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
                return None

            return {
                "url": url,
                "title": title,
                "text": text
            }
        except Exception as e:
            if attempt == retry - 1:
                return None
            continue

def main():
    print(f"[STAGE] today={TODAY}")
    print(f"[STAGE] Starting comprehensive scrape...")

    # Step 1: Get all article links
    print("[STAGE] Fetching article links from mk.co.kr...")
    try:
        link_items = scrape_links()
    except Exception as e:
        print(f"[STAGE] WARNING: Could not fetch fresh links: {e}")
        print(f"[STAGE] Will use yesterday's data as template...")
        # Load yesterday's data as fallback
        yesterday = (datetime.now(KST) - timedelta(days=1)).strftime("%Y-%m-%d")
        try:
            with open(f"out/{yesterday}/scraped.json", 'r', encoding='utf-8') as f:
                link_items = json.load(f)
                print(f"[STAGE] Loaded {len(link_items)} items from yesterday")
                # Save to today's location and exit gracefully
                os.makedirs(f"out/{TODAY}/SUMMARY_KO", exist_ok=True)
                with open(f"/tmp/scraped_{TODAY}.json", 'w', encoding='utf-8') as out:
                    json.dump(link_items, out, ensure_ascii=False, indent=2)
                print(f"[STAGE] scraped_count={len(link_items)}")
                print(f"[STAGE] Saved to {OUTPUT_FILE}")
                return
        except:
            print("[STAGE] FATAL: No fallback data available")
            sys.exit(1)

    print(f"[STAGE] Found {len(link_items)} links")

    if not link_items:
        print("[STAGE] No links found, aborting")
        sys.exit(1)

    # Step 2: Extract article content in parallel
    articles = []
    total = len(link_items)
    print(f"[STAGE] Extracting content from {total} articles (workers={MAX_WORKERS})...")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        future_to_url = {ex.submit(extract_article, item["url"] if isinstance(item, dict) else item): item for item in link_items}
        done = 0
        for fut in as_completed(future_to_url):
            done += 1
            item = future_to_url[fut]
            url = item["url"] if isinstance(item, dict) else item
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
