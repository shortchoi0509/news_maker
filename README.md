## PodCast Maker

뉴스 데이터를 기반 pod cast 자동 생성 툴

### 자동화 pipeline

* news_maker
  * ex) `python -m news_maker.news_parse_and_archive --file-name soccer_news --urls {url1},{url2},{url3},{url4} --input-language ko --output-language ENGLISH --llm-model gpt-4o --output-crolling-dir crolling_results --output-llm-podcast-dir llm_podcast_results`
    * `--output-crolling-dir` : 기사 크롤링 결과 저장 디렉토리
    * `--output-llm-podcast-dir` : llm api를 통해 생성된 pod cast 결과 저장 디렉토리
    * `--output-llm-summary-dir` : llm api를 통해 생성된 결과 저장 디렉토리
    * 위 세 argument는 **optional** 이므로 주어지지 않은 directory에 대해서는 결과를 저장하지 않음
  * news url을 던져주면 webcrolling을 통해 기사 제목, contents 추출
    * newspaper3k 라이브러리로 실패나는 url은 제외하고 추출
  * llm api로 정제 거친후 각 기사별로 (제목, 내용, 키워드) 추출 후 하나의 txt 파일로 저장
    * 위 예시의 경우 txt_files/soccer_news.txt 파일로 저장
  * 지원 llm model
    * chatGPT, deepseek

### ToDo

현재는 Google NotebookLM의 podcast 생성 툴을 이용하고 있는데.. 이 단계까지 자동화 가능하면 편할 듯

### Daily News Pipeline (GitHub Actions)

`.github/workflows/news_daily.yml` 가 매일 KST 00:30 에 실행되어
매일경제 기사를 스크랩하고 Claude Code Action 으로 한국어 데일리 브리프를
`out/<YYYY-MM-DD>/` 에 생성한 뒤, 결과 HTML 을 Gmail 로 발송한다.

발송에 필요한 GitHub Secrets (Settings → Secrets and variables → Actions):

| Secret | 설명 |
| --- | --- |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude Code Action 인증 토큰 |
| `GMAIL_USERNAME` | 발송 Gmail 주소 (예: `me@gmail.com`) |
| `GMAIL_APP_PASSWORD` | Gmail 앱 비밀번호 (2단계 인증 → 앱 비밀번호에서 발급한 16자) |
| `MAIL_TO` | 수신자 이메일. 여러 명이면 콤마로 구분 (`a@x.com,b@y.com`) |

로컬에서 발송을 테스트하려면:

```bash
TODAY=2026-05-07 \
GMAIL_USERNAME=me@gmail.com \
GMAIL_APP_PASSWORD=xxxxxxxxxxxxxxxx \
MAIL_TO=you@example.com \
python _send_email.py
```
