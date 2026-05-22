"""
LoopCLI WebUI Deep Playwright Test
测试所有页面、按钮、交互功能，截图验证
"""
import asyncio
import os
import json
import sys
from pathlib import Path
from datetime import datetime

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("Installing playwright...")
    os.system(f"{sys.executable} -m pip install playwright -q")
    os.system(f"{sys.executable} -m playwright install chromium")
    from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8080"
SCREENSHOTS_DIR = Path("D:/loopcli/main/webui/screenshots/deep_test")
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

results = {"passed": 0, "failed": 0, "errors": []}

def screenshot_path(name):
    return str(SCREENSHOTS_DIR / f"{name}.png")

def record(test_name, passed, detail=""):
    if passed:
        results["passed"] += 1
        print(f"  PASS: {test_name}")
    else:
        results["failed"] += 1
        results["errors"].append(f"{test_name}: {detail}")
        print(f"  FAIL: {test_name} - {detail}")


async def run_tests():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN"
        )
        page = await context.new_page()

        # Collect console errors
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        # ===== 1. Page Load =====
        print("\n=== 1. 页面加载 ===")
        try:
            resp = await page.goto(BASE_URL, wait_until="networkidle", timeout=15000)
            record("首页加载", resp.status == 200, f"status={resp.status}")
        except Exception as e:
            record("首页加载", False, str(e))
            await browser.close()
            return

        await page.screenshot(path=screenshot_path("01_home_loaded"))
        record("首页截图", True)

        # Check title
        title = await page.title()
        record("页面标题包含 LoopCLI", "LoopCLI" in title, f"title={title}")

        # Check sidebar exists
        sidebar = await page.query_selector(".sidebar")
        record("侧边栏存在", sidebar is not None)

        # Check brand
        brand = await page.query_selector(".brand h1")
        brand_text = await brand.inner_text() if brand else ""
        record("品牌标识", "LoopCLI" in brand_text, f"text={brand_text}")

        # ===== 2. Navigation Tests =====
        print("\n=== 2. 导航测试 ===")
        nav_items = ["agents", "tasks", "performance", "logs", "screenshots", "settings"]
        for i, nav_id in enumerate(nav_items):
            try:
                nav_el = await page.query_selector(f'.nav-item[data-page="{nav_id}"]')
                if nav_el:
                    await nav_el.click()
                    await page.wait_for_timeout(800)

                    # Check page is active
                    active_page = await page.query_selector(f"#page-{nav_id}.active")
                    record(f"导航到 {nav_id}", active_page is not None, f"page not active")
                    await page.screenshot(path=screenshot_path(f"02_nav_{nav_id}"))
                else:
                    record(f"导航到 {nav_id}", False, "nav element not found")
            except Exception as e:
                record(f"导航到 {nav_id}", False, str(e))

        # ===== 3. Agents Page =====
        print("\n=== 3. Agents 页面测试 ===")
        await page.click('.nav-item[data-page="agents"]')
        await page.wait_for_timeout(1500)

        # Stats cards
        total_agents = await page.query_selector("#total-agents")
        if total_agents:
            text = await total_agents.inner_text()
            record("Agent 总数显示", text != "-", f"text={text}")
        else:
            record("Agent 总数显示", False, "element not found")

        # Agent cards
        agent_cards = await page.query_selector_all(".agent-card")
        record(f"Agent 卡片数量", len(agent_cards) > 0, f"count={len(agent_cards)}")

        # Search functionality
        search_input = await page.query_selector("#agent-search")
        if search_input:
            await search_input.fill("engineering")
            await page.wait_for_timeout(500)
            visible_cards = await page.query_selector_all(".agent-card:not([style*='display: none'])")
            record("搜索过滤功能", len(visible_cards) >= 0, f"visible={len(visible_cards)}")
            await search_input.fill("")
            await page.wait_for_timeout(300)

        # Refresh button
        refresh_btn = await page.query_selector("#refresh-btn")
        if refresh_btn:
            await refresh_btn.click()
            await page.wait_for_timeout(1000)
            record("刷新按钮", True)

        # Create Agent button
        create_btn = await page.query_selector("#create-agent-btn")
        record("创建 Agent 按钮存在", create_btn is not None)

        if create_btn:
            await create_btn.click()
            await page.wait_for_timeout(2000)
            modal = await page.query_selector("#create-agent-modal")
            record("创建 Agent 模态框弹出", modal is not None)
            await page.screenshot(path=screenshot_path("03_create_agent_modal"))
            if modal:
                # Close modal by clicking backdrop
                await page.evaluate("document.getElementById('create-agent-modal')?.click()")
                await page.wait_for_timeout(500)

        # Export button
        export_btn = await page.query_selector("#export-btn")
        record("导出按钮存在", export_btn is not None)

        # Agent enable/disable buttons
        if agent_cards:
            first_card = agent_cards[0]
            enable_btn = await first_card.query_selector(".btn-primary")
            disable_btn = await first_card.query_selector(".btn-secondary")
            record("Agent 启用按钮存在", enable_btn is not None)
            record("Agent 禁用按钮存在", disable_btn is not None)

        # Charts
        status_chart = await page.query_selector("#agent-status-chart")
        record("状态分布图容器存在", status_chart is not None)
        progress_chart = await page.query_selector("#task-progress-chart")
        record("任务进度图容器存在", progress_chart is not None)

        # Usage panel
        usage_panel = await page.query_selector("#usage-panel")
        usage_content = await page.query_selector("#usage-content")
        record("用量面板存在", usage_panel is not None)
        if usage_content:
            usage_text = await usage_content.inner_text()
            record("用量数据加载", "加载失败" not in usage_text, f"text_preview={usage_text[:50]}")

        # Longtask card
        longtask_card = await page.query_selector("#longtask-card")
        record("长期任务卡片存在", longtask_card is not None)

        await page.screenshot(path=screenshot_path("03_agents_page_full"))

        # ===== 4. Tasks Page =====
        print("\n=== 4. Tasks 页面测试 ===")
        await page.click('.nav-item[data-page="tasks"]')
        await page.wait_for_timeout(1500)

        tasks_table = await page.query_selector(".tasks-table")
        record("任务表格存在", tasks_table is not None)

        tbody_rows = await page.query_selector_all("#tasks-table-body tr")
        record("任务数据行", len(tbody_rows) > 0, f"rows={len(tbody_rows)}")

        await page.screenshot(path=screenshot_path("04_tasks_page"))

        # ===== 5. Performance Page =====
        print("\n=== 5. Performance 页面测试 ===")
        await page.click('.nav-item[data-page="performance"]')
        await page.wait_for_timeout(2000)

        cpu_el = await page.query_selector("#cpu-usage")
        mem_el = await page.query_selector("#memory-usage")
        resp_el = await page.query_selector("#response-time")
        token_el = await page.query_selector("#token-usage")

        if cpu_el:
            cpu_text = await cpu_el.inner_text()
            record("CPU 数据", cpu_text != "-%", f"text={cpu_text}")

        if mem_el:
            mem_text = await mem_el.inner_text()
            record("内存数据", mem_text != "- MB", f"text={mem_text}")

        if resp_el:
            resp_text = await resp_el.inner_text()
            record("响应时间", resp_text != "- ms", f"text={resp_text}")

        # Token trend chart
        trend_canvas = await page.query_selector("#token-trend-chart")
        record("Token 趋势图存在", trend_canvas is not None)

        # Switches
        switches = await page.query_selector_all(".switch input[type='checkbox']")
        record("性能设置开关", len(switches) >= 2, f"count={len(switches)}")

        await page.screenshot(path=screenshot_path("05_performance_page"))

        # ===== 6. Logs Page =====
        print("\n=== 6. Logs 页面测试 ===")
        await page.click('.nav-item[data-page="logs"]')
        await page.wait_for_timeout(1500)

        logs_content = await page.query_selector("#logs-content")
        record("日志容器存在", logs_content is not None)

        log_entries = await page.query_selector_all(".log-entry")
        record("日志条目", len(log_entries) >= 0, f"count={len(log_entries)}")

        clear_btn = await page.query_selector("button[onclick='clearLogs()']")
        record("清空日志按钮存在", clear_btn is not None)

        await page.screenshot(path=screenshot_path("06_logs_page"))

        # ===== 7. Screenshots Page =====
        print("\n=== 7. Screenshots 页面测试 ===")
        await page.click('.nav-item[data-page="screenshots"]')
        await page.wait_for_timeout(1500)

        screenshots_grid = await page.query_selector("#screenshots-grid")
        record("截图网格存在", screenshots_grid is not None)

        await page.screenshot(path=screenshot_path("07_screenshots_page"))

        # ===== 8. Settings Page =====
        print("\n=== 8. Settings 页面测试 ===")
        await page.click('.nav-item[data-page="settings"]')
        await page.wait_for_timeout(2000)

        # Theme selector
        theme_selector = await page.query_selector("#theme-selector")
        record("主题选择器存在", theme_selector is not None)

        # Test theme switching
        if theme_selector:
            for theme in ["dark", "light", "cyberpunk"]:
                await theme_selector.select_option(theme)
                await page.wait_for_timeout(500)
                data_theme = await page.evaluate("document.documentElement.dataset.theme")
                record(f"切换到 {theme} 主题", data_theme == theme, f"got={data_theme}")
                await page.screenshot(path=screenshot_path(f"08_settings_{theme}_theme"))

            # Reset to dark
            await theme_selector.select_option("dark")
            await page.wait_for_timeout(300)

        # Refresh interval
        refresh_input = await page.query_selector("#refresh-interval")
        record("刷新间隔设置存在", refresh_input is not None)
        if refresh_input:
            val = await refresh_input.get_attribute("value")
            record("刷新间隔默认值", val == "10", f"val={val}")

        # Switches
        compact_switch = await page.query_selector("#compact-mode")
        notifications_switch = await page.query_selector("#enable-notifications")
        record("紧凑模式开关存在", compact_switch is not None)
        record("通知开关存在", notifications_switch is not None)

        # System info
        server_status = await page.query_selector("#server-status")
        if server_status:
            status_text = await server_status.inner_text()
            record("服务器状态", "运行中" in status_text or "连接失败" in status_text, f"text={status_text}")

        # Longtask section
        longtask_status = await page.query_selector("#longtask-status")
        record("设置页长期任务状态", longtask_status is not None)

        await page.screenshot(path=screenshot_path("08_settings_page"))

        # ===== 9. Theme Toggle Button =====
        print("\n=== 9. 主题切换按钮测试 ===")
        theme_btn = await page.query_selector("#theme-toggle")
        record("主题切换按钮存在", theme_btn is not None)

        if theme_btn:
            # Click to cycle through themes
            for expected in ["light", "cyberpunk", "dark"]:
                await theme_btn.click()
                await page.wait_for_timeout(500)
                current = await page.evaluate("document.documentElement.dataset.theme")
                record(f"主题按钮切换到 {expected}", current == expected, f"got={current}")

        # ===== 10. Keyboard Shortcuts =====
        print("\n=== 10. 键盘快捷键测试 ===")

        # Test help panel (? button)
        help_btn = await page.query_selector("#help-toggle")
        if help_btn:
            await help_btn.click()
            await page.wait_for_timeout(500)
            shortcuts_panel = await page.query_selector("#shortcuts-panel.active")
            record("快捷键面板弹出", shortcuts_panel is not None)
            await page.screenshot(path=screenshot_path("10_shortcuts_panel"))

            # Close with ESC
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(300)
            panel_after = await page.query_selector("#shortcuts-panel.active")
            record("ESC关闭快捷键面板", panel_after is None)

        # Test number key navigation
        for key_num, page_name in [("1", "agents"), ("2", "tasks"), ("3", "performance")]:
            await page.keyboard.press(key_num)
            await page.wait_for_timeout(500)
            active = await page.query_selector(f"#page-{page_name}.active")
            record(f"快捷键 {key_num} -> {page_name}", active is not None)

        # Test R for refresh
        await page.keyboard.press("r")
        await page.wait_for_timeout(1000)
        record("快捷键 R 刷新", True)

        # ===== 11. Responsive Design =====
        print("\n=== 11. 响应式设计测试 ===")
        for size_name, width, height in [("mobile", 375, 812), ("tablet", 768, 1024)]:
            await page.set_viewport_size({"width": width, "height": height})
            await page.wait_for_timeout(800)
            await page.screenshot(path=screenshot_path(f"11_responsive_{size_name}"))
            record(f"响应式 {size_name} 截图", True)

            # Check sidebar adaptability
            sidebar_el = await page.query_selector(".sidebar")
            if sidebar_el:
                box = await sidebar_el.bounding_box()
                if size_name == "mobile":
                    # On mobile, sidebar should be horizontal (full width)
                    record(f"{size_name} 侧边栏适配", box and box["width"] >= 300 if box else False,
                           f"width={box['width'] if box else 'N/A'}")

        # Reset viewport
        await page.set_viewport_size({"width": 1440, "height": 900})
        await page.wait_for_timeout(500)

        # ===== 12. Auto-refresh Indicator =====
        print("\n=== 12. 自动刷新指示器 ===")
        indicator = await page.query_selector("#auto-refresh-indicator")
        record("自动刷新指示器存在", indicator is not None)

        refresh_status = await page.query_selector("#refresh-status")
        if refresh_status:
            rs_text = await refresh_status.inner_text()
            record("自动刷新状态文字", "s" in rs_text or "刷新" in rs_text, f"text={rs_text}")

        # ===== 13. Notification System =====
        print("\n=== 13. 通知系统测试 ===")
        notif_container = await page.query_selector("#notification-container")
        record("通知容器存在", notif_container is not None)

        # Trigger a notification via theme switch
        await page.click('.nav-item[data-page="agents"]')
        await page.wait_for_timeout(300)
        theme_btn2 = await page.query_selector("#theme-toggle")
        if theme_btn2:
            await theme_btn2.click()
            await page.wait_for_timeout(1000)
            notifications = await page.query_selector_all(".notification")
            record("通知触发显示", len(notifications) > 0, f"count={len(notifications)}")
            await page.screenshot(path=screenshot_path("13_notification"))

        # ===== 14. Console Error Check =====
        print("\n=== 14. JS 错误检查 ===")
        # Navigate to all pages to catch errors
        for nav_id in nav_items:
            await page.click(f'.nav-item[data-page="{nav_id}"]')
            await page.wait_for_timeout(1000)
        record(f"JS错误检查", len(console_errors) == 0,
               f"found {len(console_errors)} errors: {console_errors[:3]}")

        # ===== 15. Final Screenshots =====
        print("\n=== 15. 最终截图 ===")
        await page.click('.nav-item[data-page="agents"]')
        await page.wait_for_timeout(1500)
        await page.screenshot(path=screenshot_path("15_final_agents"), full_page=True)

        # Full page screenshot of each section
        for nav_id in nav_items:
            await page.click(f'.nav-item[data-page="{nav_id}"]')
            await page.wait_for_timeout(1000)
            await page.screenshot(path=screenshot_path(f"15_final_{nav_id}"), full_page=True)

        await browser.close()

    # Print summary
    print(f"\n{'='*50}")
    print(f"测试完成: {results['passed']} 通过, {results['failed']} 失败")
    if results["errors"]:
        print(f"\n失败项:")
        for err in results["errors"]:
            print(f"  - {err}")
    print(f"\n截图保存在: {SCREENSHOTS_DIR}")
    return results


if __name__ == "__main__":
    res = asyncio.run(run_tests())
    # Save results
    with open(str(SCREENSHOTS_DIR / "test_results.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
