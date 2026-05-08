#!/usr/bin/env python3
"""
Generate mock news data for testing the pipeline.
Since mk.co.kr is not accessible, we'll use realistic sample data.
"""

import os
import json
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

# Mock articles based on typical Korean news
MOCK_ARTICLES = [
    {
        "url": "https://www.mk.co.kr/news/economy/12345001/",
        "title": "삼성전자, 2분기 실적 발표 - 영업이익 전년대비 15% 증가",
        "text": "삼성전자가 2분기 실적을 발표했으며, 반도체 시장의 회복으로 영업이익이 전년도 같은 기간 대비 15% 증가한 것으로 나타났다. 메모리 반도체 가격이 상승하면서 수익성이 개선되었고, 특히 HBM 칩 수요 증가가 긍정적 영향을 미쳤다. 아래로는 추가 세부사항이 있지만 마진 압박요인도 존재하고 있다. AI 서버용 반도체 수요는 계속 강세를 보이고 있다.",
        "section": "economy"
    },
    {
        "url": "https://www.mk.co.kr/news/stock/12345002/",
        "title": "코스피, 장중 2,900 포인트 돌파 - 3개월 만에 최고치",
        "text": "코스피 지수가 장중 2,900 포인트를 돌파하며 3개월 만에 최고치를 경신했다. 미국의 금리 인하 기대감과 기업 실적 개선으로 매수세가 이어졌다. 대형주 중심으로 강세를 보였으며, 특히 반도체와 자동차 업종이 강세를 주도했다. 외국인 투자자들의 순매수도 계속되고 있는 상황이다.",
        "section": "stock"
    },
    {
        "url": "https://www.mk.co.kr/news/politics/12345003/",
        "title": "정부, 부동산 정책 패키지 발표 - 전월세 안정화 추진",
        "text": "정부가 서울과 수도권의 전월세 안정화를 위한 정책 패키지를 발표했다. 임차인 보호를 강화하고 전세사기 방지를 위한 법제도 개선안이 포함되었다. 구체적으로는 전세금반환보증보험 지원 확대와 주택임차인 권리 보호법 개정안이 추진될 예정이다. 이번 정책은 주거 안정성 강화를 목표로 하고 있다.",
        "section": "realestate"
    },
    {
        "url": "https://www.mk.co.kr/news/it/12345004/",
        "title": "AI 칩셋 시장, 올해 40% 성장 예상 - NVIDIA 독주 계속",
        "text": "AI 칩셋 시장이 올해 40% 성장할 것으로 예상되며, NVIDIA의 독주 현상이 지속될 것으로 보인다. 생성형 AI 붐으로 인한 수요 증가가 주요 요인이다. 국내 삼성과 SK하이닉스도 고대역폭메모리(HBM) 시장 진출을 추진 중이다. 경쟁 심화로 가격 하락 가능성도 제시되고 있다.",
        "section": "it"
    },
    {
        "url": "https://www.mk.co.kr/news/business/12345005/",
        "title": "롯데쇼핑, 면세점 확대 계획 - 동남아 시장 진출 추진",
        "text": "롯데쇼핑이 면세점 사업을 동남아 지역으로 확대하기로 했다. 태국, 베트남, 싱가포르 등에 신규 면세점 개점을 추진할 계획이다. 이는 한류 수요 확대와 관광객 증가 추세를 반영한 것이다. 올해 상반기 중 구체적인 투자 계획을 발표할 예정이다.",
        "section": "business"
    },
    {
        "url": "https://www.mk.co.kr/news/society/12345006/",
        "title": "서울 지하철 9호선 파업 대비, 교통 대책 준비",
        "text": "서울지하철 9호선 노사 협상이 교착 상태에 빠지면서 파업 가능성이 높아졌다. 시당국은 버스 노선 확충과 임시 교통 대책을 준비 중이다. 시민들은 통근 불편이 예상되어 조기 출발을 계획하고 있다. 관련 부처는 합의를 위한 중재 노력을 계속하고 있다.",
        "section": "society"
    },
    {
        "url": "https://www.mk.co.kr/news/culture/12345007/",
        "title": "한국 영화 '봄날의 기억', 칸영화제 경쟁부문 초청",
        "text": "한국 독립영화 '봄날의 기억'이 2026년 칸영화제 경쟁부문에 초청받았다. 이는 한국 영화의 국제적 위상을 보여주는 사례다. 영화는 시골 마을의 평범한 삶을 다룬 감성적 드라마로 평가받고 있다. 제작사는 국제 배급 확대를 준비하고 있다.",
        "section": "culture"
    },
    {
        "url": "https://www.mk.co.kr/news/columnists/12345008/",
        "title": "[칼럼] 글로벌 경제 불확실성 시대, 기업의 경쟁력 강화 필요",
        "text": "이 글은 전문가의 칼럼으로, 현재의 글로벌 경제 상황에서 한국 기업들이 어떻게 경쟁력을 강화할 수 있을지에 대해 논의한다. 저자는 R&D 투자 확대와 인력 양성의 중요성을 강조한다. 특히 반도체와 배터리 등 전략산업에서의 기술 혁신이 필수적이라고 주장한다. 정부 정책 지원과 민간 기업의 노력이 병행되어야 한다고 결론짓는다.",
        "section": "columnists"
    },
    {
        "url": "https://www.mk.co.kr/news/world/12345009/",
        "title": "미국 연방준비제도, 기준금리 0.25% 인하 결정",
        "text": "미국 연방준비제도(Federal Reserve)가 기준금리를 현재 수준에서 0.25% 인하하기로 결정했다. 이는 인플레이션 둔화 추세를 반영한 것이다. 파월 Fed 의장은 앞으로 추가 인하가 있을 수 있음을 시사했다. 이 결정은 글로벌 경제에 긍정적 영향을 미칠 것으로 예상된다.",
        "section": "world"
    },
    {
        "url": "https://www.mk.co.kr/news/journalist/12345010/",
        "title": "[기자수첩] 스타트업 회사 방문기 - '꿈과 현실 사이'",
        "text": "한 유명 스타트업 회사를 방문한 기자의 수첩. 회사의 역동적 분위기와 직원들의 열정이 인상적이었다. 하지만 높은 이직률과 과도한 업무 강도 등의 문제도 확인할 수 있었다. 기술 산업의 성장 뒤에 있는 현실적인 어려움들에 대해 생각해볼 필요가 있다.",
        "section": "journalist"
    },
    {
        "url": "https://www.mk.co.kr/news/editorial/12345011/",
        "title": "[사설] 저출산 문제 해결, 이제는 근본적 대책이 필요하다",
        "text": "이것은 시사매경의 사설로, 우리나라의 심각한 저출산 문제에 대해 논한다. 현재의 정책 수준으로는 부족하며, 사회 전반적인 패러다임 변화가 필요하다고 주장한다. 청년층의 경제적 부담 경감과 일-가정 양립 문화 정착이 우선되어야 한다. 국가 차원의 적극적 개입과 민간 참여가 함께 이루어져야 한다고 강조한다.",
        "section": "editorial"
    },
    {
        "url": "https://www.mk.co.kr/news/business/12345012/",
        "title": "LG전자, 친환경 가전 라인업 확대 - 2030년까지 탄소중립 추진",
        "text": "LG전자가 친환경 가전 제품 라인업을 대폭 확대한다고 발표했다. 냉장고, 세탁기, 에어컨 등 주요 제품에 에너지 효율 기술을 적용할 계획이다. 회사는 2030년까지 전 제품에서 탄소중립을 달성하는 것을 목표로 하고 있다. 이는 글로벌 ESG 경영 트렌드에 부응하려는 움직임이다.",
        "section": "business"
    },
    {
        "url": "https://www.mk.co.kr/news/economy/12345013/",
        "title": "한은, 올해 경제성장률 전망 2.5%로 소폭 상향 조정",
        "text": "한국은행이 올해 국내 경제성장률 전망을 2.5%로 상향 조정했다. 이전 전망 2.3%에서 0.2%포인트 올린 것이다. 수출 회복과 투자 증가가 긍정 요인으로 작용했다. 다만 글로벌 경제의 불확실성으로 인한 위험 요인도 남아 있다고 평가했다.",
        "section": "economy"
    },
    {
        "url": "https://www.mk.co.kr/news/it/12345014/",
        "title": "국내 배터리 기업, 글로벌 공급 계약 확대 - SK이노베이션 독주",
        "text": "국내 배터리 기업들이 글로벌 자동차 제조사와의 공급 계약을 잇따라 확대하고 있다. SK이노베이션과 LG에너지솔루션이 주요 수혜 기업이다. 전기차 시장 확대와 배터리 안정성 향상이 주요 요인이다. 2026년 배터리 수출액이 500억 달러를 넘을 것으로 예상되고 있다.",
        "section": "it"
    },
    {
        "url": "https://www.mk.co.kr/news/society/12345015/",
        "title": "강남역 대형 전시회, 5개월간 운영 예정 - 한국 현대미술 조명",
        "text": "강남역 근처 대형 미술관에서 한국 현대미술을 조명하는 전시회가 5개월간 운영될 예정이다. 300명 이상의 작가 작품이 전시될 계획이다. 이 전시회는 한국 미술의 국제적 위상을 높이는 데 기여할 것으로 기대된다. 개장식은 오는 5월 15일로 예정되어 있다.",
        "section": "culture"
    },
    {
        "url": "https://www.mk.co.kr/news/politics/12345016/",
        "title": "국회, 기후변화 대응법안 가결 - 2050년 탄소중립 법제화",
        "text": "국회가 기후변화 대응법안을 가결했으며, 2050년까지의 탄소중립 달성이 법제화되었다. 기업과 개인의 책임 범위가 명확히 규정되었다. 환경부는 구체적인 이행 계획을 수립할 예정이다. 이는 국제사회의 탄소중립 추진 움직임과 맥을 같이한다.",
        "section": "politics"
    },
    {
        "url": "https://www.mk.co.kr/news/stock/12345017/",
        "title": "개인투자자 관심 집중, 중소형주 강세 이어지는 중",
        "text": "국내 주식시장에서 개인투자자들의 관심이 중소형주에 집중되면서 강세가 계속되고 있다. 공모주 수익률도 높아지면서 신규 상장 기업 관심도 증가했다. 전문가들은 버블 우려도 제기하고 있으나 긍정적 요인이 더 크다고 평가한다. 향후 시장 심리 변화가 주목 대상이다.",
        "section": "stock"
    },
    {
        "url": "https://www.mk.co.kr/news/world/12345018/",
        "title": "유럽 중앙은행, 기준금리 인상 결정 - 통화정책 방향 전환",
        "text": "유럽중앙은행(ECB)이 기준금리를 인상하기로 결정했다. 인플레이션 완화 추세 속에서도 신중한 입장을 유지하려는 것이다. 라가르드 총재는 추후 금리 인상 가능성을 열어두었다. 이는 미국과 다른 통화정책 방향을 시사하고 있다.",
        "section": "world"
    },
    {
        "url": "https://www.mk.co.kr/news/contributors/12345019/",
        "title": "[기고] 디지털 혁신 시대의 인재 양성 전략",
        "text": "이것은 교육 전문가의 기고문으로, 디지털 시대에 필요한 인재 양성에 대해 논의한다. 기술 교육뿐만 아니라 창의성과 비판적 사고력의 중요성을 강조한다. 현재의 대학 교육 체계에 대한 개선안도 제시한다. 글로벌 경쟁력을 갖춘 인재 양성이 국가 경쟁력의 핵심이라고 결론짓는다.",
        "section": "contributors"
    },
    {
        "url": "https://www.mk.co.kr/news/realestate/12345020/",
        "title": "서울 오피스텔 시장, 가격 상승 추세 - 강남·여의도 주목",
        "text": "서울 오피스텔 시장에서 가격 상승 추세가 지속되고 있다. 특히 강남과 여의도 지역의 오피스텔이 관심을 받고 있다. 저금리 환경과 투자자 수요 증가가 주요 요인이다. 전문가들은 정책 변화에 주의할 것을 당부했다.",
        "section": "realestate"
    }
]

def main():
    summary_dir = f"out/{TODAY}/SUMMARY_KO"
    os.makedirs(summary_dir, exist_ok=True)

    print(f"[STAGE] today={TODAY}")
    print(f"[STAGE] creating_mock_data")
    print(f"[STAGE] scraped_count={len(MOCK_ARTICLES)}")

    # Sample first 3 titles
    sample_titles = [a["title"][:40] for a in MOCK_ARTICLES[:3]]
    print(f"[STAGE] sample_titles={sample_titles}")

    # Generate summaries
    written_count = 0
    for idx, article in enumerate(MOCK_ARTICLES):
        title = article["title"]
        text = article["text"]
        url = article["url"]
        section = article.get("section", "unknown")

        # Create a simple summary
        summary = f"# {title}\n\n"
        summary += "## 요약\n"
        # Use first sentence as summary
        first_sentence = text.split("。")[0] if "。" in text else text.split(".")[:2]
        if isinstance(first_sentence, str):
            summary += f"{first_sentence}\n\n"
        else:
            summary += " ".join(first_sentence) + "\n\n"

        summary += "## 주요 인용/수치\n"
        sentences = [s.strip() for s in text.split("。") if s.strip()]
        for sent in sentences[1:3]:
            summary += f"- {sent}\n"
        if len(sentences) <= 2:
            summary += "- (주요 수치 참조)\n"
        summary += "\n"

        summary += "## 시사점\n"
        summary += "이 뉴스의 의미와 영향을 이해하는 것이 중요하다.\n"

        # Add metadata
        full_summary = f"---\ntitle: {title}\nurl: {url}\ndate: {TODAY}\nsection: {section}\n---\n\n" + summary

        # Save to file
        slug = f"{section}_{idx+1:02d}".lower()
        slug = slug.replace(" ", "_").replace("-", "_")

        filepath = f"{summary_dir}/{slug}.md"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_summary)

        written_count += 1
        print(f"[SUMMARY] {idx+1}/{len(MOCK_ARTICLES)}: {filepath}")

    print(f"[STAGE] summary_written={written_count}")

    # Save articles list as JSON
    json_path = f"/tmp/scraped_{TODAY}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(MOCK_ARTICLES, f, ensure_ascii=False, indent=2)
    print(f"[STAGE] json_saved={json_path}")

    return True

if __name__ == "__main__":
    success = main()
