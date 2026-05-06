import os
import re
import markdown
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))

def get_today_str():
    """Returns today's date in YYYY-MM-DD format (KST)."""
    return datetime.now(KST).strftime("%Y-%m-%d")


def enhance_icon_blocks_in_html(html):
    """
    마크다운이 HTML로 변환된 후, <p> 태그 내부의 아이콘 패턴을
    시맨틱 블록으로 치환합니다. 한 <p> 안에 <br/>로 여러 아이콘이 섞인
    케이스도 분해하여 각각 블록으로 만듭니다.
    """
    icon_map = [
        ('✅', 'block-summary'),
        ('✦', 'block-detail'),
        ('➕', 'block-extra'),
        ('🔎', 'block-insight'),
        ('🧾', 'block-glossary'),
    ]

    def wrap_line(line):
        line = line.strip()
        if not line:
            return ''
        for icon, cls in icon_map:
            if line.startswith(icon):
                body = line[len(icon):].strip()
                return (f'<div class="news-block {cls}">'
                        f'<span class="block-icon">{icon}</span>'
                        f'<div class="block-content">{body}</div></div>')
        # 아이콘이 없는 일반 라인은 그대로 <p>로 되돌림
        return f'<p>{line}</p>'

    def replace_p(match):
        content = match.group(1)
        # <br /> 또는 \n 로 분리된 라인을 각각 검사
        lines = re.split(r'<br\s*/?>|\n', content)

        # 모든 라인이 아이콘 없는 일반 텍스트라면 원본 유지
        has_icon = any(
            any(l.strip().startswith(icon) for icon, _ in icon_map)
            for l in lines
        )
        if not has_icon:
            return match.group(0)

        return ''.join(wrap_line(l) for l in lines if l.strip())

    html = re.sub(r'<p>(.*?)</p>', replace_p, html, flags=re.DOTALL)
    return html


def post_process_html(html_body):
    """
    ### TITLE:, ### CONTENTS: 같은 헤더를 시각적 배지로 변환하고,
    원문 보기 링크 스타일링, <hr> 치환을 처리합니다.
    """
    # ### TITLE: → 배지형 서브타이틀
    html_body = re.sub(
        r'<h3[^>]*>TITLE:</h3>\s*<p>(.*?)</p>',
        r'<div class="article-subtitle"><span class="subtitle-label">HEADLINE</span><h3 class="article-title">\1</h3></div>',
        html_body,
        flags=re.DOTALL
    )

    # ### CONTENTS: 라벨 제거 → 얇은 구분선으로 변환
    html_body = re.sub(r'<h3[^>]*>CONTENTS:</h3>', '<div class="contents-divider"></div>', html_body)

    # 원문 보기 링크 스타일링
    html_body = re.sub(
        r'<p><a href="([^"]+)">원문 보기</a></p>',
        r'<p class="source-link"><a href="\1" target="_blank" rel="noopener">원문 보기 <span class="arrow">→</span></a></p>',
        html_body
    )

    # <hr /> 또는 <hr>을 기사 구분자로 (변형 모두 처리)
    html_body = re.sub(r'<hr\s*/?>', '<div class="article-separator"></div>', html_body)

    return html_body


def wrap_articles_in_cards(html_body):
    """
    각 ## 제목부터 다음 ## 또는 <hr> 전까지를 <article> 카드로 감쌉니다.
    """
    # 먼저 separator로 split
    parts = html_body.split('<div class="article-separator"></div>')
    wrapped_parts = []
    for i, part in enumerate(parts):
        part = part.strip()
        if '<h2' in part:
            wrapped_parts.append(f'<article class="news-article" data-index="{i}">{part}</article>')
        else:
            wrapped_parts.append(part)
    return '\n'.join(wrapped_parts)


def create_html_from_markdown(md_content, title):
    """
    Editorial 스타일 - 다크모드 토글, 진행률 바, 섹션 접기 포함
    """
    extension_configs = {
        'toc': {
            'baselevel': 1,
            'toc_depth': 2,
            'title': None,
        }
    }

    md_extensions = ['toc', 'fenced_code', 'tables', 'sane_lists', 'codehilite']

    md = markdown.Markdown(
        extensions=md_extensions,
        extension_configs=extension_configs
    )

    # 마크다운 → HTML (전처리 없이 순수 변환)
    html_body = md.convert(md_content)

    # 후처리 1단계: 아이콘 블록을 시맨틱 <div>로 치환
    html_body = enhance_icon_blocks_in_html(html_body)

    # 후처리 2단계: TITLE:/CONTENTS: 배지화, 원문링크 스타일링, hr 치환
    html_body = post_process_html(html_body)

    # 후처리 3단계: 기사 단위 카드 래핑
    html_body = wrap_articles_in_cards(html_body)

    toc_content = md.toc if md.toc and len(md.toc) > 50 else '<p class="toc-empty">목차 없음</p>'

    # 오늘 날짜
    today = get_today_str()
    total_articles = md_content.count('\n## ') + (1 if md_content.startswith('## ') else 0)

    css_style = r"""
    /* ============================================
       Editorial Design System
       ============================================ */
    :root {
        --font-serif: 'Noto Serif KR', 'Source Serif Pro', Georgia, serif;
        --font-sans: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
        --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

        /* Light theme - warm neutral */
        --bg-primary: #fafaf7;
        --bg-secondary: #ffffff;
        --bg-tertiary: #f3f2ed;
        --bg-card: #ffffff;
        --border-subtle: #e8e6df;
        --border-strong: #2c2c2c;

        --text-primary: #1a1a1a;
        --text-secondary: #4a4a4a;
        --text-tertiary: #888580;
        --text-muted: #a8a5a0;

        --accent: #8b0000;
        --accent-soft: rgba(139, 0, 0, 0.08);
        --accent-line: #c9302c;

        /* Semantic colors - 아이콘 블록 */
        --color-summary: #1a4d3a;
        --color-summary-bg: #ecf4ef;
        --color-detail: #2c3e50;
        --color-detail-bg: #f5f5f0;
        --color-extra: #6b5b3e;
        --color-extra-bg: #f7f3ea;
        --color-insight: #5b3a8c;
        --color-insight-bg: #f1ecf7;
        --color-glossary: #8b6f47;
        --color-glossary-bg: #faf6ef;

        --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
        --shadow-md: 0 2px 8px rgba(0,0,0,0.06);
        --shadow-lg: 0 4px 20px rgba(0,0,0,0.08);

        --radius-sm: 4px;
        --radius-md: 8px;
        --radius-lg: 12px;
    }

    [data-theme="dark"] {
        --bg-primary: #0f0f0e;
        --bg-secondary: #1a1a18;
        --bg-tertiary: #242420;
        --bg-card: #1a1a18;
        --border-subtle: #2e2e2a;
        --border-strong: #e8e6df;

        --text-primary: #f0ede4;
        --text-secondary: #c8c5bd;
        --text-tertiary: #8a8680;
        --text-muted: #5a5650;

        --accent: #e85d5d;
        --accent-soft: rgba(232, 93, 93, 0.12);
        --accent-line: #e85d5d;

        --color-summary: #7bc49a;
        --color-summary-bg: rgba(123, 196, 154, 0.1);
        --color-detail: #a8c8e5;
        --color-detail-bg: rgba(168, 200, 229, 0.08);
        --color-extra: #d4b878;
        --color-extra-bg: rgba(212, 184, 120, 0.1);
        --color-insight: #c9a8e8;
        --color-insight-bg: rgba(201, 168, 232, 0.1);
        --color-glossary: #d4b896;
        --color-glossary-bg: rgba(212, 184, 150, 0.08);
    }

    * { box-sizing: border-box; }

    html { scroll-behavior: smooth; }

    body {
        font-family: var(--font-sans);
        line-height: 1.7;
        color: var(--text-primary);
        background: var(--bg-primary);
        margin: 0;
        padding: 0;
        transition: background 0.3s ease, color 0.3s ease;
        -webkit-font-smoothing: antialiased;
    }

    /* ============================================
       Progress Bar
       ============================================ */
    .reading-progress {
        position: fixed;
        top: 0;
        left: 0;
        width: 0%;
        height: 3px;
        background: var(--accent);
        z-index: 1000;
        transition: width 0.1s linear;
    }

    /* ============================================
       Top Bar
       ============================================ */
    .top-bar {
        position: sticky;
        top: 0;
        background: var(--bg-secondary);
        border-bottom: 1px solid var(--border-subtle);
        z-index: 100;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        background-color: rgba(255, 255, 255, 0.85);
    }

    [data-theme="dark"] .top-bar {
        background-color: rgba(26, 26, 24, 0.85);
    }

    .top-bar-inner {
        max-width: 1400px;
        margin: 0 auto;
        padding: 14px 40px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 20px;
    }

    .brand {
        font-family: var(--font-serif);
        font-weight: 700;
        font-size: 1.3rem;
        letter-spacing: -0.02em;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .brand-mark {
        width: 8px;
        height: 8px;
        background: var(--accent);
        border-radius: 50%;
    }

    .top-bar-meta {
        display: flex;
        gap: 16px;
        align-items: center;
        font-family: var(--font-mono);
        font-size: 0.78rem;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }

    .theme-toggle {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-subtle);
        color: var(--text-secondary);
        width: 36px;
        height: 36px;
        border-radius: 50%;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 1rem;
        transition: all 0.2s;
        padding: 0;
    }

    .theme-toggle:hover {
        background: var(--accent-soft);
        color: var(--accent);
        border-color: var(--accent);
        transform: rotate(15deg);
    }

    /* ============================================
       Main Layout
       ============================================ */
    .main-wrapper {
        display: grid;
        grid-template-columns: 260px 1fr;
        max-width: 1400px;
        margin: 0 auto;
        padding: 40px;
        gap: 50px;
        align-items: flex-start;
    }

    /* ============================================
       Sidebar / TOC
       ============================================ */
    #sidebar {
        position: sticky;
        top: 90px;
        max-height: calc(100vh - 110px);
        overflow-y: auto;
        padding-right: 10px;
    }

    #sidebar::-webkit-scrollbar { width: 4px; }
    #sidebar::-webkit-scrollbar-track { background: transparent; }
    #sidebar::-webkit-scrollbar-thumb {
        background: var(--border-subtle);
        border-radius: 2px;
    }

    .sidebar-label {
        font-family: var(--font-mono);
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        color: var(--text-tertiary);
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border-subtle);
    }

    .toc ul {
        list-style: none;
        padding: 0;
        margin: 0;
        counter-reset: toc-counter;
    }

    .toc ul ul { display: none; }

    .toc li {
        counter-increment: toc-counter;
        position: relative;
        margin: 0;
    }

    .toc a {
        display: block;
        padding: 10px 0 10px 32px;
        text-decoration: none;
        color: var(--text-secondary);
        font-size: 0.85rem;
        line-height: 1.5;
        border-left: 2px solid transparent;
        padding-left: 16px;
        transition: all 0.2s;
        position: relative;
    }

    .toc a::before {
        content: counter(toc-counter, decimal-leading-zero);
        position: absolute;
        left: -24px;
        top: 10px;
        font-family: var(--font-mono);
        font-size: 0.7rem;
        color: var(--text-muted);
        font-weight: 500;
    }

    .toc a:hover {
        color: var(--accent);
        border-left-color: var(--accent);
        background: var(--accent-soft);
    }

    .toc a.active {
        color: var(--accent);
        border-left-color: var(--accent);
        font-weight: 500;
    }

    .toc-empty {
        font-size: 0.85rem;
        color: var(--text-muted);
        font-style: italic;
    }

    /* ============================================
       Content Area
       ============================================ */
    .content-main { min-width: 0; }

    .masthead {
        border-bottom: 4px double var(--text-primary);
        padding-bottom: 30px;
        margin-bottom: 50px;
    }

    .masthead-kicker {
        font-family: var(--font-mono);
        font-size: 0.75rem;
        letter-spacing: 0.2em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 16px;
        font-weight: 600;
    }

    .masthead h1 {
        font-family: var(--font-serif);
        font-size: 3.2rem;
        font-weight: 700;
        line-height: 1.1;
        letter-spacing: -0.02em;
        margin: 0 0 20px 0;
        color: var(--text-primary);
    }

    .masthead-meta {
        display: flex;
        gap: 24px;
        font-family: var(--font-mono);
        font-size: 0.8rem;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .masthead-meta span {
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }

    .masthead-meta .dot {
        width: 4px;
        height: 4px;
        background: var(--text-muted);
        border-radius: 50%;
    }

    /* ============================================
       News Article Cards
       ============================================ */
    .news-article {
        background: var(--bg-card);
        border: 1px solid var(--border-subtle);
        border-radius: var(--radius-lg);
        padding: 40px 44px;
        margin-bottom: 28px;
        box-shadow: var(--shadow-sm);
        transition: all 0.25s ease;
        position: relative;
        overflow: hidden;
    }

    .news-article::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 3px;
        height: 0;
        background: var(--accent);
        transition: height 0.3s ease;
    }

    .news-article:hover {
        box-shadow: var(--shadow-lg);
        transform: translateY(-1px);
    }

    .news-article:hover::before {
        height: 100%;
    }

    .news-article h2 {
        font-family: var(--font-serif);
        font-size: 1.75rem;
        font-weight: 700;
        line-height: 1.3;
        letter-spacing: -0.01em;
        margin: 0 0 8px 0;
        color: var(--text-primary);
        cursor: pointer;
        user-select: none;
        padding-right: 40px;
        position: relative;
    }

    .news-article h2::after {
        content: '−';
        position: absolute;
        right: 0;
        top: 50%;
        transform: translateY(-50%);
        font-size: 1.5rem;
        font-weight: 300;
        color: var(--text-muted);
        width: 28px;
        height: 28px;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 1px solid var(--border-subtle);
        border-radius: 50%;
        transition: all 0.2s;
    }

    .news-article.collapsed h2::after {
        content: '+';
    }

    .news-article h2:hover::after {
        border-color: var(--accent);
        color: var(--accent);
    }

    .source-link {
        margin: 0 0 24px 0;
    }

    .source-link a {
        font-family: var(--font-mono);
        font-size: 0.72rem;
        color: var(--text-tertiary);
        text-decoration: none;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        padding: 4px 10px;
        border: 1px solid var(--border-subtle);
        border-radius: 20px;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        transition: all 0.2s;
    }

    .source-link a:hover {
        color: var(--accent);
        border-color: var(--accent);
        background: var(--accent-soft);
    }

    .source-link .arrow {
        transition: transform 0.2s;
    }

    .source-link a:hover .arrow {
        transform: translateX(3px);
    }

    /* Article body content wrapper (foldable) */
    .article-body {
        max-height: 10000px;
        overflow: hidden;
        transition: max-height 0.4s ease, opacity 0.3s ease;
        opacity: 1;
    }

    .news-article.collapsed .article-body {
        max-height: 0;
        opacity: 0;
    }

    /* ============================================
       Article Subtitle (HEADLINE)
       ============================================ */
    .article-subtitle {
        background: var(--bg-tertiary);
        border-left: 4px solid var(--accent);
        padding: 20px 24px;
        margin: 0 0 28px 0;
        border-radius: 0 var(--radius-md) var(--radius-md) 0;
    }

    .subtitle-label {
        display: inline-block;
        font-family: var(--font-mono);
        font-size: 0.65rem;
        letter-spacing: 0.2em;
        color: var(--accent);
        font-weight: 700;
        margin-bottom: 8px;
    }

    .article-title {
        font-family: var(--font-serif);
        font-size: 1.15rem;
        font-weight: 600;
        line-height: 1.5;
        margin: 0;
        color: var(--text-primary);
    }

    .contents-divider {
        height: 1px;
        background: linear-gradient(to right, var(--border-subtle), transparent);
        margin: 0 0 24px 0;
    }

    /* ============================================
       News Blocks (icon rows)
       ============================================ */
    .news-block {
        display: grid;
        grid-template-columns: 32px 1fr;
        gap: 14px;
        padding: 14px 18px;
        margin: 8px 0;
        border-radius: var(--radius-md);
        line-height: 1.65;
        font-size: 0.96rem;
        transition: background 0.2s;
    }

    .block-icon {
        font-size: 1.05rem;
        line-height: 1.65;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding-top: 2px;
    }

    .block-content {
        color: var(--text-primary);
    }

    /* 핵심 요약 - 가장 강조 */
    .block-summary {
        background: var(--color-summary-bg);
        border-left: 3px solid var(--color-summary);
        font-weight: 500;
        margin-bottom: 16px;
    }
    .block-summary .block-content {
        color: var(--color-summary);
        font-weight: 600;
    }
    [data-theme="dark"] .block-summary .block-content {
        color: var(--color-summary);
    }

    /* 주요 내용 */
    .block-detail {
        background: transparent;
        padding: 10px 18px 10px 0;
        border-left: none;
    }
    .block-detail .block-icon {
        color: var(--accent);
        font-weight: bold;
    }

    /* 추가 내용 */
    .block-extra {
        background: var(--color-extra-bg);
        border-left: 2px dashed var(--color-extra);
        margin: 12px 0;
        font-size: 0.92rem;
    }
    .block-extra .block-content { color: var(--color-extra); }

    /* 의미/영향 - 인사이트 */
    .block-insight {
        background: var(--color-insight-bg);
        border: 1px solid transparent;
        border-left: 3px solid var(--color-insight);
        margin-top: 16px;
        font-weight: 500;
        font-style: italic;
    }
    .block-insight .block-content { color: var(--color-insight); }

    /* 용어 설명 */
    .block-glossary {
        background: var(--color-glossary-bg);
        border-top: 1px solid var(--border-subtle);
        border-radius: 0;
        font-size: 0.88rem;
        margin-top: 20px;
        padding-top: 18px;
        padding-bottom: 18px;
    }
    .block-glossary .block-content {
        color: var(--color-glossary);
        font-style: italic;
    }

    /* ============================================
       Miscellaneous
       ============================================ */
    .article-separator { display: none; }

    p { margin: 12px 0; }

    code {
        font-family: var(--font-mono);
        background: var(--bg-tertiary);
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.88em;
    }

    pre {
        background: var(--bg-tertiary);
        border: 1px solid var(--border-subtle);
        color: var(--text-primary);
        padding: 20px;
        border-radius: var(--radius-md);
        overflow-x: auto;
        font-size: 0.88rem;
    }

    a {
        color: var(--accent);
        text-decoration: none;
        border-bottom: 1px solid transparent;
        transition: border-color 0.2s;
    }

    a:hover { border-bottom-color: var(--accent); }

    /* ============================================
       To-top Button
       ============================================ */
    #to-top-btn {
        display: none;
        position: fixed;
        bottom: 30px;
        right: 30px;
        background: var(--text-primary);
        color: var(--bg-primary);
        border: none;
        width: 48px;
        height: 48px;
        border-radius: 50%;
        cursor: pointer;
        font-size: 18px;
        box-shadow: var(--shadow-lg);
        transition: transform 0.2s;
        z-index: 999;
    }

    #to-top-btn:hover { transform: translateY(-3px); }

    /* ============================================
       Footer
       ============================================ */
    .footer {
        margin-top: 80px;
        padding: 40px 0 60px;
        border-top: 1px solid var(--border-subtle);
        text-align: center;
        font-family: var(--font-mono);
        font-size: 0.75rem;
        color: var(--text-tertiary);
        text-transform: uppercase;
        letter-spacing: 0.15em;
    }

    /* ============================================
       Mobile Responsive
       ============================================ */
    @media (max-width: 900px) {
        .top-bar-inner { padding: 12px 20px; }
        .brand { font-size: 1.1rem; }
        .top-bar-meta { gap: 10px; font-size: 0.7rem; }

        .main-wrapper {
            grid-template-columns: 1fr;
            padding: 20px;
            gap: 20px;
        }

        #sidebar {
            position: relative;
            top: 0;
            max-height: none;
            border: 1px solid var(--border-subtle);
            border-radius: var(--radius-md);
            padding: 20px;
            background: var(--bg-card);
        }

        .masthead h1 { font-size: 2rem; }
        .masthead-meta { flex-wrap: wrap; gap: 12px; font-size: 0.7rem; }

        .news-article {
            padding: 28px 24px;
        }

        .news-article h2 { font-size: 1.35rem; padding-right: 32px; }
        .article-subtitle { padding: 16px 18px; }
        .news-block { padding: 12px 14px; font-size: 0.92rem; }
    }

    /* Fade-in animation */
    @keyframes fadeUp {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .news-article {
        animation: fadeUp 0.4s ease both;
    }
    """

    javascript = r"""
    document.addEventListener('DOMContentLoaded', function() {
        // 1. Theme toggle (persists via data-attribute only; no storage in artifacts)
        const themeToggle = document.getElementById('theme-toggle');
        const root = document.documentElement;
        let isDark = false;

        // Detect system preference on first load
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            root.setAttribute('data-theme', 'dark');
            isDark = true;
            themeToggle.textContent = '☀';
        }

        themeToggle.addEventListener('click', function() {
            isDark = !isDark;
            if (isDark) {
                root.setAttribute('data-theme', 'dark');
                themeToggle.textContent = '☀';
            } else {
                root.removeAttribute('data-theme');
                themeToggle.textContent = '☾';
            }
        });

        // 2. Wrap article bodies for collapse/expand
        document.querySelectorAll('.news-article').forEach(function(article) {
            const h2 = article.querySelector('h2');
            if (!h2) return;

            // Gather everything after h2 into .article-body wrapper
            const body = document.createElement('div');
            body.className = 'article-body';
            let next = h2.nextSibling;
            const toMove = [];
            while (next) {
                toMove.push(next);
                next = next.nextSibling;
            }
            toMove.forEach(function(node) { body.appendChild(node); });
            article.appendChild(body);

            // Click h2 to toggle
            h2.addEventListener('click', function() {
                article.classList.toggle('collapsed');
            });
        });

        // 3. Reading progress bar
        const progressBar = document.getElementById('reading-progress');
        function updateProgress() {
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollTop = window.scrollY;
            const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
            progressBar.style.width = progress + '%';
        }

        // 4. To-top button
        const toTopBtn = document.getElementById('to-top-btn');
        toTopBtn.addEventListener('click', function() {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        });

        // 5. TOC active link highlighting (intersection observer)
        const tocLinks = document.querySelectorAll('.toc a');
        const articleHeadings = document.querySelectorAll('.news-article h2');

        window.addEventListener('scroll', function() {
            updateProgress();
            toTopBtn.style.display = (window.scrollY > 400) ? 'block' : 'none';

            // Find current section
            let current = '';
            articleHeadings.forEach(function(heading) {
                const rect = heading.getBoundingClientRect();
                if (rect.top <= 120) {
                    current = heading.id || '';
                }
            });

            tocLinks.forEach(function(link) {
                link.classList.remove('active');
                if (link.getAttribute('href') === '#' + current) {
                    link.classList.add('active');
                }
            });
        });

        updateProgress();
    });
    """

    html_template = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" as="style" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css" />
    <style>{css_style}</style>
</head>
<body>
    <div class="reading-progress" id="reading-progress"></div>

    <header class="top-bar">
        <div class="top-bar-inner">
            <div class="brand">
                <span class="brand-mark"></span>
                <span>The Daily Brief</span>
            </div>
            <div class="top-bar-meta">
                <span>{today}</span>
                <button class="theme-toggle" id="theme-toggle" aria-label="Toggle theme">☾</button>
            </div>
        </div>
    </header>

    <div class="main-wrapper">
        <nav id="sidebar">
            <div class="sidebar-label">Index · 뉴스 목록</div>
            <div class="toc">
                {toc_content}
            </div>
        </nav>

        <main class="content-main">
            <header class="masthead">
                <div class="masthead-kicker">Daily Market Brief</div>
                <h1>{title}</h1>
                <div class="masthead-meta">
                    <span>📅 {today}</span>
                    <span class="dot"></span>
                    <span>📰 {total_articles} Articles</span>
                    <span class="dot"></span>
                    <span>KST</span>
                </div>
            </header>

            {html_body}

            <footer class="footer">
                — End of Brief —
            </footer>
        </main>
    </div>

    <button id="to-top-btn" title="Go to top" aria-label="Go to top">↑</button>
    <script>{javascript}</script>
</body>
</html>"""

    return html_template


def find_md_files(start_path):
    md_files = []
    for root, _, files in os.walk(start_path):
        if os.path.basename(root).lower() == "html":
            continue
        for file in files:
            if file.endswith(".md"):
                md_files.append(os.path.join(root, file))
    return md_files


def should_skip(md_path, html_path):
    if not os.path.exists(html_path):
        return False
    return os.path.getmtime(html_path) >= os.path.getmtime(md_path)


def main():
    print("[HTML Gen] Processing...")
    out_dir = "out"
    if not os.path.isdir(out_dir):
        print(f"Error: '{out_dir}' directory not found.")
        return

    for dir_name in os.listdir(out_dir):
        dir_path = os.path.join(out_dir, dir_name)
        if not os.path.isdir(dir_path):
            continue

        html_output_dir = os.path.join(dir_path, "html")
        os.makedirs(html_output_dir, exist_ok=True)

        for md_path in find_md_files(dir_path):
            base_name = os.path.splitext(os.path.basename(md_path))[0]
            html_path = os.path.join(html_output_dir, f"{base_name}.html")

            if should_skip(md_path, html_path):
                continue

            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()

            title = base_name.replace("_", " ").title()
            full_html = create_html_from_markdown(md_content, title)

            with open(html_path, "w", encoding="utf-8") as f:
                f.write(full_html)
            print(f"[Converted] {base_name}.html")


if __name__ == "__main__":
    main()
