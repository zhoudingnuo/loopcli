# API Automation - API自动化技能

## 价值方向

- **数据采集** - 从公开API获取市场数据、价格、趋势
- **服务集成** - 连接多个服务实现自动化流程
- **监控告警** - 定期检查API状态、价格变动、新内容
- **批量操作** - 高效处理大量API请求

## 成本等级

1. **Level 1 (10-100 tokens)**: 简单REST API调用，已知端点
2. **Level 2 (100-500 tokens)**: 需要认证、分页、数据清洗
3. **Level 3 (500-2000 tokens)**: 复杂GraphQL查询、错误处理、重试逻辑

## 技术栈（按成本排序）

1. **requests** - 最简单，同步IO
2. **aiohttp** - 异步IO，高并发（15k+ stars）
3. **httpx** - 现代HTTP客户端，支持HTTP/2

## 免费API资源

- **加密货币**: CoinGecko API（免费50 call/min）
- **天气**: OpenWeatherMap（免费1000 calls/day）
- **新闻**: NewsAPI（免费100 requests/day）
- **GitHub**: GitHub REST API（5000 requests/hour authenticated）

## 用法

```bash
loopcli api <endpoint> --method GET/POST --auth <token>
loopcli api-monitor <url> --interval 60 --alert <condition>
```

## 最佳实践

- **缓存优先** - 相同请求缓存结果，减少API调用
- **批量处理** - 合并多个请求为一次
- **错误重试** - 指数退避，避免被封
- **限流控制** - 尊重API速率限制

## 禁止

- 禁止无授权访问付费API
- 禁止高频请求导致IP被封
- 禁止存储敏感API密钥（使用环境变量）

## 价值

- **市场监控** - 自动追踪价格、趋势
- **内容同步** - 多平台内容自动分发
- **数据积累** - 构建自有数据集
