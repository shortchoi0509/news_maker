# Daily News Maker

매일경제 기사를 자동으로 스크랩하고 Claude 가 한국어 데일리 브리프를
생성해 Gmail 로 발송하는 GitHub Actions 파이프라인.

## Pipeline (`.github/workflows/news_daily.yml`)

매일 KST 00:30 (UTC 15:30) 자동 실행, 또는 Actions 탭 → Run workflow 로 수동 실행.

1. `_run_scrape.py` — 매일경제 기사 목록을 병렬 스크랩하여 `out/<YYYY-MM-DD>/scraped.json` 생성
2. `anthropics/claude-code-action` — `scraped.json` 의 모든 기사를 통합 컨텍스트로 읽고
   두 개의 마크다운 작성:
   - `SUMMARY_KO/daily_brief_<YYYY-MM-DD>.md` — 전체 기사 아카이브
   - `SUMMARY_KO/email_brief_<YYYY-MM-DD>.md` — 핵심 10~15개만 선별한 발송용
   - 둘 다 최상단 `## 오늘의 한눈에 보기` (주제별 단락 종합 개관) +
     각 기사별 `## NN. 제목` + `### 요약` / `### 전망` / `### 시사점`
3. `generate_html.py` — `out/<date>/` 의 모든 마크다운을 에디토리얼 스타일 HTML 로 변환
4. `_send_email.py` — `email_brief` HTML 을 Gmail SMTP 로 발송 (없으면 `daily_brief` 로 폴백,
   인라인 본문 + 첨부)

## Required GitHub Secrets

Settings → Secrets and variables → Actions:

| Secret | 설명 |
| --- | --- |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code Action 인증 토큰 |
| `GMAIL_USERNAME` | 발송 Gmail 주소 (예: `me@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (2단계 인증 → 앱 비밀번호에서 발급한 16자) |
| `MAIL_TO` | 수신자 이메일. 여러 명이면 콤마로 구분 (`a@x.com,b@y.com`) |

## Local testing

발송만 단독으로 테스트:

```bash
TODAY=2026-05-07 \
GMAIL_USERNAME=me@gmail.com \
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx \
MAIL_TO=you@example.com \
python _send_email.py
```

또는 Actions 탭의 `Email Test (manual)` 워크플로우로 수동 발송 검증 가능.
