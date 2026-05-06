# news_maker/news_parse_and_archive.py  (CHAIN-READY)
import os
import argparse
from newspaper import Article
from llm_models_api.chat_gpt.chatgpt_api import get_response_from_chatgpt
from llm_models_api.deepseek.deepseek_api import get_response_from_deepseek

# ----- LLM system roles -----
def llm_system_role_podcast():
    return (
        "You transform raw Korean news content into a clean, podcast-ready English script.\n\n"

        "OUTPUT FORMAT — exactly these 3 fields, nothing else (no preamble, no postamble):\n"
        "TITLE:\n"
        "(A concise, descriptive English podcast title — under 15 words)\n\n"
        "CONTENTS:\n"
        "(A well-structured English podcast script following the rules below)\n\n"
        "KEYWORDS:\n"
        "(5-8 most important keywords/named entities, comma-separated, in English, on ONE line)\n\n"

        "CONTENTS STRUCTURE — follow this 3-part flow:\n"
        "1. HOOK (1-2 sentences): A hook that makes a listener care. Start directly with the hook — no 'Welcome back, listeners!' filler.\n"
        "2. BODY (2-4 short paragraphs): The key facts — who, what, when, where, so-what. Natural spoken English, short sentences, NO bullet points.\n"
        "3. TAKEAWAY (1 sentence): One-line implication / why-it-matters.\n\n"

        "STYLE RULES:\n"
        "- Spoken English, not written. Read-aloud friendly.\n"
        "- NO bullet points, NO markdown headers inside CONTENTS — just flowing paragraphs.\n"
        "- Translate Korean proper nouns accurately (삼성전자 → Samsung Electronics, 코스피 → KOSPI, 금융위원회 → Financial Services Commission, etc.).\n"
        "- Keep numbers, company names, and dates precise — do NOT round or paraphrase away.\n"
        "- For opinion pieces (사설/칼럼/기고), clearly label it as the author's view.\n"
        "- No speculation beyond the source. If unclear, omit rather than invent.\n\n"

        "NOISE REMOVAL — remove completely:\n"
        "- Reporter names, emails, phone numbers\n"
        "- Copyright notices, subscription prompts, ad banners\n"
        "- Menu / navigation / related-article lists\n"
        "- Image captions ('사진=', '출처=', 'ⓒ...'), figure descriptions\n"
        "- HTML / CSS / JS fragments, broken characters\n\n"

        "Output the 3 fields only. No extra commentary."
    )


def llm_system_role_summary():
    return (
        "You are an expert Korean news analyst. Transform raw web-crawled news text "
        "into a clean, accurate, beginner-friendly Korean summary.\n\n"

        "OUTPUT FORMAT — STRICT (only these 2 sections, no preamble, no postamble):\n"
        "### TITLE:\n"
        "한국어로 간결하고 설명력 있는 제목 한 줄\n\n"
        "### CONTENTS:\n"
        "아이콘으로 시작하는 줄들 — 아래 스키마를 따름:\n"
        "  ✅ 기사 전체를 한 줄로 압축한 핵심 요약\n"
        "  ✦ 주요 사실 (2~4줄; 내용이 빈약하면 2줄만 써도 됨, 억지로 3줄 채우지 말 것)\n"
        "  ➕ (선택) 추가 맥락·수치·배경 (0~3줄)\n"
        "  🔎 이 뉴스의 의미/영향 1줄\n"
        "  🧾 (선택) 용어 1개(쉬운 풀이)\n\n"

        "ARTICLE TYPE ADAPTATION — 기사 성격에 맞춰 ✦ 내용을 조정:\n"
        "- 속보/리포트: ✦는 '주요 사실 (누가/무엇/언제/결과)'.\n"
        "- 사설/칼럼/기고(editorial/columnists/contributors): ✦는 '필자 주장의 근거/논리'. "
        "  ✅는 '필자의 핵심 주장'으로 쓰고, '필자는 ~라고 주장한다' 투로 기술해 사실 보도와 구분할 것.\n"
        "- 기자수첩(journalist): ✦는 '관찰된 현상 + 기자의 해석'. ✅는 '전달하려는 핵심 메시지'.\n"
        "- 짧은 공지·인사 발령·단순 속보는 ✦ 1~2줄 + 🔎 만 있어도 됨.\n\n"

        "CRITICAL FORMATTING RULES (violation = invalid output):\n"
        "1. 앵글 브래킷 `<...>` 플레이스홀더를 절대 출력하지 말 것.\n"
        "   BAD  : `✦ <주요 내용 1> 삼성전자가...`\n"
        "   GOOD : `✦ 삼성전자가...`\n"
        "2. `주요 내용 1:`, `주요 사실 2:`, `용어 1개 설명:` 같은 레이블 접두사 금지.\n"
        "   아이콘 바로 뒤에 실제 내용이 이어져야 함.\n"
        "3. 각 줄은 '아이콘 + 공백 + 내용' 형태. 들여쓰기·중첩·줄바꿈 금지 (한 bullet = 한 줄).\n"
        "4. ✅ 와 🔎 는 정확히 각 1줄. 여러 번 쓰지 말 것.\n"
        "5. 🧾 포맷은 반드시 `용어(쉬운 풀이)` — 콜론(:) 사용 금지.\n"
        "   GOOD : `🧾 레버리지 ETF(기초자산 수익률의 2배를 추종하는 파생 ETF)`\n"
        "   BAD  : `🧾 레버리지 ETF: 기초자산의 2배를 추종하는 ETF`\n"
        "   BAD  : `🧾 용어 1개 설명: 레버리지 ETF — ...`\n"
        "6. 어려운 용어가 없으면 🧾는 생략. 억지로 만들지 말 것.\n"
        "7. ✦는 최소 2줄, 최대 4줄.\n\n"

        "CONTENT QUALITY RULES:\n"
        "- 원문에 없는 내용 추측 금지. 불명확하면 해당 줄을 아예 빼라.\n"
        "- 숫자·고유명사·날짜·정책명·인물명은 원문에서 정확히 인용.\n"
        "- '~할 것으로 예상된다' 같은 추측성 표현은 원문이 명시한 경우만.\n"
        "- 모든 bullet은 한국어 종결어미(~다/~ㅁ/~음)로 끝낼 것.\n"
        "- 중복 표현·미사여구·'~를 위해 노력한다' 같은 빈 문구 제거.\n\n"

        "NOISE REMOVAL (완전히 제거):\n"
        "- 기자 이름·이메일·전화번호·SNS 계정\n"
        "- 저작권·무단전재·재배포 문구\n"
        "- 광고·구독·앱 설치·로그인 배너\n"
        "- 메뉴·네비·관련기사 리스트·태그 나열\n"
        "- 사진 캡션(사진=, 출처=, ⓒ...), figure 설명\n"
        "- HTML/CSS/JS 잔재, 깨진 문자, 중복 단락\n\n"

        "SELF-CHECK before output:\n"
        "□ `<` 문자가 bullet 내용에 남아있지 않은가?\n"
        "□ 모든 bullet이 아이콘으로 시작하는가?\n"
        "□ ✅와 🔎가 정확히 1줄씩 있는가?\n"
        "□ 🧾 형식이 `용어(풀이)`인가? (없어도 OK)\n"
        "□ `주요 내용 N`, `용어 1개` 같은 레이블이 내용에 섞이지 않았는가?\n\n"

        "체크 실패 시 다시 작성하라. 추가 멘트·자기 평가 없이 결과만 출력하라."
    )


# ----- Helpers -----
def make_article(url, lang):
    article = Article(url, language=lang)
    article.download()
    article.parse()
    return article

def make_croll_result(article, url):
    # RAW 덤프도 보기 좋게: 제목 H2 + 원문 링크 + 본문
    return f"""## {article.title}
[원문 보기]({url})

{article.text}
"""

def user_prompt(contents):
    return f"""
raw web ARTICLE is here: 

{contents}
""".strip()

def translate_prompt(lang):
    return f"""
TRANSLATE into {lang}
""".strip()

def podcast_from_korean_summary_prompt(ko_summary_text):
    # 요약을 입력으로 팟캐스트 생성 (체인 모드)
    return (
        "You are given a Korean summary of a news article below.\n"
        "Write an English podcast-style script using ONLY the information present in the summary. "
        "Remove any noise and do not add external facts.\n\n"
        "KOREAN SUMMARY START\n"
        f"{ko_summary_text}\n"
        "KOREAN SUMMARY END"
    )

def write_result(output_dir, filename, result_list):
    os.makedirs(output_dir, exist_ok=True)
    out_path = f"{output_dir}/{filename}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(result_list)
    print(f"SUCCESS to write at {out_path}")

# ----- Main pipeline -----
def run(
    filename,
    urls,
    input_lang,
    ouput_lang,
    llm_model,
    croll_ouput_dir,
    llm_podcast_output_dir,
    llm_summary_output_dir,
    use_chained_podcast: bool = False,   # ✅ 체인 옵션 추가 (기본 False)
):
    # 입력 URL 정리
    url_list = [u.strip() for u in urls.split(",") if u.strip()]
    valid_url_list = []

    for url in url_list:
        try:
            cur_article = make_article(url, input_lang)
            len_cur_article = len(cur_article.text or "")
            if len_cur_article < 300:
                print(f"{url} crolling contents is too small: {len_cur_article}, skip this news")
                continue
            valid_url_list.append(url)
        except Exception as e:
            print(f"{url} crolling failed, skip this news", e)

    print("\ninput url count: ", len(url_list))
    print("valid url count for crolling: ", len(valid_url_list))
    print("")

    llm_podcast_role = llm_system_role_podcast()
    llm_summary_role = llm_system_role_summary()

    _save_podcast_result = llm_podcast_output_dir is not None
    _save_summary_result = llm_summary_output_dir is not None

    print("start to clean and extract (news title, news contents, news main keywords)...", llm_model)
    print("")
    if _save_podcast_result:
        print("LLM PODCAST ROLE SETTING:")
        print(llm_podcast_role)
        print("")
    if _save_summary_result:
        print("LLM SUMMARY ROLE SETTING:")
        print(llm_summary_role)
        print("")

    croll_result_list = []
    llm_podcast_result_list = []
    llm_summary_result_list = []
    success_count = 0

    # 번역 필요 여부
    _need_translate = False
    if input_lang == "ko":
        if ouput_lang != "KOREAN":
            _need_translate = True
    elif input_lang == "en":
        if ouput_lang != "ENGLISH":
            _need_translate = True
    else:
        raise ValueError(f"not supported input lang: {input_lang}")

    SEP = "\n\n---\n\n"  # 기사 구분선

    for idx, url in enumerate(valid_url_list):
        # 1) 기사 파싱
        cur_article = make_article(url, input_lang)

        # 2) RAW 결과(옵션)
        croll_result = make_croll_result(cur_article, url)
        croll_result_list.append(croll_result)

        # ===== A) SUMMARY: 원문 기반 한국어 요약 =====
        summary_resp = None
        if _save_summary_result:
            cur_prompt_summary = [user_prompt(croll_result)]
            if _need_translate:
                cur_prompt_summary.append(translate_prompt(ouput_lang))
            try:
                if llm_model.startswith("gpt"):
                    summary_resp = get_response_from_chatgpt(llm_summary_role, cur_prompt_summary, model=llm_model)
                elif llm_model.startswith("deepseek"):
                    summary_resp = get_response_from_deepseek(llm_summary_role, cur_prompt_summary, model=llm_model)
                else:
                    raise ValueError(f"not supported llm model: {llm_model}")

                llm_summary_result_list.append(
                    f"## {cur_article.title}\n[원문 보기]({url})\n\n{summary_resp}"
                )
            except Exception as e:
                print(f"summary failed for {url}", e)

        # ===== B) PODCAST: 체인 모드면 '요약'을 입력으로 사용, 아니면 원문 사용 =====
        if _save_podcast_result:
            try:
                if use_chained_podcast and summary_resp:
                    # 요약이 너무 짧으면 원문으로 폴백
                    podcast_user = (
                        user_prompt(croll_result) if len(summary_resp) < 200
                        else podcast_from_korean_summary_prompt(summary_resp)
                    )
                else:
                    # 기존 방식: 원문 기반
                    podcast_user = user_prompt(croll_result)

                cur_prompt_podcast = [podcast_user]

                if llm_model.startswith("gpt"):
                    podcast_resp = get_response_from_chatgpt(llm_podcast_role, cur_prompt_podcast, model=llm_model)
                elif llm_model.startswith("deepseek"):
                    podcast_resp = get_response_from_deepseek(llm_podcast_role, cur_prompt_podcast, model=llm_model)
                else:
                    raise ValueError(f"not supported llm model: {llm_model}")

                llm_podcast_result_list.append(
                    f"## {cur_article.title}\n[원문 보기]({url})\n\n{podcast_resp}"
                )
            except Exception as e:
                print(f"podcast failed for {url}", e)

        # 5) 기사 간 구분선
        if idx != len(valid_url_list) - 1:
            croll_result_list.append(SEP)
            if _save_podcast_result:
                llm_podcast_result_list.append(SEP)
            if _save_summary_result:
                llm_summary_result_list.append(SEP)

        success_count += 1

    print("SUCCESS to extract (news title, news contents, news main keywords) from LLM!: ", success_count)

    # 6) 저장
    if croll_ouput_dir is not None and len(croll_result_list) != 0:
        write_result(croll_ouput_dir, filename, croll_result_list)

    if _save_podcast_result and len(llm_podcast_result_list) != 0:
        write_result(llm_podcast_output_dir, filename, llm_podcast_result_list)

    if _save_summary_result and len(llm_summary_result_list) != 0:
        write_result(llm_summary_output_dir, filename, llm_summary_result_list)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file-name", type=str, help="file name for .md")
    parser.add_argument("--urls", type=str, help="news urls for parsing, split by comma(,)")
    parser.add_argument("--input-language", type=str, default="ko", help="news language, en or ko")
    parser.add_argument("--output-language", type=str, default="ENGLISH", help="output language, KOREAN OR ENGLISH")
    parser.add_argument(
        "--llm-model",
        type=str,
        default="gpt-5-nano-2025-08-07",
        help="gpt-5-nano-2025-08-07 OR gpt-4o OR deepseek-chat OR deepseek-reasoner",
    )
    parser.add_argument("--output-crolling-dir", type=str, help="directory for crolling raw result")
    parser.add_argument("--output-llm-podcast-dir", type=str, help="directory for llm podcast result")
    parser.add_argument("--output-llm-summary-dir", type=str, help="directory for llm summary result")
    parser.add_argument("--use-chained-podcast", action="store_true", help="use summary as input for podcast generation")  # ✅
    args = parser.parse_args()

    run(
        filename=args.file_name,
        urls=args.urls,
        input_lang=args.input_language,
        ouput_lang=args.output_language,
        llm_model=args.llm_model,
        croll_ouput_dir=args.output_crolling_dir,
        llm_podcast_output_dir=args.output_llm_podcast_dir,
        llm_summary_output_dir=args.output_llm_summary_dir,
        use_chained_podcast=args.use_chained_podcast,  # ✅
    )

if __name__ == "__main__":
    main()
