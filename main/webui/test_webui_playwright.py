"""
WebUI Playwright 深度测试
测试所有按钮、交互、响应式设计，并生成截图报告
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, expect

WEBUI_URL = "http://localhost:8080"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots"
REPORT_FILE = SCREENSHOT_DIR / f"playwright_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

# 测试结果
results = {
    "timestamp": datetime.now().isoformat(),
    "summary": {"total": 0, "passed": 0, "failed": 0, "skipped": 0},
    "tests": []
}

async def take_screenshot(page, name, category=""):
    """截图并保存"""
    category_dir = SCREENSHOT_DIR / category if category else SCREENSHOT_DIR
    category_dir.mkdir(parents=True, exist_ok=True)
    path = category_dir / f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    await page.screenshot(path=str(path), full_page=True)
    return str(path)

async def test_page(page, page_name, page_id):
    """测试单个页面"""
    test_result = {"page": page_name, "tests": []}

    try:
        # 点击导航
        await page.click(f"[data-page=\"{page_id}\"]")
        await page.wait_for_timeout(500)

        # 截图
        screenshot_path = await take_screenshot(page, f"page_{page_id}", "pages")
        test_result["tests"].append({"name": f"页面 {page_name} 加载", "status": "passed", "screenshot": screenshot_path})

        # 检查页面元素
        try:
            content = await page.content()
            if page_id in content or page_name in content:
                test_result["tests"].append({"name": f"页面 {page_name} 内容验证", "status": "passed"})
            else:
                test_result["tests"].append({"name": f"页面 {page_name} 内容验证", "status": "failed", "error": "内容未找到"})
        except Exception as e:
            test_result["tests"].append({"name": f"页面 {page_name} 内容验证", "status": "failed", "error": str(e)})

        # 测试页面上的按钮
        buttons = await page.query_selector_all("button, .btn, [role=\"button\"]")
        test_result["tests"].append({"name": f"页面 {page_name} 按钮数量: {len(buttons)}", "status": "passed"})

        # 点击主要按钮（前3个）
        for i, button in enumerate(buttons[:3]):
            try:
                await button.click()
                await page.wait_for_timeout(200)
                test_result["tests"].append({"name": f"页面 {page_name} 按钮{i+1} 点击", "status": "passed"})
            except Exception as e:
                test_result["tests"].append({"name": f"页面 {page_name} 按钮{i+1} 点击", "status": "failed", "error": str(e)})

        test_result["status"] = "passed"
    except Exception as e:
        test_result["status"] = "failed"
        test_result["error"] = str(e)

    return test_result

async def test_themes(page):
    """测试主题切换"""
    test_result = {"category": "主题切换", "tests": []}

    themes = ["dark", "light", "cyberpunk"]

    for theme in themes:
        try:
            await page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
            await page.wait_for_timeout(300)
            screenshot_path = await take_screenshot(page, f"theme_{theme}", "themes")
            test_result["tests"].append({"name": f"主题 {theme}", "status": "passed", "screenshot": screenshot_path})
        except Exception as e:
            test_result["tests"].append({"name": f"主题 {theme}", "status": "failed", "error": str(e)})

    # 恢复默认主题
    await page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
    return test_result

async def test_responsive(page):
    """测试响应式设计"""
    test_result = {"category": "响应式设计", "tests": []}

    viewports = [
        {"name": "桌面", "width": 1920, "height": 1080},
        {"name": "平板", "width": 768, "height": 1024},
        {"name": "手机", "width": 375, "height": 667}
    ]

    for vp in viewports:
        try:
            await page.set_viewport_size({"width": vp["width"], "height": vp["height"]})
            await page.wait_for_timeout(300)
            screenshot_path = await take_screenshot(page, f"responsive_{vp['name']}", "responsive")
            test_result["tests"].append({"name": f"响应式 {vp['name']}", "status": "passed", "screenshot": screenshot_path})
        except Exception as e:
            test_result["tests"].append({"name": f"响应式 {vp['name']}", "status": "failed", "error": str(e)})

    # 恢复桌面视图
    await page.set_viewport_size({"width": 1920, "height": 1080})
    return test_result

async def test_interactions(page):
    """测试交互功能"""
    test_result = {"category": "交互功能", "tests": []}

    # 测试侧边栏切换
    try:
        sidebar_toggle = await page.query_selector("[data-action=\"toggle-sidebar\"]")
        if sidebar_toggle:
            await sidebar_toggle.click()
            await page.wait_for_timeout(300)
            screenshot_path = await take_screenshot(page, "sidebar_collapsed", "interactions")
            test_result["tests"].append({"name": "侧边栏折叠", "status": "passed", "screenshot": screenshot_path})

            # 恢复侧边栏
            await sidebar_toggle.click()
            await page.wait_for_timeout(300)
        else:
            test_result["tests"].append({"name": "侧边栏折叠", "status": "skipped", "error": "按钮未找到"})
    except Exception as e:
        test_result["tests"].append({"name": "侧边栏折叠", "status": "failed", "error": str(e)})

    # 测试快捷键帮助
    try:
        help_btn = await page.query_selector("[data-action=\"show-help\"]")
        if help_btn:
            await help_btn.click()
            await page.wait_for_timeout(300)
            screenshot_path = await take_screenshot(page, "shortcuts_modal", "interactions")
            test_result["tests"].append({"name": "快捷键帮助", "status": "passed", "screenshot": screenshot_path})

            # 关闭帮助
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(200)
        else:
            test_result["tests"].append({"name": "快捷键帮助", "status": "skipped", "error": "按钮未找到"})
    except Exception as e:
        test_result["tests"].append({"name": "快捷键帮助", "status": "failed", "error": str(e)})

    return test_result

async def test_api_endpoints(page):
    """测试API端点"""
    test_result = {"category": "API端点", "tests": []}

    endpoints = [
        {"name": "Agents", "path": "/api/agents"},
        {"name": "Tasks", "path": "/api/tasks"},
        {"name": "Messages", "path": "/api/messages"},
        {"name": "Stats", "path": "/api/stats"}
    ]

    for endpoint in endpoints:
        try:
            response = await page.request.get(f"{WEBUI_URL}{endpoint['path']}")
            if response.status == 200:
                test_result["tests"].append({"name": f"API {endpoint['name']}", "status": "passed", "status_code": response.status})
            else:
                test_result["tests"].append({"name": f"API {endpoint['name']}", "status": "failed", "status_code": response.status})
        except Exception as e:
            test_result["tests"].append({"name": f"API {endpoint['name']}", "status": "failed", "error": str(e)})

    return test_result

async def main():
    """主测试流程"""
    import sys
    import io

    # 设置标准输出编码为UTF-8
    if sys.platform == "win32":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print("[START] WebUI深度测试开始...")

        # 访问WebUI
        try:
            await page.goto(WEBUI_URL, wait_until="networkidle")
            print("[OK] WebUI加载成功")
            await take_screenshot(page, "initial_state", "overview")
        except Exception as e:
            print(f"[ERROR] WebUI加载失败: {e}")
            await browser.close()
            return

        # 测试各个页面
        pages = [
            {"name": "控制台", "id": "dashboard"},
            {"name": "代理", "id": "agents"},
            {"name": "任务", "id": "tasks"},
            {"name": "日志", "id": "logs"},
            {"name": "消息", "id": "messages"},
            {"name": "通知", "id": "notifications"},
            {"name": "健康", "id": "health"},
            {"name": "分析", "id": "analytics"},
            {"name": "成本", "id": "cost"},
            {"name": "设置", "id": "settings"},
            {"name": "控制", "id": "control"}
        ]

        for page_info in pages:
            print(f"[TEST] 页面: {page_info['name']}")
            result = await test_page(page, page_info['name'], page_info['id'])
            results["tests"].append(result)
            results["summary"]["total"] += len(result["tests"])
            results["summary"]["passed"] += sum(1 for t in result["tests"] if t["status"] == "passed")
            results["summary"]["failed"] += sum(1 for t in result["tests"] if t["status"] == "failed")
            results["summary"]["skipped"] += sum(1 for t in result["tests"] if t["status"] == "skipped")

        # 测试主题
        print("[TEST] 主题切换...")
        theme_result = await test_themes(page)
        results["tests"].append(theme_result)
        results["summary"]["total"] += len(theme_result["tests"])
        results["summary"]["passed"] += sum(1 for t in theme_result["tests"] if t["status"] == "passed")

        # 测试响应式
        print("[TEST] 响应式设计...")
        responsive_result = await test_responsive(page)
        results["tests"].append(responsive_result)
        results["summary"]["total"] += len(responsive_result["tests"])
        results["summary"]["passed"] += sum(1 for t in responsive_result["tests"] if t["status"] == "passed")

        # 测试交互
        print("[TEST] 交互功能...")
        interaction_result = await test_interactions(page)
        results["tests"].append(interaction_result)
        results["summary"]["total"] += len(interaction_result["tests"])
        results["summary"]["passed"] += sum(1 for t in interaction_result["tests"] if t["status"] == "passed")

        # 测试API
        print("[TEST] API端点...")
        api_result = await test_api_endpoints(page)
        results["tests"].append(api_result)
        results["summary"]["total"] += len(api_result["tests"])
        results["summary"]["passed"] += sum(1 for t in api_result["tests"] if t["status"] == "passed")

        await browser.close()

    # 保存报告
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 打印摘要
    print("\n" + "="*50)
    print("[DONE] 测试完成!")
    print(f"总计: {results['summary']['total']} | 通过: {results['summary']['passed']} | 失败: {results['summary']['failed']} | 跳过: {results['summary']['skipped']}")
    if results['summary']['total'] > 0:
        print(f"成功率: {results['summary']['passed']/results['summary']['total']*100:.1f}%")
    print(f"报告: {REPORT_FILE}")
    print(f"截图目录: {SCREENSHOT_DIR}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
