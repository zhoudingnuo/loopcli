# Web Scraper - Web抓取技能

## 价值方向

- **市场数据** - 采集价格、库存、评分等实时数据
- **竞品分析** - 监控竞争对手的定价、产品、活动
- **趋势追踪** - 追踪关键词、话题热度变化
- **内容积累** - 构建自有数据集训练 AI

## 成本等级

1. **Level 1 (10-100 tokens)**: 静态页面，已知 HTML 结构
2. **Level 2 (100-500 tokens)**: 动态内容，需要 JS 渲染
3. **Level 3 (500-2000 tokens)**: 反爬虫对抗，登录验证

## 技术栈（按成本排序）

1. **requests + BeautifulSoup4** - 静态页面（BS4 51k+ stars）
2. **playwright** - 动态页面，支持 JS（71k+ stars）
3. **scrapy** - 大规模分布式爬虫（53k+ stars）

## 免费数据源

- **电商**: Amazon、eBay、AliExpress（商品价格、评论）
- **新闻**: Google News、Hacker News（热点追踪）
- **社交**: Reddit、Twitter（趋势话题）
- **金融**: Yahoo Finance、CoinGecko（价格数据）

## 用法

```bash
loopcli scrape <url> --selector "css.selector"
loopcli scrape-monitor <url> --interval 3600 --alert "price < 100"
loopcli scrape-list <file.txt> --output results.json
```

## 最佳实践

- **频率控制** - 默认 1 req/sec，避免被封
- **User Agent 轮换** - 模拟真实浏览器
- **代理支持** - 分布式抓取
- **增量更新** - 只抓取变化部分

## 禁止

- 禁止绕过付费墙
- 禁止抓取个人隐私数据
- 禁止违反 robots.txt
- 禁止商业用途未经授权的数据

## 价值

- **价格监控** - 自动追踪竞品价格变化
- **库存告警** - 热门商品到货通知
- **数据产品** - 销售清洗后的数据集
- **趋势分析** - 提前发现市场机会