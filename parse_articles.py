#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import re
import os

def clean_text(text):
    """Remove emojis and clean text"""
    # Remove all emojis and symbols
    text = re.sub(r'[📈📉📊🚀💡💪🤔🧐✨⚡️🇰🇷🌟🌐🛠️💰🚦💲🎯📉💯🎉🔥👍✅🎊📄🎁📱💼📚⚖️🌍📢🔔📂📝💎🎪📍📌📖🔍📋🔮📸📰📻📺🎨🎬🎸🎤📡🔧🔨🛡️⛡️🔒🔓🔅🔆🌕🌑🌅🌇🏆🎖️🥇🥈🥉🏅🎗️⭐️✴️🌟💫🌠☄️🎇🎆🧿🔸🔹💎🔷🔶🌈⚡️❤️💚💙💜🖤🤍🤎💗💖💕💓💔❤️‍🔥❤️‍🩹💟💞💝🦾🦿🧠🫀🫁🦷🦴👀👁️👄👅👃👂🦻🦶🦵💪👍👎👏🙌👐🤲🤝🤜🤛✊👊🖐️✋🤚👋🤟🤘🤙🖖👌🤏✌️🤞🖕👆👇☝️👉👈🫲🫱🫰🫳🫴🙏✍️💅🤳💃🕺🕴️🧘🧘‍♂️🧘‍♀️🚶🚶‍♂️🚶‍♀️🏃🏃‍♂️🏃‍♀️🧍🧍‍♂️🧍‍♀️🧎🧎‍♂️🧎‍♀️🤸🤸‍♂️🤸‍♀️🤾🤾‍♂️🤾‍♀️⛷️🏂🏇🧗🧗‍♂️🧗‍♀️🚵🚵‍♂️🚵‍♀️🚴🚴‍♂️🚴‍♀️🏆🥇🥈🥉🏅🎖️🏵️🎗️🎪🤹🤹‍♂️🤹‍♀️🎭🎨🎬🎤🎧🎼🎵🎶🎹🎸🎻🎺🎷🥁🪘🎲🎯🎳🎮🎰🧩]', '', text)
    
    # Clean up repeated patterns
    text = re.sub(r'[\n\r]+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

def categorize_article(title, url, text):
    """Categorize article based on content"""
    title_lower = title.lower()
    text_lower = text.lower()
    
    if any(word in title_lower for word in ['etf', 'ETF']):
        return 'ETF/펀드'
    elif any(word in title_lower for word in ['반도체', '삼성전자', 'sk하이닉스', 'ai', 'AI']):
        return '반도체/AI'
    elif any(word in title_lower for word in ['코스피', '증시', '주식시장', '지수']):
        return '증시 동향'
    elif any(word in title_lower for word in ['미국', '중국', '일본', '글로벌']):
        return '해외 증시'
    elif any(word in title_lower for word in ['부동산', '아파트', '집값']):
        return '부동산'
    elif any(word in title_lower for word in ['기업', '실적', '매출', '영업']):
        return '기업 실적'
    elif any(word in title_lower for word in ['경제', '정책', '금리', '금융']):
        return '경제 정책'
    else:
        return '기타'

def extract_summary_from_text(text):
    """Extract key information from article text"""
    # Remove excessive repetition and emoji
    text = clean_text(text)
    
    # Split into sentences
    sentences = re.split(r'[.!?]\s+', text)
    
    # Filter out very short or repetitive sentences
    unique_sentences = []
    for sentence in sentences:
        if len(sentence.strip()) > 20 and sentence.strip() not in unique_sentences:
            unique_sentences.append(sentence.strip())
    
    return unique_sentences[:10]  # Return first 10 meaningful sentences

def extract_prospects(text):
    """Extract future prospects from text"""
    text = clean_text(text)
    
    # Look for future-related keywords
    future_keywords = ['예상', '전망', '계획', '예정', '기대', '향후', '미래', '장기적', '내년', '다음', '앞으로']
    
    sentences = re.split(r'[.!?]\s+', text)
    prospect_sentences = []
    
    for sentence in sentences:
        if any(keyword in sentence for keyword in future_keywords) and len(sentence.strip()) > 20:
            prospect_sentences.append(sentence.strip())
    
    return prospect_sentences[:3]  # Return first 3 prospect sentences

def main():
    # Read JSON file
    with open('/home/runner/work/news_maker/news_maker/out/2026-05-07/scraped.json', 'r', encoding='utf-8') as f:
        articles = json.load(f)
    
    # Process all articles
    processed_articles = []
    
    for i, article in enumerate(articles):
        url = article['url']
        title = article['title']
        text = article['text']
        
        # Clean title (remove site name)
        clean_title = re.sub(r'\s*-\s*매일경제\s*$', '', title).strip()
        clean_title = re.sub(r'^\s*\[.*?\]\s*', '', clean_title).strip()
        clean_title = re.sub(r'^"', '', clean_title)
        clean_title = re.sub(r'"$', '', clean_title)
        
        category = categorize_article(title, url, text)
        summary_sentences = extract_summary_from_text(text)
        prospect_sentences = extract_prospects(text)
        
        processed_article = {
            'index': i + 1,
            'title': clean_title,
            'url': url,
            'category': category,
            'text': clean_text(text),
            'summary_sentences': summary_sentences,
            'prospect_sentences': prospect_sentences
        }
        
        processed_articles.append(processed_article)
    
    # Save processed data
    with open('/home/runner/work/news_maker/news_maker/processed_articles.json', 'w', encoding='utf-8') as f:
        json.dump(processed_articles, f, ensure_ascii=False, indent=2)
    
    print(f"Processed {len(processed_articles)} articles")
    
    # Print summary
    for article in processed_articles[:3]:
        print(f"\n{article['index']}. {article['title']}")
        print(f"Category: {article['category']}")
        print(f"Summary sentences: {len(article['summary_sentences'])}")
        print(f"Prospect sentences: {len(article['prospect_sentences'])}")

if __name__ == "__main__":
    main()