---
name: feishu-news-push
description: 查询新闻热点并通过飞书推送。当用户说"推送XX新闻"、"推送微博热搜"、"推送虎扑热帖"等时使用此技能。技能自带Python脚本直接调用各新闻源API，无需本地服务。
---

# feishu-news-push

直接获取各平台热搜，推送到飞书。**无需本地新闻服务**，纯API调用。

## 支持的新闻源

| 命令词 | source_id | 说明 |
|--------|-----------|------|
| 微博 | `weibo` | 实时热搜 |
| 知乎 | `zhihu` | 热榜 |
| 百度 | `baidu` | 热搜 |
| 虎扑 | `hupu` | 热帖 |
| IT之家 | `ithome` | 科技 |
| 36氪 | `36kr` | 科技 |
| 华尔街见闻 | `wallstreetcn` | 财经 |
| 抖音 | `douyin` | 热搜 |
| B站 | `bilibili` | 热搜 |
| 掘金 | `juejin` | 技术 |
| 少数派 | `sspai` | 高质量 |
| Hacker News | `hackernews` | 全球技术 |

## 执行流程

1. **识别新闻源**：根据用户需求确定 source_id
2. **直接调用API**：通过 Python urllib 直接请求新闻源
3. **解析数据**：提取标题、链接、热度值
4. **格式化消息**：拼接为飞书 Markdown
5. **发送飞书**：使用 message 工具发送

## 直接获取示例

```python
# 微博热搜
import urllib.request
import json

url = "https://weibo.com/ajax/side/hotSearch"
req = urllib.request.Request(url, headers={
    "User-Agent": "Mozilla/5.0 ..."
})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read())
    
for item in data["data"]["realtime"][:15]:
    print(item["word"])
```

## 消息格式

```markdown
🔥 **微博热搜 Top10**

1️⃣ [郑钦文毛巾事件](https://s.weibo.com/weibo?q=郑钦文) 🔥 856万
2️⃣ [美国袭击伊朗](https://s.weibo.com/weibo?q=美国袭击伊朗) 🔥 520万
...
```

## 命令行使用

```bash
python scripts/feishu_news_push.py weibo 15
python scripts/feishu_news_push.py hupu
python scripts/feishu_news_push.py zhihu 10
```

## 注意事项

- 纯 Python 标准库，无第三方依赖
- 直接调用新闻源API，无需本地服务
- 部分平台可能需要代理访问
- 获取失败时返回友好提示
