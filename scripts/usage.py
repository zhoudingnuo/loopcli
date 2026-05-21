#!/usr/bin/env python3
"""查询 GLM Coding Plan 用量。用法：python usage.py"""
import os, json, urllib.request, urllib.parse
from datetime import datetime, timedelta

BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "")
TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")

if not BASE_URL or not TOKEN:
    print("请设置 ANTHROPIC_BASE_URL 和 ANTHROPIC_AUTH_TOKEN")
    exit(1)

from urllib.parse import urlparse
parsed = urlparse(BASE_URL)
DOMAIN = f"{parsed.scheme}://{parsed.netloc}"

now = datetime.now()
start = (now - timedelta(days=1)).strftime("%Y-%m-%d %H:00:00")
end = now.strftime("%Y-%m-%d %H:59:59")
params = f"?startTime={urllib.parse.quote(start)}&endTime={urllib.parse.quote(end)}"

HEADERS = {"Authorization": TOKEN, "Content-Type": "application/json"}

def query(path, use_params=True):
    url = DOMAIN + path + (params if use_params else "")
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get("data", {})

print(f"时段: {start} ~ {end}\n")

# ── 模型用量 ──
model = query("/api/monitor/usage/model-usage")
summary = model.get("totalUsage", {})
print(f"总调用: {summary.get('totalModelCallCount', 0):,} 次")
print(f"总 Token: {summary.get('totalTokensUsage', 0):,}")
for m in summary.get("modelSummaryList", []):
    print(f"  {m['modelName']}: {m['totalTokens']:,} tokens")

# ── 工具用量 ──
tool = query("/api/monitor/usage/tool-usage")
tsummary = tool.get("totalUsage", {})
print(f"\n搜索: {tsummary.get('totalNetworkSearchCount', 0)} 次")
print(f"网页读取: {tsummary.get('totalWebReadMcpCount', 0)} 次")
for t in tsummary.get("toolSummaryList", []):
    print(f"  {t.get('toolCode','?')}: {t.get('totalUsageCount',0)} 次")

# ── 配额 ──
quota = query("/api/monitor/usage/quota/limit", use_params=False)
for item in quota.get("limits", []):
    t, pct = item.get("type", "?"), item.get("percentage", 0)
    if "TOKEN" in t:
        print(f"\nToken 配额 (5h): {pct:.1f}%")
    elif "TIME" in t:
        cur = item.get("currentValue", 0)
        total = item.get("usage", "?")
        print(f"MCP 配额 (月): {pct:.1f}% ({cur}/{total} 分钟)")
