# Financial Monitor - 金融监控技能

## 价值方向

- **价格监控** - 股票、加密货币、商品实时价格追踪
- **套利机会** - 跨交易所价差监控
- **止损止盈** - 自动触发价格告警
- **投资组合** - 资产净值实时计算
- **趋势分析** - 技术指标、市场情绪

## 成本等级

1. **Level 1 (10-50 tokens)**: 单次价格查询
2. **Level 2 (50-200 tokens)**: 技术指标计算
3. **Level 3 (200-1000 tokens)**: 多资产组合分析

## 免费数据源

- **股票**: Yahoo Finance API、Alpha Vantage (免费额度)
- **加密货币**: CoinGecko API、Binance Public API
- **商品**: Metals-API (免费层)
- **汇率**: ExchangeRate-API

## 用法

```bash
loopcli finance-price BTC --currency USD
loopcli finance-monitor AAPL BTC --alert "AAPL < 150" --interval 300
loopcli finance-portfolio --file portfolio.json
```

## Alert 示例

- 价格突破: `AAPL > 200`
- 止损: `BTC < 40000`
- 涨跌幅: `ETH change > 5%`
- 套利: `binance_BTC - coinbase_BTC > 100`

## 技术实现

```python
# CoinGecko (免费，无 API key)
requests.get('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')

# Yahoo Finance (需 yfinance 库)
import yfinance as yf
ticker = yf.Ticker('AAPL')
ticker.history(period='1d')['Close'].iloc[-1]

# Binance Public (免费)
requests.get('https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT')
```

## 最佳实践

- **频率控制** - 免费 API 有速率限制
- **本地缓存** - 减少重复请求
- **批量查询** - 一次 API 调用获取多个数据
- **异步监控** - 不阻塞主线程

## 禁止

- 禁止高频交易（需要付费 API）
- 禁止绕过 API 限制
- 禁止内幕交易
- 禁止无风险对冲（需要专业账户）

## 价值

- **及时止损** - 避免大幅亏损
- **捕获机会** - 短暂价格窗口
- **被动收入** - 自动化套利
- **数据资产** - 积累历史数据训练模型
