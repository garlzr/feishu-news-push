#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
feishu_news_push.py - 飞书新闻推送工具
直接调用各新闻源API，无需本地服务

用法:
    python feishu_news_push.py <source_id> [count]

示例:
    python feishu_news_push.py weibo 15
    python feishu_news_push.py hupu
    python feishu_news_push.py zhihu 10
"""

import argparse
import json
import re
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# 默认Headers
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.google.com",
}

# 微博热搜API
WEIBO_API = "https://weibo.com/ajax/side/hotSearch"

# 知乎热榜API
ZHIHU_API = "https://api.zhihu.com/top-story/hot-list"

# 百度热搜API  
BAIDU_API = "https://top.baidu.com/api?get=home"

# 虎扑帖子API
HUPU_API = "https://bbs.hupu.com/topic-daily-hot"

# IT之家API
ITHOME_API = "https://www.ithome.com/api/news/getNews"


def fetch_weibo(limit: int = 15) -> List[Dict]:
    """获取微博热搜"""
    try:
        req = Request(WEIBO_API, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        items = []
        realtime = data.get("data", {}).get("realtime", [])
        for item in realtime[:limit]:
            items.append({
                "title": item.get("word", ""),
                "url": f"https://s.weibo.com/weibo?q={quote(item.get('word', ''))}",
                "hot": item.get("raw_hot", "")
            })
        return items
    except Exception as e:
        print(f"[微博] 获取失败: {e}")
        return []


def fetch_zhihu(limit: int = 15) -> List[Dict]:
    """获取知乎热榜"""
    try:
        req = Request(ZHIHU_API, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        items = []
        for item in data.get("data", [])[:limit]:
            target = item.get("target", {})
            items.append({
                "title": target.get("title", ""),
                "url": f"https://www.zhihu.com/question/{target.get('id', '')}",
                "hot": target.get("detail_text", "")
            })
        return items
    except Exception as e:
        print(f"[知乎] 获取失败: {e}")
        return []


def fetch_baidu(limit: int = 15) -> List[Dict]:
    """获取百度热搜"""
    try:
        req = Request(BAIDU_API, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        items = []
        for item in data.get("data", {}).get("bangList", [])[:limit]:
            items.append({
                "title": item.get("query", ""),
                "url": f"https://www.baidu.com/s?wd={quote(item.get('query', ''))}",
                "hot": item.get("hotScore", "")
            })
        return items
    except Exception as e:
        print(f"[百度] 获取失败: {e}")
        return []


def fetch_hupu(limit: int = 15) -> List[Dict]:
    """获取虎扑热帖"""
    try:
        req = Request(HUPU_API, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        
        items = []
        # 解析虎扑HTML
        pattern = re.compile(r'<a href="(/[^"]+\.html)"[^>]*?class="p-title"[^>]*>([^<]+)</a>')
        for match in pattern.finditer(html):
            path, title = match.groups()
            items.append({
                "title": title.strip(),
                "url": f"https://bbs.hupu.com{path}",
                "hot": ""
            })
            if len(items) >= limit:
                break
        
        # 如果解析失败，尝试备用方法
        if not items:
            pattern2 = re.compile(r'title">([^<]+)</[^>]+><a href="([^"]+)"')
            for match in pattern2.finditer(html):
                title, path = match.groups()
                items.append({
                    "title": title.strip(),
                    "url": f"https://bbs.hupu.com{path}" if path.startswith("/") else path,
                    "hot": ""
                })
                if len(items) >= limit:
                    break
        
        return items
    except Exception as e:
        print(f"[虎扑] 获取失败: {e}")
        return []


def fetch_ithome(limit: int = 15) -> List[Dict]:
    """获取IT之家"""
    try:
        req = Request(ITHOME_API, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        items = []
        for item in data.get("data", {}).get("news", [])[:limit]:
            items.append({
                "title": item.get("title", ""),
                "url": f"https://www.ithome.com/{item.get('id', '')}.htm",
                "hot": item.get("热度", "")
            })
        return items
    except Exception as e:
        print(f"[IT之家] 获取失败: {e}")
        return []


def fetch_36kr(limit: int = 15) -> List[Dict]:
    """获取36氪"""
    try:
        # 36氪需要登录，这里用RSS作为备选
        url = "https://36kr.com/feed"
        req = Request(url, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            import xml.etree.ElementTree as ET
            root = ET.parse(resp).getroot()
        
        items = []
        for item in root.findall(".//item")[:limit]:
            title = item.find("title")
            link = item.find("link")
            items.append({
                "title": title.text if title is not None else "",
                "url": link.text if link is not None else "",
                "hot": ""
            })
        return items
    except Exception as e:
        print(f"[36氪] 获取失败: {e}")
        return []


def fetch_wallstreetcn(limit: int = 15) -> List[Dict]:
    """获取华尔街见闻"""
    try:
        url = "https://wallstreetcn.com/"
        req = Request(url, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        
        items = []
        pattern = re.compile(r'<a href="/(post/\d+)"[^>]*?>([^<]+)<')
        for match in pattern.finditer(html):
            path, title = match.groups()
            items.append({
                "title": title.strip(),
                "url": f"https://wallstreetcn.com/{path}",
                "hot": ""
            })
            if len(items) >= limit:
                break
        return items
    except Exception as e:
        print(f"[华尔街见闻] 获取失败: {e}")
        return []


def fetch_hackernews(limit: int = 15) -> List[Dict]:
    """获取Hacker News"""
    try:
        # 获取Top Stories IDs
        ids_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        req = Request(ids_url, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            ids = json.loads(resp.read().decode("utf-8"))
        
        items = []
        for story_id in ids[:limit]:
            story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
            story_req = Request(story_url, headers=DEFAULT_HEADERS)
            with urlopen(story_req, timeout=10) as story_resp:
                story = json.loads(story_resp.read().decode("utf-8"))
            
            items.append({
                "title": story.get("title", ""),
                "url": story.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
                "hot": f"⬆️ {story.get('score', 0)}"
            })
        return items
    except Exception as e:
        print(f"[Hacker News] 获取失败: {e}")
        return []


def fetch_juejin(limit: int = 15) -> List[Dict]:
    """获取掘金热榜"""
    try:
        url = "https://api.juejin.cn/recommend_api/v1/article/hot_list"
        data = json.dumps({"cursor": "", "limit": limit, "tag_id": ""}).encode("utf-8")
        req = Request(url, data=data, headers={**DEFAULT_HEADERS, "Content-Type": "application/json"})
        with urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        
        items = []
        for item in result.get("data", []):
            article = item.get("article_info", {})
            items.append({
                "title": article.get("title", ""),
                "url": f"https://juejin.cn/post/{article.get('article_id', '')}",
                "hot": f"👍 {article.get('digg_count', 0)}"
            })
        return items
    except Exception as e:
        print(f"[掘金] 获取失败: {e}")
        return []


def fetch_sspai(limit: int = 15) -> List[Dict]:
    """获取少数派"""
    try:
        url = "https://sspai.com/api/v1/article/hot_list/get"
        req = Request(url, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        items = []
        for item in data.get("data", [])[:limit]:
            items.append({
                "title": item.get("title", ""),
                "url": f"https://sspai.com/post/{item.get('id', '')}",
                "hot": f"👍 {item.get('dig_count', 0)}"
            })
        return items
    except Exception as e:
        print(f"[少数派] 获取失败: {e}")
        return []


def fetch_douyin(limit: int = 15) -> List[Dict]:
    """获取抖音热搜"""
    try:
        url = "https://www.iesdouyin.com/web/api/v2/hot/search/broad/"
        req = Request(url, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        items = []
        for word in data.get("word_list", [])[:limit]:
            items.append({
                "title": word.get("word", ""),
                "url": f"https://www.douyin.com/search/{quote(word.get('word', ''))}",
                "hot": f"🔥 {word.get('hot_value', '')}"
            })
        return items
    except Exception as e:
        print(f"[抖音] 获取失败: {e}")
        return []


def fetch_bilibili(limit: int = 15) -> List[Dict]:
    """获取B站热搜"""
    try:
        url = "https://api.bilibili.com/x/web-interface/ranking/v2"
        req = Request(url, headers=DEFAULT_HEADERS)
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        
        items = []
        for item in data.get("data", {}).get("list", [])[:limit]:
            items.append({
                "title": item.get("title", ""),
                "url": f"https://www.bilibili.com/video/{item.get('bvid', '')}",
                "hot": f"▶️ {item.get('pts', 0)}"
            })
        return items
    except Exception as e:
        print(f"[B站] 获取失败: {e}")
        return []


# 新闻源映射表
NEWS_FETCHERS = {
    "weibo": ("微博热搜", fetch_weibo),
    "zhihu": ("知乎热榜", fetch_zhihu),
    "baidu": ("百度热搜", fetch_baidu),
    "hupu": ("虎扑热帖", fetch_hupu),
    "ithome": ("IT之家", fetch_ithome),
    "36kr": ("36氪", fetch_36kr),
    "wallstreetcn": ("华尔街见闻", fetch_wallstreetcn),
    "hackernews": ("Hacker News", fetch_hackernews),
    "juejin": ("稀土掘金", fetch_juejin),
    "sspai": ("少数派", fetch_sspai),
    "douyin": ("抖音热搜", fetch_douyin),
    "bilibili": ("B站热搜", fetch_bilibili),
}


def format_message(source_id: str, items: List[Dict], limit: int = 15) -> str:
    """格式化飞书消息"""
    if source_id not in NEWS_FETCHERS:
        return f"未知新闻源: {source_id}"
    
    name, _ = NEWS_FETCHERS[source_id]
    items = items[:limit]
    
    emoji = "🔥"
    lines = [f"{emoji} **{name} Top{len(items)}**\n"]
    
    for i, item in enumerate(items, 1):
        title = item.get("title", "无标题")
        url = item.get("url", "")
        hot = item.get("hot", "")
        
        if hot:
            line = f"{i}️⃣ [{title}]({url}) {hot}"
        else:
            line = f"{i}️⃣ [{title}]({url})"
        
        lines.append(line)
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="飞书新闻推送 - 直接获取各平台热搜",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
支持的平台:
  weibo      微博热搜
  zhihu      知乎热榜  
  baidu      百度热搜
  hupu       虎扑热帖
  ithome     IT之家
  36kr       36氪
  wallstreetcn  华尔街见闻
  hackernews Hacker News
  juejin     稀土掘金
  sspai      少数派
  douyin     抖音热搜
  bilibili   B站热搜

示例:
  python feishu_news_push.py weibo 15
  python feishu_news_push.py hupu
  python feishu_news_push.py zhihu 10
        """
    )
    parser.add_argument("source", help="新闻源ID，如 weibo, hupu, zhihu")
    parser.add_argument("limit", nargs="?", type=int, default=10, help="获取条数，默认10")
    
    args = parser.parse_args()
    
    if args.source not in NEWS_FETCHERS:
        print(f"未知新闻源: {args.source}")
        print(f"支持的平台: {', '.join(NEWS_FETCHERS.keys())}")
        sys.exit(1)
    
    name, fetcher = NEWS_FETCHERS[args.source]
    print(f"正在获取 {name}...")
    
    items = fetcher(args.limit)
    
    if not items:
        print("获取失败，请检查网络或稍后重试")
        sys.exit(1)
    
    message = format_message(args.source, items, args.limit)
    
    print("\n" + "=" * 50)
    print(message)
    print("=" * 50)
    
    # 输出JSON格式方便程序调用
    print("\n[JSON格式]")
    print(json.dumps({
        "source": args.source,
        "name": name,
        "items": items,
        "count": len(items)
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
