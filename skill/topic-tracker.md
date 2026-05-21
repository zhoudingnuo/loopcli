# Skill: Topic Tracker

自动追踪热点话题，为内容生成提供数据源。

## 功能

- **Hacker News** - 免费API获取top stories
- **自动评分** - 按热度、评论数、关键词评分
- **本地缓存** - 避免重复请求，节省成本

## 用法

```bash
cd D:/loopcli/content-generator && python topic_tracker.py
```

## 输出

- 数据保存到 `content-generator/memory/cache/topics.json`
- 包含top_pick（最高分话题）
- 所有话题按评分排序

## 成本

- 零成本（使用免费API）
- 无token消耗

## 价值

- 为内容生成提供热点话题
- 自动发现高价值写作主题
- 可扩展到Reddit、GitHub Trending
