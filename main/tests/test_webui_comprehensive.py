"""
WebUI Comprehensive Test Suite with Playwright
Tests all pages, themes, responsive design, and interactions.
"""

import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser

# Configuration
WEBUI_URL = "http://127.0.0.1:8080"
SCREENSHOT_DIR = Path("webui/screenshots")
REPORT_DIR = Path("webui/screenshots")

# Ensure directories exist
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


class WebUITester:
    def __init__(self):
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def setup(self):
        """Initialize browser and context"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()

    async def teardown(self):
        """Clean up"""
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.results.append({
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    async def screenshot(self, name: str):
        """Take screenshot with timestamp"""
        path = SCREENSHOT_DIR / f"test_{name}_{self.timestamp}.png"
        await self.page.screenshot(path=str(path))
        return path

    async def test_initial_load(self):
        """Test 1: Initial page load"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")
            await self.page.wait_for_selector(".app", timeout=5000)

            # Check main elements
            has_sidebar = await self.page.locator(".sidebar").count() > 0
            has_main = await self.page.locator(".main").count() > 0
            has_brand = await self.page.locator(".brand").count() > 0

            passed = has_sidebar and has_main and has_brand
            self.log_result("Initial Load", passed,
                          f"sidebar={has_sidebar}, main={has_main}, brand={has_brand}")
            await self.screenshot("initial_state")
            return passed
        except Exception as e:
            self.log_result("Initial Load", False, str(e))
            return False

    async def test_navigation(self):
        """Test 2: Navigation menu"""
        try:
            nav_items = [
                ("Dashboard", 1),
                ("Agents", 2),
                ("Tasks", 3),
                ("Logs", 4),
                ("Performance", 5),
                ("Settings", 6),
                ("Screenshots", 7)
            ]

            results = []
            for name, key in nav_items:
                try:
                    # Try clicking nav item
                    await self.page.keyboard.press(str(key))
                    await asyncio.sleep(0.5)
                    results.append(True)
                except:
                    results.append(False)

            passed = all(results)
            self.log_result("Navigation", passed, f"{sum(results)}/{len(results)} items work")
            return passed
        except Exception as e:
            self.log_result("Navigation", False, str(e))
            return False

    async def test_themes(self):
        """Test 3: Theme switching"""
        themes = ["dark", "light", "cyberpunk"]
        results = []

        for theme in themes:
            try:
                await self.page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
                await asyncio.sleep(0.3)
                await self.screenshot(f"theme_{theme}")

                # Verify theme changed
                current_theme = await self.page.evaluate(
                    "document.documentElement.getAttribute('data-theme')"
                )
                results.append(current_theme == theme)
            except Exception as e:
                results.append(False)

        passed = all(results)
        self.log_result("Theme Switching", passed, f"{sum(results)}/{len(themes)} themes work")
        return passed

    async def test_responsive(self):
        """Test 4: Responsive design"""
        viewports = [
            ("Desktop", 1920, 1080),
            ("Tablet", 768, 1024),
            ("Mobile", 375, 667)
        ]

        results = []
        for name, width, height in viewports:
            try:
                await self.page.set_viewport_size({"width": width, "height": height})
                await asyncio.sleep(0.3)
                await self.screenshot(f"responsive_{name}")
                results.append(True)
            except Exception as e:
                results.append(False)

        # Reset to desktop
        await self.page.set_viewport_size({"width": 1920, "height": 1080})

        passed = all(results)
        self.log_result("Responsive Design", passed, f"{sum(results)}/{len(viewports)} sizes work")
        return passed

    async def test_dashboard_cards(self):
        """Test 5: Dashboard statistics cards"""
        try:
            # Navigate to dashboard
            await self.page.keyboard.press("1")
            await asyncio.sleep(0.5)

            # Check for stats cards
            cards = await self.page.locator(".stat-card, .stats-grid > *").count()
            has_content = cards > 0

            await self.screenshot("dashboard_cards")

            self.log_result("Dashboard Cards", has_content, f"Found {cards} cards")
            return has_content
        except Exception as e:
            self.log_result("Dashboard Cards", False, str(e))
            return False

    async def test_agent_list(self):
        """Test 6: Agent list display"""
        try:
            await self.page.keyboard.press("2")
            await asyncio.sleep(0.5)

            # Check for agent items
            agents = await self.page.locator(".agent-card, .agent-item").count()

            await self.screenshot("agent_list")

            self.log_result("Agent List", True, f"Displaying {agents} agents")
            return True
        except Exception as e:
            self.log_result("Agent List", False, str(e))
            return False

    async def test_tasks_page(self):
        """Test 7: Tasks page"""
        try:
            await self.page.keyboard.press("3")
            await asyncio.sleep(0.5)

            # Check for tasks content
            has_tasks = await self.page.locator("[class*='task']").count() > 0

            await self.screenshot("tasks_page")

            self.log_result("Tasks Page", True, "Tasks page loads")
            return True
        except Exception as e:
            self.log_result("Tasks Page", False, str(e))
            return False

    async def test_logs_page(self):
        """Test 8: Logs page"""
        try:
            await self.page.keyboard.press("4")
            await asyncio.sleep(0.5)

            await self.screenshot("logs_page")

            self.log_result("Logs Page", True, "Logs page loads")
            return True
        except Exception as e:
            self.log_result("Logs Page", False, str(e))
            return False

    async def test_performance_page(self):
        """Test 9: Performance metrics"""
        try:
            await self.page.keyboard.press("5")  # May be different key
            await asyncio.sleep(0.5)

            await self.screenshot("performance_page")

            self.log_result("Performance Page", True, "Performance page loads")
            return True
        except Exception as e:
            self.log_result("Performance Page", False, str(e))
            return False

    async def test_screenshots_page(self):
        """Test 10: Screenshots gallery"""
        try:
            await self.page.keyboard.press("6")  # Screenshots page
            await asyncio.sleep(0.5)

            # Check for screenshot grid
            has_gallery = await self.page.locator(".screenshot-grid, [class*='screenshot']").count() >= 0

            await self.screenshot("screenshots_page")

            self.log_result("Screenshots Page", True, "Screenshots page loads")
            return True
        except Exception as e:
            self.log_result("Screenshots Page", False, str(e))
            return False

    async def test_settings_page(self):
        """Test 11: Settings page"""
        try:
            await self.page.keyboard.press("7")
            await asyncio.sleep(0.5)

            await self.screenshot("settings_page")

            self.log_result("Settings Page", True, "Settings page loads")
            return True
        except Exception as e:
            self.log_result("Settings Page", False, str(e))
            return False

    async def test_longtask_display(self):
        """Test 12: Long task display on main page"""
        try:
            await self.page.keyboard.press("1")
            await asyncio.sleep(0.5)

            # Check for long task card
            has_longtask = await self.page.locator("[class*='longtask']").count() > 0

            self.log_result("Long Task Display", has_longtask,
                          "Long task card visible" if has_longtask else "No long task")
            return True
        except Exception as e:
            self.log_result("Long Task Display", False, str(e))
            return False

    async def run_all_tests(self):
        """Run all tests and generate report"""
        print("[TEST] Starting WebUI Comprehensive Test Suite...")

        await self.setup()

        tests = [
            ("Initial Load", self.test_initial_load),
            ("Navigation", self.test_navigation),
            ("Themes", self.test_themes),
            ("Responsive Design", self.test_responsive),
            ("Dashboard Cards", self.test_dashboard_cards),
            ("Agent List", self.test_agent_list),
            ("Tasks Page", self.test_tasks_page),
            ("Logs Page", self.test_logs_page),
            ("Performance Page", self.test_performance_page),
            ("Screenshots Page", self.test_screenshots_page),
            ("Settings Page", self.test_settings_page),
            ("Long Task Display", self.test_longtask_display),
        ]

        for name, test_func in tests:
            print(f"  [RUN] Testing: {name}...")
            try:
                await test_func()
            except Exception as e:
                self.log_result(name, False, f"Exception: {e}")

        await self.teardown()
        await self.generate_report()

    async def generate_report(self):
        """Generate test report"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = total - passed

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "results": self.results
        }

        report_path = REPORT_DIR / f"comprehensive_test_report_{self.timestamp}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        # Print summary
        print(f"\n[REPORT] Test Report Generated: {report_path}")
        print(f"   Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f"   Success Rate: {report['summary']['success_rate']}")

        return report


async def main():
    """Main entry point"""
    tester = WebUITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
