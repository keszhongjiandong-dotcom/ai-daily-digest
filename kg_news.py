#!/usr/bin/env python3
"""
吉尔吉斯斯坦新闻聚合器 - 使用 DeepSeek AI 分析
采集自 Kabar.kg, 24.kg, AKIpress 等吉尔吉斯新闻源
"""

import os
import json
import requests
import feedparser
from datetime import datetime
from openai import OpenAI

# 吉尔吉斯新闻源配置
NEWS_SOURCES = [
    {
        "name": "Kabar.kg (吉尔吉斯官方通讯社)",
        "url": "https://kabar.kg/rss/",
        "lang": "ru"
    },
    {
        "name": "24.kg",
        "url": "https://24.kg/rss.xml",
        "lang": "ru"
    },
    {
        "name": "AKIpress",
        "url": "https://akipress.com/rss/rss_news.php",
        "lang": "ru"
    },
    {
        "name": "VB.KG",
        "url": "https://vb.kg/rss",
        "lang": "ru"
    },
    {
        "name": "Kaktus.media",
        "url": "https://kaktus.media/rss/all",
        "lang": "ru"
    }
]

def fetch_all_news():
    """从所有源抓取最新新闻"""
    all_articles = []
    for source in NEWS_SOURCES:
        try:
            print(f"📡 正在抓取: {source['name']}")
            feed = feedparser.parse(source["url"])
            for entry in feed.entries[:8]:  # 每个源取前8条
                article = {
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": entry.get("published", ""),
                    "source": source["name"]
                }
                all_articles.append(article)
            print(f"   ✓ 抓取到 {len(feed.entries[:8])} 条新闻")
        except Exception as e:
            print(f"   ✗ 抓取失败: {e}")
    return all_articles

def ai_summarize(articles, api_key):
    """使用 DeepSeek API 生成中文新闻摘要"""
    if not api_key:
        print("❌ 未找到 API_KEY")
        return None
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"
    )
    
    # 构建新闻列表
    news_text = ""
    for i, article in enumerate(articles[:20]):  # 最多20条
        news_text += f"{i+1}. {article['title']}\n   来源: {article['source']}\n   链接: {article['link']}\n\n"
    
    prompt = f"""你是一个专业的新闻分析师。以下是吉尔吉斯斯坦今天的新闻列表，请用中文完成：

1. 筛选出最重要的5-8条新闻
2. 为每条新闻写出一句话摘要（简洁、抓住重点）
3. 最后写一段"今日观察"，概括吉尔吉斯斯坦今天的主要动态（100字左右）

新闻列表：
{news_text}

请用以下格式输出：

## 📰 今日要闻

### 1. [新闻标题]
摘要：[一句话摘要]
🔗 [原文链接]

### 2. [新闻标题]
...

## 📊 今日观察
[你的分析]
"""
    
    try:
        print("🤖 正在调用 DeepSeek AI 分析新闻...")
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ AI 分析失败: {e}")
        return None

def save_report(articles, summary):
    """保存日报"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 确保目录存在
    os.makedirs("daily", exist_ok=True)
    
    # 生成 Markdown 内容
    content = f"# 🇰🇬 吉尔吉斯斯坦新闻日报 - {today}\n\n"
    
    if summary:
        content += summary
    else:
        content += "## ⚠️ AI 分析暂不可用，以下是原始新闻列表\n\n"
        for article in articles[:15]:
            content += f"### {article['title']}\n"
            content += f"**来源**: {article['source']}\n"
            content += f"[阅读全文]({article['link']})\n\n"
    
    # 保存文件
    filepath = f"daily/{today}.md"
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"✅ 日报已保存: {filepath}")
    return filepath

def main():
    print("🚀 吉尔吉斯新闻聚合器启动")
    print("=" * 40)
    
    # 获取 API Key - 直接读取 API_KEY
    api_key = os.getenv("API_KEY")
    
    if not api_key:
        print("⚠️ 警告: 未找到 API_KEY 环境变量")
        print("请在 GitHub Secrets 中配置 API_KEY")
    else:
        print("✓ 已找到 API_KEY")
    
    # 抓取新闻
    articles = fetch_all_news()
    print(f"\n📊 共抓取到 {len(articles)} 条新闻")
    
    if not articles:
        print("❌ 没有抓取到任何新闻，请检查网络或新闻源")
        return
    
    # AI 分析
    summary = None
    if api_key:
        summary = ai_summarize(articles, api_key)
    else:
        print("⚠️ 未配置 API_KEY，跳过 AI 分析")
    
    # 保存报告
    save_report(articles, summary)
    print("\n✨ 完成！")

if __name__ == "__main__":
    main()
