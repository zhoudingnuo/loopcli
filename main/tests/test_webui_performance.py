"""
WebUI Performance Tests
Measures load times, responsiveness, and resource usage.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

WEBUI_URL = "http://127.0.0.1:8080"
SCREENSHOT_DIR = Path("webui/screenshots")


class PerformanceTester:
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

    async def test_page_load_time(self):
        """Test: Initial page load time"""
        try:
            start = asyncio.get_event_loop().time()
            await self.page.goto(WEBUI_URL, wait_until="networkidle")
            end = asyncio.get_event_loop().time()

            load_time = (end - start) * 1000  # Convert to ms
            passed = load_time < 2000  # Should load in under 2 seconds

            self.log_result("Page Load Time", passed,
                          f"{load_time:.0f}ms (target: <2000ms)")
            return passed
        except Exception as e:
            self.log_result("Page Load Time", False, str(e))
            return False

    async def test_navigation_speed(self):
        """Test: Navigation between pages"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")

            times = []
            pages = [1, 2, 3, 4, 5, 6]  # Dashboard, Agents, Tasks, Logs, Performance, Settings

            for page_num in pages:
                start = asyncio.get_event_loop().time()
                await self.page.keyboard.press(str(page_num))
                await self.page.wait_for_load_state("networkidle")
                end = asyncio.get_event_loop().time()
                times.append((end - start) * 1000)
                await asyncio.sleep(0.2)

            avg_time = sum(times) / len(times)
            passed = avg_time < 500  # Average navigation under 500ms

            self.log_result("Navigation Speed", passed,
                          f"Avg {avg_time:.0f}ms (target: <500ms)")
            return passed
        except Exception as e:
            self.log_result("Navigation Speed", False, str(e))
            return False

    async def test_api_response_time(self):
        """Test: API endpoint response times"""
        try:
            endpoints = [
                "/api/stats",
                "/api/agents",
                "/api/tasks",
                "/api/logs",
                "/api/screenshots"
            ]

            times = []
            for endpoint in endpoints:
                start = asyncio.get_event_loop().time()
                response = await self.page.request.get(WEBUI_URL + endpoint)
                await response.body()
                end = asyncio.get_event_loop().time()
                times.append((end - start) * 1000)

            avg_time = sum(times) / len(times)
            passed = avg_time < 200  # Average API response under 200ms

            self.log_result("API Response Time", passed,
                          f"Avg {avg_time:.0f}ms (target: <200ms)")
            return passed
        except Exception as e:
            self.log_result("API Response Time", False, str(e))
            return False

    async def test_theme_switch_speed(self):
        """Test: Theme switching performance"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")

            themes = ["light", "dark", "cyberpunk"]
            times = []

            for theme in themes:
                start = asyncio.get_event_loop().time()
                await self.page.evaluate(
                    f"document.documentElement.setAttribute('data-theme', '{theme}')"
                )
                # Wait for paint
                await self.page.wait_for_selector("body")
                end = asyncio.get_event_loop().time()
                times.append((end - start) * 1000)

            avg_time = sum(times) / len(times)
            passed = avg_time < 100  # Theme switch should be instant

            self.log_result("Theme Switch Speed", passed,
                          f"Avg {avg_time:.0f}ms (target: <100ms)")
            return passed
        except Exception as e:
            self.log_result("Theme Switch Speed", False, str(e))
            return False

    async def test_memory_stability(self):
        """Test: Memory usage over multiple page loads"""
        try:
            # Load pages multiple times
            for i in range(10):
                await self.page.goto(WEBUI_URL, wait_until="networkidle")
                for key in ["1", "2", "3", "4"]:
                    await self.page.keyboard.press(key)
                    await asyncio.sleep(0.1)

            # If we get here without crash, test passes
            self.log_result("Memory Stability", True,
                          "10 page load cycles completed")
            return True
        except Exception as e:
            self.log_result("Memory Stability", False, str(e))
            return False

    async def test_responsive_resize(self):
        """Test: Responsive layout changes"""
        try:
            await self.page.goto(WEBUI_URL, wait_until="networkidle")

            sizes = [
                (1920, 1080),  # Desktop
                (768, 1024),   # Tablet
                (375, 667),    # Mobile
                (1920, 1080)   # Back to desktop
            ]

            times = []
            for width, height in sizes:
                start = asyncio.get_event_loop().time()
                await self.page.set_viewport_size({"width": width, "height": height})
                await self.page.wait_for_selector("body")
                end = asyncio.get_event_loop().time()
                times.append((end - start) * 1000)

            avg_time = sum(times) / len(times)
            passed = avg_time < 200  # Resize should be smooth

            self.log_result("Responsive Resize", passed,
                          f"Avg {avg_time:.0f}ms (target: <200ms)")
            return passed
        except Exception as e:
            self.log_result("Responsive Resize", False, str(e))
            return False

    async def run_all_tests(self):
        print("[TEST] Starting WebUI Performance Tests...")

        await self.setup()

        tests = [
            ("Page Load Time", self.test_page_load_time),
            ("Navigation Speed", self.test_navigation_speed),
            ("API Response Time", self.test_api_response_time),
            ("Theme Switch Speed", self.test_theme_switch_speed),
            ("Memory Stability", self.test_memory_stability),
            ("Responsive Resize", self.test_responsive_resize),
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
            "type": "performance_tests",
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": f"{(passed/total*100):.1f}%" if total > 0 else "0%"
            },
            "results": self.results
        }

        report_path = SCREENSHOT_DIR / f"performance_test_report_{self.timestamp}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"\n[REPORT] {report_path}")
        print(f"   Total: {total} | Passed: {passed} | Failed: {failed}")
        print(f"   Success Rate: {report['summary']['success_rate']}")

        return report


async def main():
    tester = PerformanceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
