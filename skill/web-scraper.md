# Skill: Web Scraper

自动化网页数据采集，支持市场分析、趋势检测、内容生成数据源。

## 能力

- **静态页面抓取** - BeautifulSoup + requests（成本低，速度快）
- **动态页面抓取** - Playwright（处理JS渲染，成本中等）
- **AI智能提取** - ScrapeGraphAI（LLM驱动，成本高但智能）
- **数据清洗** - 自动去重、格式化、存储为JSON/CSV

## 成本等级

1. **Level 1 (100-500 tokens)**: 简单HTML解析，已知结构
2. **Level 2 (500-2000 tokens)**: 动态页面，需要JS执行
3. **Level 3 (2000-5000 tokens)**: AI智能提取，复杂非结构化数据

## 用法

```bash
loopcli scrape <URL> --level 1-3 --output json/csv
```

## 技术栈

- **低成本**: requests + BeautifulSoup4
- **中成本**: playwright-python
- **高智能**: scrapegraphai

## 禁止

- 禁止爬取需要登录的付费内容（侵犯版权）
- 禁止高频请求导致被封IP（添加限流）
- 禁止爬取个人隐私数据

## 价值

- **市场分析** - 抓取竞品价格、评论、趋势
- **内容生成** - 收集素材用于AI内容生成
- **趋势检测** - 监控热门话题、关键词排名
