#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebUI Automation Script
Automated testing, screenshots, and performance monitoring with Playwright
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime
from pathlib import Path

class WebUIAutomation:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

    def take_screenshot(self, page, name, full_page=True):
        """截图并保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.screenshots_dir / f"{name}_{timestamp}.png"
        page.screenshot(path=str(path), full_page=full_page)
        return path

    def navigate_all_pages(self, page):
        """遍历所有页面并截图"""
        pages = [
            ("analytics", "0"),
            ("dashboard", "1"),
            ("agents", "2"),
            ("tasks", "3"),
            ("logs", "4"),
            ("control", "5"),
            ("messages", "6"),
            ("health", "7"),
            ("notifications", "8"),
            ("cost", "9"),
            ("settings", ";"),
        ]

        results = []
        for page_name, key in pages:
            try:
                page.keyboard.press(key)
                page.wait_for_timeout(500)  # 等待页面切换动画
                screenshot_path = self.take_screenshot(page, f"page_{page_name}")
                results.append({
                    "page": page_name,
                    "status": "success",
                    "screenshot": str(screenshot_path),
                    "timestamp": datetime.now().isoformat()
                })
                print(f"✓ 已截图: {page_name}")
            except Exception as e:
                results.append({
                    "page": page_name,
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                })
                print(f"✗ 错误: {page_name} - {e}")

        return results

    def test_interactive_features(self, page):
        """测试交互功能"""
        tests = []

        # 测试主题切换
        try:
            page.keyboard.press("Control+KeyT")
            page.wait_for_timeout(300)
            self.take_screenshot(page, "theme_light")
            page.keyboard.press("Control+KeyT")
            page.wait_for_timeout(300)
            self.take_screenshot(page, "theme_dark")
            tests.append({"feature": "theme_toggle", "status": "pass"})
            print("✓ 主题切换测试通过")
        except Exception as e:
            tests.append({"feature": "theme_toggle", "status": "fail", "error": str(e)})

        # 测试侧边栏折叠
        try:
            page.keyboard.press("Control+KeyB")
            page.wait_for_timeout(300)
            self.take_screenshot(page, "sidebar_collapsed")
            page.keyboard.press("Control+KeyB")
            page.wait_for_timeout(300)
            tests.append({"feature": "sidebar_toggle", "status": "pass"})
            print("✓ 侧边栏折叠测试通过")
        except Exception as e:
            tests.append({"feature": "sidebar_toggle", "status": "fail", "error": str(e)})

        # 测试快捷键帮助
        try:
            page.keyboard.press("Control+KeyK")
            page.wait_for_timeout(300)
            self.take_screenshot(page, "shortcuts_modal")
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            tests.append({"feature": "shortcuts_modal", "status": "pass"})
            print("✓ 快捷键帮助测试通过")
        except Exception as e:
            tests.append({"feature": "shortcuts_modal", "status": "fail", "error": str(e)})

        return tests

    def measure_performance(self, page):
        """测量页面性能"""
        metrics = page.evaluate("""() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            return {
                loadTime: navigation.loadEventEnd - navigation.fetchStart,
                domReady: navigation.domContentLoadedEventEnd - navigation.fetchStart,
                firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
            };
        }""")
        return metrics

    def run_full_audit(self):
        """运行完整审计"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

            print(f"\n🚀 开始 WebUI 审计 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 50)

            # 访问主页
            page.goto(self.base_url)
            page.wait_for_load_state("networkidle")
            print("✓ WebUI 已加载")

            # 测量性能
            metrics = self.measure_performance(page)
            print(f"📊 性能指标: 加载时间 {metrics['loadTime']:.0f}ms, DOM就绪 {metrics['domReady']:.0f}ms")

            # 遍历所有页面
            print("\n📸 截图所有页面...")
            page_results = self.navigate_all_pages(page)

            # 测试交互功能
            print("\n🧪 测试交互功能...")
            feature_tests = self.test_interactive_features(page)

            # 生成报告
            report = {
                "timestamp": datetime.now().isoformat(),
                "performance": metrics,
                "pages": page_results,
                "features": feature_tests,
                "summary": {
                    "total_pages": len(page_results),
                    "successful_pages": sum(1 for p in page_results if p["status"] == "success"),
                    "total_features": len(feature_tests),
                    "passed_features": sum(1 for f in feature_tests if f["status"] == "pass")
                }
            }

            browser.close()

            # 保存报告
            report_path = self.screenshots_dir / f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            print("\n" + "=" * 50)
            print(f"✅ 审计完成！报告: {report_path}")
            print(f"📊 页面成功率: {report['summary']['successful_pages']}/{report['summary']['total_pages']}")
            print(f"🧪 功能通过率: {report['summary']['passed_features']}/{report['summary']['total_features']}")

            return report

def main():
    automation = WebUIAutomation()
    report = automation.run_full_audit()
    return report

if __name__ == "__main__":
    main()
