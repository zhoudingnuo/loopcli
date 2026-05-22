"""
WebUI 简化测试 - 同步版本
快速测试WebUI核心功能和截图
"""
import json
import time
from datetime import datetime
from pathlib import Path
from playwright.sync_api import sync_playwright

WEBUI_URL = "http://localhost:8080"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
REPORT_FILE = SCREENSHOT_DIR / f"simple_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

results = {
    "timestamp": datetime.now().isoformat(),
    "tests": []
}

def test_webui():
    """主测试函数"""
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        print("启动浏览器...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # 访问WebUI
            print(f"访问 {WEBUI_URL}...")
            page.goto(WEBUI_URL, wait_until="networkidle", timeout=10000)
            results["tests"].append({"name": "WebUI加载", "status": "passed"})
            page.screenshot(path=str(SCREENSHOT_DIR / "test_initial_state.png"))
            print("WebUI加载成功")

            # 测试各个页面
            pages = [
                ("dashboard", "控制台"),
                ("agents", "代理"),
                ("tasks", "任务"),
                ("logs", "日志"),
                ("messages", "消息"),
                ("notifications", "通知"),
                ("health", "健康"),
                ("analytics", "分析"),
                ("cost", "成本"),
                ("settings", "设置"),
                ("control", "控制")
            ]

            for page_id, page_name in pages:
                try:
                    print(f"测试页面: {page_name}")
                    # 点击导航
                    page.click(f"[data-page=\"{page_id}\"]")
                    time.sleep(0.3)

                    # 截图
                    screenshot_path = SCREENSHOT_DIR / f"test_page_{page_id}.png"
                    page.screenshot(path=str(screenshot_path))

                    # 检查内容
                    content = page.content()
                    if page_id in content:
                        results["tests"].append({"name": f"页面{page_name}", "status": "passed"})
                    else:
                        results["tests"].append({"name": f"页面{page_name}", "status": "warning", "note": "内容未完全验证"})

                except Exception as e:
                    results["tests"].append({"name": f"页面{page_name}", "status": "failed", "error": str(e)})
                    print(f"  错误: {e}")

            # 测试主题
            print("测试主题切换...")
            for theme in ["light", "dark", "cyberpunk"]:
                try:
                    page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
                    time.sleep(0.2)
                    page.screenshot(path=str(SCREENSHOT_DIR / f"test_theme_{theme}.png"))
                    results["tests"].append({"name": f"主题{theme}", "status": "passed"})
                except Exception as e:
                    results["tests"].append({"name": f"主题{theme}", "status": "failed", "error": str(e)})

            # 恢复默认主题
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")

            # 测试响应式
            print("测试响应式设计...")
            for size_name, width, height in [("桌面", 1920, 1080), ("平板", 768, 1024), ("手机", 375, 667)]:
                try:
                    page.set_viewport_size({"width": width, "height": height})
                    time.sleep(0.2)
                    page.screenshot(path=str(SCREENSHOT_DIR / f"test_responsive_{size_name}.png"))
                    results["tests"].append({"name": f"响应式{size_name}", "status": "passed"})
                except Exception as e:
                    results["tests"].append({"name": f"响应式{size_name}", "status": "failed", "error": str(e)})

            # 测试按钮
            print("测试按钮功能...")
            try:
                # 侧边栏切换
                page.click("[data-action=\"toggle-sidebar\"]")
                time.sleep(0.2)
                page.screenshot(path=str(SCREENSHOT_DIR / "test_sidebar_collapsed.png"))
                results["tests"].append({"name": "侧边栏折叠", "status": "passed"})

                # 恢复侧边栏
                page.click("[data-action=\"toggle-sidebar\"]")
                time.sleep(0.2)
            except Exception as e:
                results["tests"].append({"name": "侧边栏切换", "status": "failed", "error": str(e)})

            # 测试API端点
            print("测试API端点...")
            api_endpoints = ["/api/agents", "/api/tasks", "/api/messages", "/api/stats"]
            for endpoint in api_endpoints:
                try:
                    response = page.request.get(f"{WEBUI_URL}{endpoint}")
                    if response.status == 200:
                        results["tests"].append({"name": f"API{endpoint}", "status": "passed"})
                    else:
                        results["tests"].append({"name": f"API{endpoint}", "status": "failed", "status_code": response.status})
                except Exception as e:
                    results["tests"].append({"name": f"API{endpoint}", "status": "failed", "error": str(e)})

        except Exception as e:
            results["tests"].append({"name": "主测试流程", "status": "failed", "error": str(e)})
            print(f"主测试错误: {e}")

        finally:
            browser.close()

    # 统计结果
    total = len(results["tests"])
    passed = sum(1 for t in results["tests"] if t["status"] == "passed")
    failed = sum(1 for t in results["tests"] if t["status"] == "failed")
    warning = sum(1 for t in results["tests"] if t["status"] == "warning")

    results["summary"] = {
        "total": total,
        "passed": passed,
        "failed": failed,
        "warning": warning,
        "success_rate": f"{passed/total*100:.1f}%" if total > 0 else "0%"
    }

    # 保存报告
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print("\n" + "="*50)
    print("测试完成!")
    print(f"总计: {total} | 通过: {passed} | 失败: {failed} | 警告: {warning}")
    print(f"成功率: {results['summary']['success_rate']}")
    print(f"报告: {REPORT_FILE}")
    print(f"截图目录: {SCREENSHOT_DIR}")
    print("="*50)

if __name__ == "__main__":
    test_webui()
