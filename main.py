"""
全球 AI 重大新闻日报
每天自动收集欧、美、中 AI 重大突破性新闻，AI 总结后推送到微信
GitHub Actions 定时触发，电脑关机也能运行
"""

import os
import sys
import json
import hashlib
import time
from datetime import datetime, timedelta
from pathlib import Path

import feedparser
import requests

import google.generativeai as genai


# ──────────────────── 配置 ────────────────────

# RSS 新闻源列表（英文为主，覆盖欧美主要 AI 媒体）
RSS_SOURCES_EN = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://venturebeat.com/category/ai/feed/",
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://www.artificialintelligence-news.com/feed/",
]

# 中文 AI 媒体 RSS
RSS_SOURCES_CN = [
    "https://www.jiqizhixin.com/rss",
    "https://www.qbitai.com/feed",
]

# NewsAPI 配置（可选，免费 100 次/天）
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Gemini 配置
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# PushPlus 配置
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
PUSHPLUS_URL = "http://www.pushplus.plus/send"


def fetch_rss_articles(sources, max_per_source=10):
    """从 RSS 源获取最近 24 小时的文章"""
    articles = []
    cutoff = datetime.now() - timedelta(hours=48)  # 48h 宽容窗口

    for url in sources:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:max_per_source]:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6])

                if published and published < cutoff:
                    continue

                articles.append({
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", ""),
                    "link": entry.get("link", ""),
                    "source": feed.feed.get("title", "Unknown"),
                    "published": published.isoformat() if published else "unknown",
                })
        except Exception as e:
            print(f"[RSS] Failed to fetch {url}: {e}")

    return articles


def fetch_newsapi_articles():
    """从 NewsAPI 获取 AI 相关新闻（需要 API key）"""
    if not NEWS_API_KEY:
        return []

    articles = []
    queries = [
        "AI artificial intelligence breakthrough",
        "large language model release",
        "AI regulation EU US",
        "中国 人工智能 突破",
    ]

    from_date = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")

    for q in queries:
        try:
            resp = requests.get(NEWS_API_URL, params={
                "q": q,
                "from": from_date,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": 10,
                "apiKey": NEWS_API_KEY,
            }, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("articles", []):
                    articles.append({
                        "title": item.get("title", ""),
                        "summary": item.get("description", ""),
                        "link": item.get("url", ""),
                        "source": item.get("source", {}).get("name", "NewsAPI"),
                        "published": item.get("publishedAt", ""),
                    })
        except Exception as e:
            print(f"[NewsAPI] Error for query '{q}': {e}")

    return articles


def filter_articles(articles):
    """去重 + 限制总数避免 token 过长"""
    seen = set()
    unique = []
    for a in articles:
        key = a["title"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    # 取最近 60 条给 Gemini 筛选
    return unique[:60]


def build_prompt(articles):
    """构建发给 Gemini 的 prompt"""
    news_text = ""
    for i, a in enumerate(articles):
        news_text += f"\n[{i+1}] {a['title']}\n  摘要: {a['summary'][:200]}\n  来源: {a['source']}\n  链接: {a['link']}\n"

    today = datetime.now().strftime("%Y年%m月%d日")

    return f"""你是一位资深 AI 行业分析师。请从以下近 48 小时的 AI 相关新闻中，筛选出具有"较大突破性"的新闻，并以中文日报格式输出。

## 筛选标准（仅选真正重要的）

必须属于以下类型之一，否则不要收录：
- 大模型/LLM 重大版本发布或能力跃升（如 GPT 级大版本、新架构）
- AI 政策法规重大转折（欧盟 AI 法案、美国/中国重大监管动作）
- AI 领域重大融资/并购（亿美元级别或行业标杆）
- AI 技术真正的前沿突破（新算法、新范式、SOTA 刷新）
- AI 行业格局性事件（大公司战略转型、重大合作/拆分）
- AI 安全/对齐领域的重大进展或警示

## 排除标准
不要收录以下内容：
- 常规产品小更新、小功能迭代
- 普通合作/投资（非战略性）
- 缺乏实质内容的行业评论
- 已知信息的重复报道
- 模糊的预测或猜测性内容

## 输出格式（严格遵守）

---
🌍 **全球AI重大新闻日报** | {today}

🇺🇸🇪🇺 **欧美要闻**

**新闻标题1**
简要说明（1-2句），来源：来源名

**新闻标题2**
简要说明（1-2句），来源：来源名

🇨🇳 **中国要闻**

**新闻标题1**
简要说明（1-2句），来源：来源名

💡 **今日洞察**：1-2句话总结今日全球AI领域最值得关注的趋势或信号。

---

## 要求
- 宁缺毋滥，如果某区域没有真正突破性新闻，可以注明"今日无重大新闻"
- 总条数控制在 4-8 条
- 标题使用中文，说清楚核心突破点
- 每条保留原文链接

以下是待筛选的新闻：
{news_text}
"""


def generate_report(prompt):
    """调用 Gemini 生成日报"""
    model = genai.GenerativeModel(
        "gemini-2.5-flash",
        generation_config={
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 2048,
        },
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return None


def push_to_wechat(title, content):
    """通过 PushPlus 推送到微信"""
    if not PUSHPLUS_TOKEN:
        print("[PushPlus] No token configured, skipping push")
        return False

    payload = {
        "token": PUSHPLUS_TOKEN,
        "title": title,
        "content": content,
        "template": "markdown",
    }

    try:
        resp = requests.post(PUSHPLUS_URL, json=payload, timeout=15)
        result = resp.json()
        if result.get("code") == 200:
            print("[PushPlus] Sent successfully!")
            return True
        else:
            print(f"[PushPlus] Failed: {result}")
            return False
    except Exception as e:
        print(f"[PushPlus] Error: {e}")
        return False


def fallback_report(articles):
    """如果 Gemini 不可用，生成简易版报告"""
    today = datetime.now().strftime("%Y年%m月%d日")
    lines = [
        f"---",
        f"🌍 **全球AI重大新闻日报** | {today}",
        f"",
        f"⚠️ AI 总结服务暂时不可用，以下是近24小时AI相关新闻列表：",
        f"",
    ]

    for a in articles[:8]:
        source_label = f"来源：{a['source']}"
        lines.append(f"**{a['title']}**")
        lines.append(f"{source_label}")
        lines.append(f"[阅读原文]({a['link']})")
        lines.append("")

    lines.append(f"💡 请等待下次获取 AI 总结版。")
    lines.append(f"---")

    return "\n".join(lines)


def main():
    print(f"[{datetime.now()}] Starting AI News Daily...")

    # 1. 收集新闻
    print("[Step 1] Fetching news from RSS...")
    articles = fetch_rss_articles(RSS_SOURCES_EN + RSS_SOURCES_CN)

    if NEWS_API_KEY:
        print("[Step 1b] Fetching news from NewsAPI...")
        articles += fetch_newsapi_articles()

    print(f"[Step 1] Collected {len(articles)} articles total")

    if not articles:
        print("[Step 1] No articles found, exiting")
        return

    # 2. 去重
    articles = filter_articles(articles)
    print(f"[Step 2] {len(articles)} unique articles after dedup")

    # 3. AI 总结
    if GEMINI_API_KEY:
        print("[Step 3] Generating report with Gemini...")
        prompt = build_prompt(articles)
        report = generate_report(prompt)
        if report:
            print("[Step 3] Report generated ✓")
            # 只保留从第一个 --- 开始的内容
            idx = report.find("---")
            if idx >= 0:
                report = report[idx:]
        else:
            print("[Step 3] Gemini failed, using fallback")
            report = fallback_report(articles)
    else:
        print("[Step 3] No Gemini API key, using fallback")
        report = fallback_report(articles)

    # 4. 推送微信
    title = f"AI 日报 {datetime.now().strftime('%Y-%m-%d')}"
    success = push_to_wechat(title, report)

    # 5. 输出结果
    print("=" * 50)
    print(report)
    print("=" * 50)
    print(f"[Done] Push {'success' if success else 'failed'}")

    if not success and PUSHPLUS_TOKEN:
        sys.exit(1)


if __name__ == "__main__":
    main()
