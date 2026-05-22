import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "main" / "webui"))
from loopcli_lib import read_json, write_json, LOOPCLI_ROOT

LOOPCLI_DIR = str(LOOPCLI_ROOT)
PRICING_FILE = os.path.join(LOOPCLI_DIR, "scripts", "pricing.json")
LAST_USAGE_FILE = os.path.join(LOOPCLI_DIR, "logs", ".last_usage.json")


def load_pricing():
    try:
        with open(PRICING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _get_api_creds():
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if base_url and token:
        return base_url, token
    env_file = os.path.join(LOOPCLI_DIR, ".env.json")
    if os.path.isfile(env_file):
        cfg = read_json(env_file, {})
        return cfg.get("ANTHROPIC_BASE_URL", ""), cfg.get("ANTHROPIC_AUTH_TOKEN", "")
    return "", ""


def query_model_usage(out_fn=None):
    try:
        base_url, token = _get_api_creds()
        if not base_url or not token:
            if out_fn:
                from .colors import C
                out_fn(f"  {C.YELLOW}⚠ 花费查询失败: 未设置 ANTHROPIC_BASE_URL 或 ANTHROPIC_AUTH_TOKEN{C.RST}")
            return None

        from urllib.parse import urlparse
        import urllib.parse, urllib.request
        from datetime import timedelta, datetime

        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        now = datetime.now()
        start = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:00:00")
        end = now.strftime("%Y-%m-%d %H:%M:%S")
        params = f"?startTime={urllib.parse.quote(start)}&endTime={urllib.parse.quote(end)}"

        req = urllib.request.Request(
            domain + "/api/monitor/usage/model-usage" + params,
            headers={"Authorization": token, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            summary = data.get("data", {}).get("totalUsage", {})
            models = {}
            for m in summary.get("modelSummaryList", []):
                models[m["modelName"]] = m["totalTokens"]
            return models
    except Exception as e:
        if out_fn:
            from .colors import C
            out_fn(f"  {C.YELLOW}⚠ 花费查询失败: {e}{C.RST}")
        return None


def calc_cost(models, pricing):
    total = 0.0
    details = []
    for model, tokens in models.items():
        p = pricing.get(model, {})
        avg_price = (p.get("input_per_million", 0) + p.get("output_per_million", 0)) / 2
        cost = (tokens / 1_000_000) * avg_price
        total += cost
        details.append((model, tokens, cost))
    return total, details


def load_last_usage():
    return read_json(LAST_USAGE_FILE, {})


def save_last_usage(usage):
    write_json(LAST_USAGE_FILE, usage)
