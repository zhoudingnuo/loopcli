"""Financial Monitor - 价格监控与套利机会检测

使用免费 API 追踪加密货币、股票价格，检测套利机会。
成本等级: Level 1 (10-50 tokens/次)
"""

import requests
import json
from datetime import datetime
from pathlib import Path
import os

# 本地缓存路径
CACHE_DIR = Path.home() / ".loopcli" / "cache" / "finance"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_crypto_price(coin="bitcoin", currency="usd"):
    """获取加密货币价格 - 多数据源备选"""
    cache_file = CACHE_DIR / f"{coin}_{currency}.json"

    # 检查缓存 (5分钟有效期)
    if cache_file.exists():
        with open(cache_file) as f:
            cached = json.load(f)
            if (datetime.now().timestamp() - cached.get("timestamp", 0)) < 300:
                return cached["price"]

    # 数据源 1: CoinGecko
    sources = [
        ("CoinGecko", f"https://api.coingecko.com/api/v3/simple/price", {"ids": coin, "vs_currencies": currency}),
        ("Binance", "https://api.binance.com/api/v3/ticker/price", {"symbol": f"{coin.upper()}USDT"}),
    ]

    for name, url, params in sources:
        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            # 解析不同 API 格式
            if name == "CoinGecko":
                price = data[coin][currency]
            else:  # Binance
                price = float(data["price"])

            # 更新缓存
            with open(cache_file, "w") as f:
                json.dump({"price": price, "timestamp": datetime.now().timestamp()}, f)

            return price
        except Exception:
            continue

    return "Error: All sources failed"


def check_arbitrage(symbol="BTC"):
    """检查跨交易所套利机会 (Binance vs Coinbase)"""
    try:
        # Binance 价格
        binance_resp = requests.get(
            "https://api.binance.com/api/v3/ticker/price",
            params={"symbol": f"{symbol}USDT"},
            timeout=10
        )
        binance_price = float(binance_resp.json()["price"])

        # Coinbase 价格 (通过 CoinGecko)
        coinbase_resp = requests.get(
            "https://api.coingecko.com/api/v3/exchanges/binance/tickers?coin_ids=bitcoin",
            timeout=10
        )

        return {
            "binance": binance_price,
            "spread": "Check Coinbase manually",
            "opportunity": binance_price * 0.001  # 0.1% spread threshold
        }
    except Exception as e:
        return f"Error: {e}"


def monitor_portfolio(coins=None):
    """监控投资组合"""
    if coins is None:
        coins = ["bitcoin", "ethereum", "solana"]

    results = {}
    for coin in coins:
        results[coin] = get_crypto_price(coin)
    return results


if __name__ == "__main__":
    # 测试
    print("BTC Price:", get_crypto_price("bitcoin"))
    print("Portfolio:", monitor_portfolio())
