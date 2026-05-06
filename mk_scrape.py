# mk_scrape.py
import re, json, os
from collections import OrderedDict
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone, timedelta
import requests
from bs4 import BeautifulSoup

URL = "https://www.mk.co.kr/today-paper/"
TARGET = {"world","economy","business","realestate","it","stock","society","politics","culture","columnists","journalist","contributors","editorial"}
#TARGET = {"editorial"}
def fetch(sess, url):
    # Add more realistic User-Agent headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.google.com/",
    }
    try:
        r = sess.get(url, timeout=20, headers=headers)
        r.raise_for_status()
        return r.text
    except requests.exceptions.HTTPError as e:
        # Retry with different headers on 403
        if e.response.status_code == 403:
            import time
            time.sleep(2)
            headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
            r = sess.get(url, timeout=20, headers=headers)
            r.raise_for_status()
            return r.text
        raise

def norm(href, base=URL):
    if not href:
        return ""
    href = href.strip()
    if href.startswith("//"):
        href = "https:" + href
    if href.startswith("/"):
        href = urljoin(base, href)
    return href

def scrape():
    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9",
        "Referer": "https://www.google.com/",
    })
    root = fetch(sess, URL)
    soup = BeautifulSoup(root, "lxml")
    pat = re.compile(r"^https://www\.mk\.co\.kr/news/([a-z0-9\-]+)/(\d+)/?$", re.I)

    sections = OrderedDict()
    seen = set()

    for a in soup.find_all("a", href=True):
        u = norm(a["href"])
        m = pat.match(u)
        if not m:
            continue
        sec = m.group(1).lower()
        if sec not in TARGET:
            continue
        pu = urlparse(u)
        clean = f"{pu.scheme}://{pu.netloc}{pu.path}"
        if clean in seen:
            continue
        seen.add(clean)
        sections.setdefault(sec, []).append(clean)

    data = []
    for sec, urls in sections.items():
        for u in urls:
            data.append({"section": sec, "url": u})

    # 날짜별 디렉토리 저장
    kst = timezone(timedelta(hours=9))
    dstr = datetime.now(kst).strftime("%Y-%m-%d")
    out_dir = os.path.join("out", dstr)
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "mk_links.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[SCRAPER] {len(data)} links saved to {json_path}")
    return data

if __name__ == "__main__":
    scrape()
