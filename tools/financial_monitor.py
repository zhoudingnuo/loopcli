#!/usr/bin/env python3
"""
Financial Monitor - 成本优化的金融监控工具
免费 API，最小 token 消耗
"""
import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: requests not installed. Run: pip install requests")
    sys.exit(1)


# 免费数据源
class FreeDataSources:
    """免费金融数据源（无需 API key）"""

    @staticmethod
    def get_crypto_price(coin: str, currency: str = "usd") -> Optional[float]:
        """CoinGecko API - 免费，无限制"""
        try:
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": coin.lower(), "vs_currencies": currency.lower()}
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            return data.get(coin.lower(), {}).get(currency.lower())
        except Exception as e:
            print(f"Error fetching crypto price: {e}")
            return None

    @staticmethod
    def get_binance_price(symbol: str) -> Optional[float]:
        """Binance Public API - 免费，无需 key"""
        try:
            url = "https://api.binance.com/api/v3/ticker/price"
            params = {"symbol": symbol.upper()}
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            return float(data.get("price"))
        except Exception as e:
            print(f"Error fetching binance price: {e}")
            return None

    @staticmethod
    def get_exchange_rate(from_curr: str, to_curr: str = "usd") -> Optional[float]:
        """ExchangeRate-API - 免费，有速率限制"""
        try:
            url = f"https://api.exchangerate-api.com/v4/latest/{from_curr.upper()}"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()
            return data.get("rates", {}).get(to_curr.upper())
        except Exception as e:
            print(f"Error fetching exchange rate: {e}")
            return None


# 价格缓存（减少 API 调用）
_price_cache: Dict[str, tuple] = {}  # key -> (price, timestamp)


def get_cached_price(source_func: callable, cache_key: str, ttl: int = 60, *args, **kwargs) -> Optional[float]:
    """获取缓存价格（TTL 秒）"""
    now = time.time()
    if cache_key in _price_cache:
        price, ts = _price_cache[cache_key]
        if now - ts < ttl:
            return price
    price = source_func(*args, **kwargs)
    if price is not None:
        _price_cache[cache_key] = (price, now)
    return price


# CLI 接口
def cmd_price(args):
    """查询价格"""
    if args.source == "coingecko":
        price = get_cached_price(FreeDataSources.get_crypto_price, f"cg_{args.asset}", 60, args.asset, args.currency)
    elif args.source == "binance":
        price = get_cached_price(FreeDataSources.get_binance_price, f"bn_{args.asset}", 60, args.asset)
    elif args.source == "forex":
        price = get_cached_price(FreeDataSources.get_exchange_rate, f"fx_{args.asset}", 3600, args.asset, args.currency)
    else:
        print(f"Unknown source: {args.source}")
        return

    if price is not None:
        print(f"{args.asset.upper()} = {price} {args.currency.upper()}")
        return price
    else:
        print(f"Failed to fetch price for {args.asset}")
        return None


def cmd_monitor(args):
    """监控价格（简单实现，无告警）"""
    print(f"Monitoring {', '.join(args.assets)} (Ctrl+C to stop)...")
    try:
        while True:
            prices = {}
            for asset in args.assets:
                if args.source == "coingecko":
                    price = FreeDataSources.get_crypto_price(asset, args.currency)
                elif args.source == "binance":
                    price = FreeDataSources.get_binance_price(asset)
                elif args.source == "forex":
                    price = FreeDataSources.get_exchange_rate(asset, args.currency)
                else:
                    continue
                if price is not None:
                    prices[asset] = price
            if prices:
                ts = datetime.now().strftime("%H:%M:%S")
                line = f"[{ts}] " + " | ".join(f"{a.upper()}={p}" for a, p in prices.items())
                print(line)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


def main():
    parser = argparse.ArgumentParser(description="Financial Monitor - 成本优化的金融监控工具")
    sub = parser.add_subparsers(dest="command", help="可用命令")

    # price 命令
    p_price = sub.add_parser("price", help="查询价格")
    p_price.add_argument("asset", help="资产代码（如 BTC, ETH）")
    p_price.add_argument("--currency", "-c", default="usd", help="计价货币（默认 usd）")
    p_price.add_argument("--source", "-s", default="coingecko", choices=["coingecko", "binance", "forex"], help="数据源")

    # monitor 命令
    p_monitor = sub.add_parser("monitor", help="监控价格")
    p_monitor.add_argument("assets", nargs="+", help="资产列表")
    p_monitor.add_argument("--currency", "-c", default="usd", help="计价货币")
    p_monitor.add_argument("--source", "-s", default="coingecko", choices=["coingecko", "binance", "forex"], help="数据源")
    p_monitor.add_argument("--interval", "-i", type=int, default=60, help="刷新间隔（秒）")

    args = parser.parse_args()

    if args.command == "price":
        cmd_price(args)
    elif args.command == "monitor":
        cmd_monitor(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
