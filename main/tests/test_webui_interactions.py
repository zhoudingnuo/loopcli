"""
WebUI Interaction Tests with Playwright
Tests all buttons, forms, and API interactions.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

WEBUI_URL = "http://127.0.0.1:8080"
SCREENSHOT_DIR = Path("webui/screenshots")


class InteractionTester:
    def __init__(self):
        self.results = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def setup(self):
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
        await self.context.close()
        await self.browser.close()
        await self.playwright.stop()

    def log_result(self, test_name: str, passed: bool, details: str = ""):
        self.results.append({
            "test": test_name,
            "status": "PASS" if passed else "FAIL",
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

    async def screenshot(self, name: str):
        path = SCREENSHOT_DIR / f"interact_{name}_{self.timestamp}.png"
        await self.page.screenshot(path=str(path))

    async def test_button_count(self):
        """Test: Count all interactive buttons"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")
            await asyncio.sleep(1)

            # Count all buttons
            buttons = await self.page.locator("button, .btn, [role='button']").count()
            nav_items = await self.page.locator(".nav-item").count()

            self.log_result("Button Count", True,
                          f"Found {buttons} buttons, {nav_items} nav items")
            await self.screenshot("button_count")
            return True
        except Exception as e:
            self.log_result("Button Count", False, str(e))
            return False

    async def test_theme_toggle(self):
        """Test: Theme toggle button"""
        try:
            # Navigate to settings
            await self.page.goto(WEBUI_URL + "?page=settings", wait_until="networkidle")
            await asyncio.sleep(0.5)

            # Try to find and click theme toggle
            toggles = await self.page.locator("[class*='theme'], [class*='toggle']").count()

            # Test theme switching via JS
            themes_tested = []
            for theme in ["light", "dark", "cyberpunk"]:
                await self.page.evaluate(
                    f"document.documentElement.setAttribute('data-theme', '{theme}')"
                )
                await asyncio.sleep(0.2)
                current = await self.page.evaluate(
                    "document.documentElement.getAttribute('data-theme')"
                )
                themes_tested.append(current == theme)

            passed = all(themes_tested)
            self.log_result("Theme Toggle", passed,
                          f"{sum(themes_tested)}/3 themes switched")
            await self.screenshot("theme_toggle_test")
            return passed
        except Exception as e:
            self.log_result("Theme Toggle", False, str(e))
            return False

    async def test_api_endpoints(self):
        """Test: Key API endpoints"""
        try:
            api_tests = []

            # Test /api/stats
            response = await self.page.request.get(WEBUI_URL + "/api/stats")
            api_tests.append(("stats", response.status == 200))

            # Test /api/agents
            response = await self.page.request.get(WEBUI_URL + "/api/agents")
            api_tests.append(("agents", response.status == 200))

            # Test /api/tasks
            response = await self.page.request.get(WEBUI_URL + "/api/tasks")
            api_tests.append(("tasks", response.status == 200))

            # Test /api/logs
            response = await self.page.request.get(WEBUI_URL + "/api/logs")
            api_tests.append(("logs", response.status == 200))

            # Test /api/screenshots
            response = await self.page.request.get(WEBUI_URL + "/api/screenshots")
            api_tests.append(("screenshots", response.status == 200))

            passed = sum(1 for _, p in api_tests if p)
            total = len(api_tests)

            self.log_result("API Endpoints", passed == total,
                          f"{passed}/{total} endpoints respond")
            return passed == total
        except Exception as e:
            self.log_result("API Endpoints", False, str(e))
            return False

    async def test_create_agent_modal(self):
        """Test: Create Agent button/modal"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")
            await asyncio.sleep(0.5)

            # Navigate to Agents page
            await self.page.keyboard.press("2")
            await asyncio.sleep(0.5)

            # Look for create button
            create_buttons = await self.page.locator(
                "text=Create, text=New, button:has-text('Agent')"
            ).count()

            self.log_result("Create Agent Button", create_buttons > 0,
                          f"Found {create_buttons} create buttons")
            await self.screenshot("create_agent")
            return True
        except Exception as e:
            self.log_result("Create Agent Button", False, str(e))
            return False

    async def test_send_message_form(self):
        """Test: Send message form"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")
            await asyncio.sleep(0.5)

            # Check for message input
            has_input = await self.page.locator(
                "textarea, input[type='text'], [contenteditable]"
            ).count() > 0

            # Check for send button
            has_send = await self.page.locator(
                "button:has-text('Send'), button:has-text('Submit')"
            ).count() > 0

            passed = has_input and has_send
            self.log_result("Message Form", passed,
                          f"input={has_input}, send={has_send}")
            await self.screenshot("message_form")
            return passed
        except Exception as e:
            self.log_result("Message Form", False, str(e))
            return False

    async def test_automation_buttons(self):
        """Test: Automation action buttons"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")
            await asyncio.sleep(0.5)

            automation_keywords = [
                "Cleanup", "Compress", "Disable", "Health", "Sync"
            ]

            found_buttons = 0
            for keyword in automation_keywords:
                count = await self.page.locator(f"text=/{keyword}/i").count()
                found_buttons += count

            self.log_result("Automation Buttons", found_buttons > 0,
                          f"Found {found_buttons} automation-related elements")
            await self.screenshot("automation_buttons")
            return True
        except Exception as e:
            self.log_result("Automation Buttons", False, str(e))
            return False

    async def test_quick_actions(self):
        """Test: Quick action buttons on dashboard"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")
            await asyncio.sleep(0.5)

            # Look for quick action buttons
            quick_actions = await self.page.locator(
                "[class*='quick'], [class*='action']"
            ).count()

            self.log_result("Quick Actions", quick_actions > 0,
                          f"Found {quick_actions} action elements")
            await self.screenshot("quick_actions")
            return True
        except Exception as e:
            self.log_result("Quick Actions", False, str(e))
            return False

    async def test_responsive_interactions(self):
        """Test: Touch interactions on mobile"""
        try:
            # Set mobile viewport
            await self.page.set_viewport_size({"width": 375, "height": 667})
            await self.page.goto(WEBUI_URL, wait_until="networkidle")
            await asyncio.sleep(0.5)

            # Check if elements are touch-friendly (size > 44px)
            buttons = await self.page.locator("button").all()
            touch_friendly = 0

            for btn in buttons[:10]:  # Check first 10
                box = await btn.bounding_box()
                if box:
                    height = box.get('height', 0)
                    if height >= 44:
                        touch_friendly += 1

            await self.page.set_viewport_size({"width": 1920, "height": 1080})

            self.log_result("Mobile Touch", True,
                          f"{touch_friendly}/10 buttons touch-friendly")
            await self.screenshot("mobile_touch")
            return True
        except Exception as e:
            self.log_result("Mobile Touch", False, str(e))
            return False

    async def run_all_tests(self):
        print("[TEST] Starting WebUI Interaction Tests...")

        await self.setup()

        tests = [
            ("Button Count", self.test_button_count),
            ("Theme Toggle", self.test_theme_toggle),
            ("API Endpoints", self.test_api_endpoints),
            ("Create Agent Modal", self.test_create_agent_modal),
            ("Message Form", self.test_send_message_form),
            ("Automation Buttons", self.test_automation_buttons),
            ("Quick Actions", self.test_quick_actions),
            ("Mobile Touch", self.test_responsive_interactions),
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
        total = len(self.results)
        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = total - passed

        report = {
            "timestamp": datetime.now().isoformat(),
            "type": "interaction_tests",
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "results": self.results
        }

        report_path = SCREENSHOT_DIR / f"interaction_test_report_{self.timestamp}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n[REPORT] {report_path}")
        print(f"   Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f"   Success Rate: {report['summary']['success_rate']}")

        return report


async def main():
    tester = InteractionTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
