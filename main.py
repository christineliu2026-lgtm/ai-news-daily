"""
鍏ㄧ悆 AI 閲嶅ぇ鏂伴椈鏃ユ姤
姣忓ぉ鑷姩鏀堕泦娆с€佺編銆佷腑 AI 閲嶅ぇ绐佺牬鎬ф柊闂伙紝AI 鎬荤粨鍚庢帹閫佸埌寰俊
GitHub Actions 瀹氭椂瑙﹀彂锛岀數鑴戝叧鏈轰篃鑳借繍琛?"""

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


# 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€ 閰嶇疆 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€

# RSS 鏂伴椈婧愬垪琛紙鑻辨枃涓轰富锛岃鐩栨缇庝富瑕?AI 濯掍綋锛?RSS_SOURCES_EN = [
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml",
    "https://venturebeat.com/category/ai/feed/",
    "https://feeds.feedburner.com/venturebeat/SZYF",
    "https://www.artificialintelligence-news.com/feed/",
]

# 涓枃 AI 濯掍綋 RSS
RSS_SOURCES_CN = [
    "https://www.jiqizhixin.com/rss",
    "https://www.qbitai.com/feed",
]

# NewsAPI 閰嶇疆锛堝彲閫夛紝鍏嶈垂 100 娆?澶╋級
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_API_URL = "https://newsapi.org/v2/everything"

# Gemini 閰嶇疆
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# PushPlus 閰嶇疆
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
PUSHPLUS_URL = "http://www.pushplus.plus/send"


def fetch_rss_articles(sources, max_per_source=10):
    """浠?RSS 婧愯幏鍙栨渶杩?24 灏忔椂鐨勬枃绔?""
    articles = []
    cutoff = datetime.now() - timedelta(hours=48)  # 48h 瀹藉绐楀彛

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
    """浠?NewsAPI 鑾峰彇 AI 鐩稿叧鏂伴椈锛堥渶瑕?API key锛?""
    if not NEWS_API_KEY:
        return []

    articles = []
    queries = [
        "AI artificial intelligence breakthrough",
        "large language model release",
        "AI regulation EU US",
        "涓浗 浜哄伐鏅鸿兘 绐佺牬",
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
    """鍘婚噸 + 闄愬埗鎬绘暟閬垮厤 token 杩囬暱"""
    seen = set()
    unique = []
    for a in articles:
        key = a["title"][:80]
        if key not in seen:
            seen.add(key)
            unique.append(a)
    # 鍙栨渶杩?60 鏉＄粰 Gemini 绛涢€?    return unique[:60]


def build_prompt(articles):
    """鏋勫缓鍙戠粰 Gemini 鐨?prompt"""
    news_text = ""
    for i, a in enumerate(articles):
        news_text += f"\n[{i+1}] {a['title']}\n  鎽樿: {a['summary'][:200]}\n  鏉ユ簮: {a['source']}\n  閾炬帴: {a['link']}\n"

    today = datetime.now().strftime("%Y骞?m鏈?d鏃?)

    return f"""浣犳槸涓€浣嶈祫娣?AI 琛屼笟鍒嗘瀽甯堛€傝浠庝互涓嬭繎 48 灏忔椂鐨?AI 鐩稿叧鏂伴椈涓紝绛涢€夊嚭鍏锋湁"杈冨ぇ绐佺牬鎬?鐨勬柊闂伙紝骞朵互涓枃鏃ユ姤鏍煎紡杈撳嚭銆?
## 绛涢€夋爣鍑嗭紙浠呴€夌湡姝ｉ噸瑕佺殑锛?
蹇呴』灞炰簬浠ヤ笅绫诲瀷涔嬩竴锛屽惁鍒欎笉瑕佹敹褰曪細
- 澶фā鍨?LLM 閲嶅ぇ鐗堟湰鍙戝竷鎴栬兘鍔涜穬鍗囷紙濡?GPT 绾уぇ鐗堟湰銆佹柊鏋舵瀯锛?- AI 鏀跨瓥娉曡閲嶅ぇ杞姌锛堟鐩?AI 娉曟銆佺編鍥?涓浗閲嶅ぇ鐩戠鍔ㄤ綔锛?- AI 棰嗗煙閲嶅ぇ铻嶈祫/骞惰喘锛堜嚎缇庡厓绾у埆鎴栬涓氭爣鏉嗭級
- AI 鎶€鏈湡姝ｇ殑鍓嶆部绐佺牬锛堟柊绠楁硶銆佹柊鑼冨紡銆丼OTA 鍒锋柊锛?- AI 琛屼笟鏍煎眬鎬т簨浠讹紙澶у叕鍙告垬鐣ヨ浆鍨嬨€侀噸澶у悎浣?鎷嗗垎锛?- AI 瀹夊叏/瀵归綈棰嗗煙鐨勯噸澶ц繘灞曟垨璀︾ず

## 鎺掗櫎鏍囧噯
涓嶈鏀跺綍浠ヤ笅鍐呭锛?- 甯歌浜у搧灏忔洿鏂般€佸皬鍔熻兘杩唬
- 鏅€氬悎浣?鎶曡祫锛堥潪鎴樼暐鎬э級
- 缂轰箯瀹炶川鍐呭鐨勮涓氳瘎璁?- 宸茬煡淇℃伅鐨勯噸澶嶆姤閬?- 妯＄硦鐨勯娴嬫垨鐚滄祴鎬у唴瀹?
## 杈撳嚭鏍煎紡锛堜弗鏍奸伒瀹堬級

---
馃實 **鍏ㄧ悆AI閲嶅ぇ鏂伴椈鏃ユ姤** | {today}

馃嚭馃嚫馃嚜馃嚭 **娆х編瑕侀椈**

**鏂伴椈鏍囬1**
绠€瑕佽鏄庯紙1-2鍙ワ級锛屾潵婧愶細鏉ユ簮鍚?
**鏂伴椈鏍囬2**
绠€瑕佽鏄庯紙1-2鍙ワ級锛屾潵婧愶細鏉ユ簮鍚?
馃嚚馃嚦 **涓浗瑕侀椈**

**鏂伴椈鏍囬1**
绠€瑕佽鏄庯紙1-2鍙ワ級锛屾潵婧愶細鏉ユ簮鍚?
馃挕 **浠婃棩娲炲療**锛?-2鍙ヨ瘽鎬荤粨浠婃棩鍏ㄧ悆AI棰嗗煙鏈€鍊煎緱鍏虫敞鐨勮秼鍔挎垨淇″彿銆?
---

## 瑕佹眰
- 瀹佺己姣嬫互锛屽鏋滄煇鍖哄煙娌℃湁鐪熸绐佺牬鎬ф柊闂伙紝鍙互娉ㄦ槑"浠婃棩鏃犻噸澶ф柊闂?
- 鎬绘潯鏁版帶鍒跺湪 4-8 鏉?- 鏍囬浣跨敤涓枃锛岃娓呮鏍稿績绐佺牬鐐?- 姣忔潯淇濈暀鍘熸枃閾炬帴

浠ヤ笅鏄緟绛涢€夌殑鏂伴椈锛?{news_text}
"""


def generate_report(prompt):
    """璋冪敤 Gemini 鐢熸垚鏃ユ姤"""
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
    """閫氳繃 PushPlus 鎺ㄩ€佸埌寰俊"""
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
    """濡傛灉 Gemini 涓嶅彲鐢紝鐢熸垚绠€鏄撶増鎶ュ憡"""
    today = datetime.now().strftime("%Y骞?m鏈?d鏃?)
    lines = [
        f"---",
        f"馃實 **鍏ㄧ悆AI閲嶅ぇ鏂伴椈鏃ユ姤** | {today}",
        f"",
        f"鈿狅笍 AI 鎬荤粨鏈嶅姟鏆傛椂涓嶅彲鐢紝浠ヤ笅鏄繎24灏忔椂AI鐩稿叧鏂伴椈鍒楄〃锛?,
        f"",
    ]

    for a in articles[:8]:
        source_label = f"鏉ユ簮锛歿a['source']}"
        lines.append(f"**{a['title']}**")
        lines.append(f"{source_label}")
        lines.append(f"[闃呰鍘熸枃]({a['link']})")
        lines.append("")

    lines.append(f"馃挕 璇风瓑寰呬笅娆¤幏鍙?AI 鎬荤粨鐗堛€?)
    lines.append(f"---")

    return "\n".join(lines)


def main():
    print(f"[{datetime.now()}] Starting AI News Daily...")

    # 1. 鏀堕泦鏂伴椈
    print("[Step 1] Fetching news from RSS...")
    articles = fetch_rss_articles(RSS_SOURCES_EN + RSS_SOURCES_CN)

    if NEWS_API_KEY:
        print("[Step 1b] Fetching news from NewsAPI...")
        articles += fetch_newsapi_articles()

    print(f"[Step 1] Collected {len(articles)} articles total")

    if not articles:
        print("[Step 1] No articles found, exiting")
        return

    # 2. 鍘婚噸
    articles = filter_articles(articles)
    print(f"[Step 2] {len(articles)} unique articles after dedup")

    # 3. AI 鎬荤粨
    if GEMINI_API_KEY:
        print("[Step 3] Generating report with Gemini...")
        prompt = build_prompt(articles)
        report = generate_report(prompt)
        if report:
            print("[Step 3] Report generated 鉁?)
            # 鍙繚鐣欎粠绗竴涓?--- 寮€濮嬬殑鍐呭
            idx = report.find("---")
            if idx >= 0:
                report = report[idx:]
        else:
            print("[Step 3] Gemini failed, using fallback")
            report = fallback_report(articles)
    else:
        print("[Step 3] No Gemini API key, using fallback")
        report = fallback_report(articles)

    # 4. 鎺ㄩ€佸井淇?    title = f"AI 鏃ユ姤 {datetime.now().strftime('%Y-%m-%d')}"
    success = push_to_wechat(title, report)

    # 5. 杈撳嚭缁撴灉
    print("=" * 50)
    print(report)
    print("=" * 50)
    print(f"[Done] Push {'success' if success else 'failed'}")

    if not success and PUSHPLUS_TOKEN:
        sys.exit(1)


if __name__ == "__main__":
    main()
