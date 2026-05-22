"""
WebUI API 端点测试
直接测试API，无需浏览器
"""
import json
import requests
from datetime import datetime
from pathlib import Path

WEBUI_URL = "http://localhost:8080"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
REPORT_FILE = SCREENSHOT_DIR / f"api_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

results = {
    "timestamp": datetime.now().isoformat(),
    "tests": []
}

def test_endpoint(path, name):
    """测试单个API端点"""
    try:
        response = requests.get(f"{WEBUI_URL}{path}", timeout=5)
        if response.status_code == 200:
            results["tests"].append({
                "name": name,
                "status": "passed",
                "status_code": response.status_code,
                "response_time": response.elapsed.total_seconds()
            })
            print(f"[OK] {name}: {response.status_code}")
            return True
        else:
            results["tests"].append({
                "name": name,
                "status": "failed",
                "status_code": response.status_code
            })
            print(f"[FAIL] {name}: {response.status_code}")
            return False
    except Exception as e:
        results["tests"].append({
            "name": name,
            "status": "error",
            "error": str(e)
        })
        print(f"[ERROR] {name}: {e}")
        return False

def main():
    """主测试函数"""
    print("开始API端点测试...")
    print(f"目标: {WEBUI_URL}")
    print("="*50)

    # 测试主页
    try:
        response = requests.get(WEBUI_URL, timeout=5)
        print(f"[OK] 主页加载: {response.status_code}")
        results["tests"].append({
            "name": "主页加载",
            "status": "passed",
            "status_code": response.status_code
        })
    except Exception as e:
        print(f"[ERROR] 主页加载失败: {e}")
        results["tests"].append({
            "name": "主页加载",
            "status": "error",
            "error": str(e)
        })
        return

    # 测试API端点
    endpoints = [
        ("/api/agents", "Agents API"),
        ("/api/tasks", "Tasks API"),
        ("/api/messages", "Messages API"),
        ("/api/longtask", "LongTask API"),
        ("/api/stats", "Stats API"),
        ("/api/health", "Health API")
    ]

    for path, name in endpoints:
        test_endpoint(path, name)

    # 测试静态资源
    print("\n测试静态资源...")
    static_files = [
        ("/index.html", "主页HTML"),
        ("/favicon.ico", "图标")
    ]

    for path, name in static_files:
        test_endpoint(path, name)

    # 统计结果
    total = len(results["tests"])
    passed = sum(1 for t in results["tests"] if t["status"] == "passed")
    failed = sum(1 for t in results["tests"] if t["status"] == "failed")
    errors = sum(1 for t in results["tests"] if t["status"] == "error")

    results["summary"] = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "success_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%"
    }

    # 保存报告
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print("\n" + "="*50)
    print("API测试完成!")
    print(f"总计: {total} | 通过: {passed} | 失败: {failed} | 错误: {errors}")
    print(f"成功率: {results['summary']['success_rate']}")
    print(f"报告: {REPORT_FILE}")
    print("="*50)

if __name__ == "__main__":
    main()
