#!/usr/bin/env python3
"""
Financial Monitor - Low-cost financial signal generator
Uses free APIs: CoinGecko, Binance, Alpha Vantage
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional

class FinancialMonitor:
    """Financial signal monitor using free APIs"""

    def __init__(self):
        self.cache = {}
        self.cache_ttl = 60  # 60 seconds

    def get_crypto_price(self, symbols: List[str]) -> Dict:
        """Get crypto prices from CoinGecko (no API key needed)"""
        ids = ",".join(symbols)
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd,cny"

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def get_binance_price(self, symbol: str) -> Dict:
        """Get price from Binance (no API key needed)"""
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e)}

    def check_arbitrage(self, symbol: str = "BTCUSDT") -> Dict:
        """Check price across exchanges for arbitrage opportunities"""
        binance = self.get_binance_price(symbol)

        # CoinGecko aggregate price
        crypto_map = {
            "BTCUSDT": "bitcoin",
            "ETHUSDT": "ethereum"
        }
        coingecko = self.get_crypto_price([crypto_map.get(symbol, "bitcoin")])

        if "error" in binance or "error" in coingecko:
            return {"error": "API error"}

        binance_price = float(binance.get("price", 0))
        cg_id = crypto_map.get(symbol, "bitcoin")
        cg_price = coingecko.get(cg_id, {}).get("usd", 0)

        diff_percent = ((cg_price - binance_price) / binance_price) * 100 if binance_price > 0 else 0

        return {
            "symbol": symbol,
            "binance": binance_price,
            "coingecko_avg": cg_price,
            "diff_percent": round(diff_percent, 2),
            "arbitrage": abs(diff_percent) > 1  # 1% threshold
        }

    def price_alert(self, symbol: str, condition: str) -> Dict:
        """Check if price meets alert condition"""
        # Simple condition parser: "AAPL > 150" or "BTC < 40000"
        parts = condition.split()
        if len(parts) != 3:
            return {"error": "Invalid condition. Use: SYMBOL > < VALUE"}

        sym, op, val = parts
        val = float(val)

        if sym in ["BTC", "ETH"]:
            prices = self.get_crypto_price(["bitcoin" if sym == "BTC" else "ethereum"])
            key = "bitcoin" if sym == "BTC" else "ethereum"
            current = prices.get(key, {}).get("usd", 0)
        else:
            # Would need Alpha Vantage for stocks
            return {"error": f"Stock monitoring requires Alpha Vantage API key"}

        triggered = False
        if op == ">":
            triggered = current > val
        elif op == "<":
            triggered = current < val

        return {
            "symbol": sym,
            "current": current,
            "condition": condition,
            "triggered": triggered,
            "timestamp": datetime.now().isoformat()
        }

def main():
    """CLI interface"""
    monitor = FinancialMonitor()

    if len(sys.argv) < 2:
        print("Usage: python monitor.py [price|arbitrage|alert] [args...]")
        print("Examples:")
        print("  python monitor.py price BTC ETH")
        print("  python monitor.py arbitrage BTCUSDT")
        print("  python monitor.py alert BTC < 40000")
        sys.exit(1)

    command = sys.argv[1]

    if command == "price":
        symbols = sys.argv[2:] if len(sys.argv) > 2 else ["bitcoin", "ethereum"]
        # Convert common symbols
        symbol_map = {"BTC": "bitcoin", "ETH": "ethereum"}
        symbols = [symbol_map.get(s, s) for s in symbols]
        result = monitor.get_crypto_price(symbols)

    elif command == "arbitrage":
        symbol = sys.argv[2] if len(sys.argv) > 2 else "BTCUSDT"
        result = monitor.check_arbitrage(symbol)

    elif command == "alert":
        if len(sys.argv) < 4:
            print("Usage: python monitor.py alert SYMBOL < | > VALUE")
            sys.exit(1)
        symbol = sys.argv[2]
        condition = f"{symbol} {sys.argv[3]} {sys.argv[4]}"
        result = monitor.price_alert(symbol, condition)

    else:
        result = {"error": f"Unknown command: {command}"}

    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
