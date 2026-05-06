# auto_run.py (토글 추가 예시)
import os
from datetime import datetime, timezone, timedelta
from mk_scrape import scrape
from news_maker.news_parse_and_archive import run

KST = timezone(timedelta(hours=9))

def _truthy(v: str | None, default=True) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1","true","yes","y","on"}

def main():
    items = scrape()
    if not items:
        print("[WARN] No links scraped. Exit.")
        return
    urls_str = ",".join([it["url"] for it in items])

    today_str = datetime.now(KST).strftime("%Y-%m-%d")
    base_dir = os.path.join("out", today_str)
    summary_dir = os.path.join(base_dir, "SUMMARY_KO")
    podcast_dir = os.path.join(base_dir, "PODCAST_EN")
    os.makedirs(summary_dir, exist_ok=True)
    os.makedirs(podcast_dir, exist_ok=True)

    DO_PODCAST_EN = _truthy(os.getenv("DO_PODCAST_EN"), default=False)  # ← 기본 ON

    run(
        filename=today_str,
        urls=urls_str,
        input_lang="ko",
        ouput_lang="KOREAN",
        llm_model="gpt-5-nano-2025-08-07",
        croll_ouput_dir=None,
        llm_podcast_output_dir=(podcast_dir if DO_PODCAST_EN else None),  # ← 토글
        llm_summary_output_dir=summary_dir,
        use_chained_podcast=DO_PODCAST_EN  # 팟캐스트가 켜진 경우에만 체인 사용
    )

if __name__ == "__main__":
    main()
