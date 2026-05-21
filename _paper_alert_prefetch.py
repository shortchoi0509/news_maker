"""Prefetch step for the Hydrogeochem Paper Alert routine.

Fetches the 7 ScienceDirect RSS feeds, enriches each NEW paper's abstract
(Elsevier API -> OpenAlex -> Crossref), and writes
paper_alert/inbox/inbox_<KST-DATE>.json for the scoring routine to consume.

Only papers whose guid is not already in paper_alert/seen.csv are enriched,
to keep API usage low.

Environment variables:
  ELSEVIER   Elsevier API key (optional; falls back to OpenAlex/Crossref)

Stdlib only.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html import unescape
from pathlib import Path

# ScienceDirect (Elsevier) journals - fetched via RSS.
FEEDS = {
    "Applied Geochemistry": "https://rss.sciencedirect.com/publication/science/08832927",
    "Chemical Geology": "https://rss.sciencedirect.com/publication/science/00092541",
    "Journal of Hydrology": "https://rss.sciencedirect.com/publication/science/00221694",
    "Geothermics": "https://rss.sciencedirect.com/publication/science/03756505",
    "Science of the Total Environment": "https://rss.sciencedirect.com/publication/science/00489697",
    "Geochimica et Cosmochimica Acta": "https://rss.sciencedirect.com/publication/science/00167037",
    "Journal of Hazardous Materials": "https://rss.sciencedirect.com/publication/science/03043894",
    "Journal of Contaminant Hydrology": "https://rss.sciencedirect.com/publication/science/01697722",
    "Journal of Environmental Radioactivity": "https://rss.sciencedirect.com/publication/science/0265931X",
    "Journal of Hydrology: Regional Studies": "https://rss.sciencedirect.com/publication/science/22145818",
}

# Non-ScienceDirect journals - fetched via the Crossref journal works API by ISSN.
CROSSREF_JOURNALS = {
    "Hydrogeology Journal": "1431-2174",
}

MAILTO = "shortchoi0509@gmail.com"
UA = f"HydrogeochemPaperAlert/1.0 (mailto:{MAILTO})"
SEEN_CSV = Path("paper_alert/seen.csv")
OUT_DIR = Path("paper_alert/inbox")

DC = "{http://purl.org/dc/elements/1.1/}"
PRISM = "{http://prism.prismstandard.org/namespaces/basic/2.0/}"
CONTENT = "{http://purl.org/rss/1.0/modules/content/}"

TAG_RE = re.compile(r"<[^>]+>")
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s\"'<>]+")
PII_RE = re.compile(r"/pii/([A-Z0-9]+)", re.I)
PUBDATE_RE = re.compile(r"Publication date:\s*(.+?)\s*(?:Source:|$)", re.I)

elsevier_denied = False


def kst_today() -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%Y-%m-%d")


def strip_html(text: str) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", unescape(TAG_RE.sub(" ", text))).strip()


def http_get(url: str, headers: dict | None = None, timeout: int = 25):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def load_seen() -> set[str]:
    seen: set[str] = set()
    if not SEEN_CSV.is_file():
        return seen
    with SEEN_CSV.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            guid = (row.get("guid") or "").strip()
            if guid:
                seen.add(guid)
    return seen


def parse_feed(journal: str, xml_bytes: bytes) -> list[dict]:
    items = []
    root = ET.fromstring(xml_bytes)
    for item in root.iter("item"):
        title = strip_html(item.findtext("title") or "")
        link = (item.findtext("link") or "").strip()
        guid = (item.findtext("guid") or link).strip()
        pub = (item.findtext("pubDate") or item.findtext(DC + "date") or "").strip()
        desc = strip_html(
            item.findtext("description")
            or item.findtext(CONTENT + "encoded")
            or ""
        )
        if not pub:
            # ScienceDirect leaves <pubDate> empty; the date sits in the
            # description as "Publication date: <date> Source: ...".
            m = PUBDATE_RE.search(desc)
            if m:
                pub = m.group(1).strip()
        doi = ""
        for cand in (
            item.findtext(PRISM + "doi"),
            item.findtext(DC + "identifier"),
        ):
            if cand:
                m = DOI_RE.search(cand)
                if m:
                    doi = m.group(0).rstrip(".")
                    break
        if not doi:
            m = DOI_RE.search(f"{desc} {guid} {link}")
            if m:
                doi = m.group(0).rstrip(".")
        pii = ""
        m = PII_RE.search(link)
        if m:
            pii = m.group(1).upper()
        if title and guid:
            items.append({
                "guid": guid, "title": title, "link": link, "journal": journal,
                "pubDate": pub, "description": desc, "doi": doi, "pii": pii,
            })
    return items


def elsevier_abstract(doi: str, pii: str, key: str) -> tuple[str, str]:
    global elsevier_denied
    if not key:
        return "", ""
    headers = {"X-ELS-APIKey": key, "Accept": "application/json", "User-Agent": UA}
    targets = []
    if doi:
        targets.append(
            f"https://api.elsevier.com/content/article/doi/{urllib.parse.quote(doi)}"
            "?httpAccept=application/json"
        )
    if pii:
        targets.append(
            f"https://api.elsevier.com/content/article/pii/{pii}"
            "?httpAccept=application/json"
        )
    for url in targets:
        try:
            data = json.loads(http_get(url, headers=headers))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                elsevier_denied = True
            continue
        except Exception:
            continue
        finally:
            time.sleep(0.2)
        resp = (
            data.get("full-text-retrieval-response")
            or data.get("abstracts-retrieval-response")
            or {}
        )
        core = resp.get("coredata", {}) if isinstance(resp, dict) else {}
        desc = core.get("dc:description")
        if isinstance(desc, dict):
            desc = desc.get("#text", "")
        text = strip_html(str(desc or ""))
        if text:
            return text, "elsevier"
    return "", ""


def openalex_abstract(doi: str, title: str) -> str:
    try:
        if doi:
            url = (
                f"https://api.openalex.org/works/doi:{urllib.parse.quote(doi)}"
                f"?mailto={MAILTO}"
            )
            data = json.loads(http_get(url))
        else:
            url = (
                "https://api.openalex.org/works?per_page=1&mailto="
                f"{MAILTO}&filter=title.search:{urllib.parse.quote(title)}"
            )
            results = json.loads(http_get(url)).get("results", [])
            data = results[0] if results else None
        if not data:
            return ""
        inv = data.get("abstract_inverted_index")
        if not inv:
            return ""
        positions: dict[int, str] = {}
        for word, idxs in inv.items():
            for i in idxs:
                positions[i] = word
        return " ".join(positions[i] for i in sorted(positions)).strip()
    except Exception:
        return ""


def crossref_abstract(doi: str, title: str) -> str:
    headers = {"User-Agent": UA}
    try:
        if doi:
            url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
            item = json.loads(http_get(url, headers=headers)).get("message", {})
        else:
            url = (
                "https://api.crossref.org/works?rows=1&query.bibliographic="
                f"{urllib.parse.quote(title)}"
            )
            items = json.loads(http_get(url, headers=headers)).get(
                "message", {}
            ).get("items", [])
            item = items[0] if items else {}
        return strip_html(item.get("abstract", ""))
    except Exception:
        return ""


def fetch_crossref_journal(journal: str, issn: str) -> list[dict]:
    url = (
        f"https://api.crossref.org/journals/{issn}/works"
        f"?sort=published&order=desc&rows=60&mailto={MAILTO}"
        "&select=DOI,title,issued,URL"
    )
    data = json.loads(http_get(url, headers={"User-Agent": UA}))
    items = []
    for work in data.get("message", {}).get("items", []):
        doi = (work.get("DOI") or "").strip()
        if not doi:
            continue
        titles = work.get("title") or []
        title = next((strip_html(t) for t in titles if t and t.strip()), "")
        if not title:
            continue
        parts = ((work.get("issued") or {}).get("date-parts") or [[]])[0]
        pub = "-".join(f"{p:02d}" if i else str(p) for i, p in enumerate(parts))
        items.append({
            "guid": f"https://doi.org/{doi}",
            "title": title,
            "link": work.get("URL") or f"https://doi.org/{doi}",
            "journal": journal,
            "pubDate": pub,
            "description": "",
            "doi": doi,
            "pii": "",
        })
    return items


def enrich(item: dict, key: str) -> tuple[str, str]:
    doi, pii = item["doi"], item["pii"]
    # The Elsevier API only serves Elsevier content; skip it for other publishers.
    if pii or doi.startswith("10.1016/"):
        text, src = elsevier_abstract(doi, pii, key)
        if text:
            return text, src
    text = openalex_abstract(doi, item["title"])
    if text:
        return text, "openalex"
    text = crossref_abstract(doi, item["title"])
    if text:
        return text, "crossref"
    return "", "none"


def main() -> int:
    key = os.environ.get("ELSEVIER", "").strip()
    seen = load_seen()
    print(f"[PREFETCH] seen_guids={len(seen)} elsevier_key={'yes' if key else 'no'}")

    feeds_ok = 0
    raw: list[dict] = []
    for journal, url in FEEDS.items():
        try:
            raw.extend(parse_feed(journal, http_get(url)))
            feeds_ok += 1
        except Exception as exc:
            print(f"::warning::Feed failed ({journal}): {exc}")
    for journal, issn in CROSSREF_JOURNALS.items():
        try:
            raw.extend(fetch_crossref_journal(journal, issn))
            feeds_ok += 1
        except Exception as exc:
            print(f"::warning::Crossref journal failed ({journal}): {exc}")

    if feeds_ok == 0:
        print("::error::All RSS feeds failed; not writing inbox (routine will fall back)")
        return 1

    new: list[dict] = []
    seen_run: set[str] = set()
    for item in raw:
        guid = item["guid"]
        if guid in seen or guid in seen_run:
            continue
        seen_run.add(guid)
        new.append(item)

    total_sources = len(FEEDS) + len(CROSSREF_JOURNALS)
    print(f"[PREFETCH] feeds_ok={feeds_ok}/{total_sources} raw={len(raw)} new={len(new)}")

    counts = {"elsevier": 0, "openalex": 0, "crossref": 0, "none": 0}
    out = []
    for idx, item in enumerate(new, 1):
        abstract, source = enrich(item, key)
        counts[source] = counts.get(source, 0) + 1
        out.append({
            "guid": item["guid"], "title": item["title"], "link": item["link"],
            "journal": item["journal"], "pubDate": item["pubDate"],
            "description": item["description"], "abstract": abstract,
            "abstract_source": source,
        })
        if idx % 25 == 0:
            print(f"[PREFETCH] enriched {idx}/{len(new)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"inbox_{kst_today()}.json"
    out_path.write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    if elsevier_denied:
        print(
            "::warning::Elsevier API returned 401/403 (key not valid from this "
            "runner IP) - used OpenAlex/Crossref fallback instead"
        )
    print(
        f"[PREFETCH] wrote {out_path} items={len(out)} "
        f"abstracts: elsevier={counts['elsevier']} openalex={counts['openalex']} "
        f"crossref={counts['crossref']} none={counts['none']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
