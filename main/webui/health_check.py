"""
WebUI 健康检查脚本
独立运行，检查WebUI和系统状态
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from loopcli_lib import LOOPCLI_ROOT, scan_agents

WEBUI_URL = "http://localhost:8080"
MAIN_DIR = LOOPCLI_ROOT / "main"

def check_webui():
    """检查WebUI状态"""
    try:
        import urllib.request
        req = urllib.request.Request(WEBUI_URL, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return {"status": "running", "response_code": resp.status}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def check_apis():
    """检查API端点"""
    apis = [
        "/api/agents",
        "/api/tasks",
        "/api/messages",
        "/api/longtask",
        "/api/stats"
    ]

    results = {}
    for api in apis:
        try:
            import urllib.request
            req = urllib.request.Request(f"{WEBUI_URL}{api}", method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                results[api] = {"status": "ok", "code": resp.status}
        except Exception as e:
            results[api] = {"status": "error", "error": str(e)}

    return results

def get_system_info():
    """获取系统信息"""
    info = {"timestamp": datetime.now(timezone.utc).isoformat()}

    if HAS_PSUTIL:
        try:
            info["cpu"] = {
                "percent": psutil.cpu_percent(interval=0.1)
            }
            memory = psutil.virtual_memory()
            info["memory"] = {
                "percent": memory.percent,
                "available_gb": round(memory.available / (1024**3), 2)
            }
            disk = psutil.disk_usage(str(LOOPCLI_ROOT))
            info["disk"] = {
                "percent": disk.percent,
                "free_gb": round(disk.free / (1024**3), 2)
            }
        except Exception as e:
            info["psutil_error"] = str(e)

    return info

def get_agent_status():
    """获取Agent状态"""
    agents = scan_agents()
    active = [a for a in agents if not a.get("disabled", False)]
    disabled = [a for a in agents if a.get("disabled", False)]

    return {
        "total": len(agents),
        "active": len(active),
        "disabled": len(disabled),
        "active_agents": [a.get("id", a.get("name", "unknown")) for a in active]
    }

def get_log_info():
    """获取日志信息"""
    log_path = MAIN_DIR / "log" / "run.md"
    if log_path.exists():
        stat = log_path.stat()
        return {
            "exists": True,
            "size_bytes": stat.st_size,
            "size_kb": round(stat.st_size / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()
        }
    return {"exists": False}

def main():
    """主检查函数"""
    print("=" * 50)
    print("WebUI 健康检查")
    print("=" * 50)

    # WebUI状态
    webui = check_webui()
    print(f"\n[WebUI] {webui['status']}")
    if webui['status'] == 'running':
        print(f"  响应码: {webui['response_code']}")
    else:
        print(f"  错误: {webui.get('error', 'Unknown')}")

    # API检查
    print("\n[API端点]")
    apis = check_apis()
    for api, result in apis.items():
        status_icon = "[OK]" if result['status'] == 'ok' else "[FAIL]"
        print(f"  {status_icon} {api}: {result.get('code', result.get('error'))}")

    # Agent状态
    print("\n[Agent状态]")
    agents = get_agent_status()
    print(f"  总数: {agents['total']}")
    print(f"  活跃: {agents['active']}")
    print(f"  禁用: {agents['disabled']}")
    if agents['active_agents']:
        print(f"  活跃列表: {', '.join(agents['active_agents'])}")

    # 系统信息
    print("\n[系统信息]")
    sys_info = get_system_info()
    if HAS_PSUTIL:
        print(f"  CPU: {sys_info['cpu']['percent']}%")
        print(f"  内存: {sys_info['memory']['percent']}% (可用: {sys_info['memory']['available_gb']}GB)")
        print(f"  磁盘: {sys_info['disk']['percent']}% (剩余: {sys_info['disk']['free_gb']}GB)")
    else:
        print("  (psutil未安装，跳过系统信息)")

    # 日志信息
    print("\n[日志信息]")
    log_info = get_log_info()
    if log_info['exists']:
        print(f"  大小: {log_info['size_kb']}KB")
        print(f"  修改时间: {log_info['modified']}")
    else:
        print("  日志文件不存在")

    # 生成报告
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "webui": webui,
        "apis": apis,
        "agents": agents,
        "system": sys_info,
        "logs": log_info
    }

    # 保存报告
    report_dir = Path(__file__).parent / "screenshots"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"health_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n报告已保存: {report_file}")
    print("=" * 50)

if __name__ == "__main__":
    main()
