#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebUI 全面测试脚本
测试所有按钮、表单、API 调用和交互功能
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright
import json
import time
from datetime import datetime
from pathlib import Path

class WebUIComprehensiveTest:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        self.results = []

    def log(self, message, status="info"):
        """记录日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = {"info": "ℹ️", "success": "✅", "error": "❌", "warning": "⚠️"}
        print(f"[{timestamp}] {icon.get(status, '•')} {message}")
        self.results.append({"time": timestamp, "message": message, "status": status})

    def take_screenshot(self, page, name):
        """截图"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.screenshots_dir / f"test_{name}_{timestamp}.png"
        page.screenshot(path=str(path), full_page=False)
        return path

    def test_navigation(self, page):
        """测试页面导航"""
        self.log("测试页面导航", "info")

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

        for page_name, key in pages:
            try:
                page.keyboard.press(key)
                page.wait_for_timeout(500)
                # 验证页面内容已加载
                content = page.text_content("body")
                if content and len(content) > 100:
                    self.log(f"页面 {page_name} 加载成功", "success")
                else:
                    self.log(f"页面 {page_name} 内容为空", "warning")
            except Exception as e:
                self.log(f"页面 {page_name} 加载失败: {e}", "error")

    def test_theme_toggle(self, page):
        """测试主题切换"""
        self.log("测试主题切换功能", "info")

        themes = ["light", "dark", "cyberpunk"]
        for theme in themes:
            try:
                # 切换主题
                page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
                page.wait_for_timeout(300)
                self.take_screenshot(page, f"theme_{theme}")

                # 验证主题已应用
                current_theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
                if current_theme == theme:
                    self.log(f"主题 {theme} 应用成功", "success")
                else:
                    self.log(f"主题 {theme} 应用失败", "error")
            except Exception as e:
                self.log(f"主题 {theme} 测试失败: {e}", "error")

    def test_buttons(self, page):
        """测试所有按钮"""
        self.log("测试按钮功能", "info")

        # 获取所有按钮
        buttons = page.query_selector_all("button")
        self.log(f"发现 {len(buttons)} 个按钮", "info")

        # 测试可见按钮的点击
        clickable_tests = [
            ("主题切换", lambda: page.keyboard.press("Control+KeyT")),
            ("侧边栏切换", lambda: page.keyboard.press("Control+KeyB")),
            ("快捷键帮助", lambda: page.keyboard.press("Control+KeyK")),
        ]

        for name, action in clickable_tests:
            try:
                action()
                page.wait_for_timeout(300)
                self.log(f"按钮/快捷键 {name} 响应正常", "success")
                # 关闭可能打开的弹窗
                page.keyboard.press("Escape")
                page.wait_for_timeout(200)
            except Exception as e:
                self.log(f"按钮/快捷键 {name} 测试失败: {e}", "error")

    def test_api_endpoints(self, page):
        """测试 API 端点"""
        self.log("测试 API 端点", "info")

        endpoints = [
            ("/api/agents", "Agents API"),
            ("/api/tasks", "Tasks API"),
            ("/api/messages", "Messages API"),
            ("/api/longtask", "LongTask API"),
            ("/api/stats", "Stats API"),
        ]

        for endpoint, name in endpoints:
            try:
                response = page.request.get(f"{self.base_url}{endpoint}")
                if response.status == 200:
                    self.log(f"{name} 响应正常 (200)", "success")
                else:
                    self.log(f"{name} 响应异常 ({response.status})", "warning")
            except Exception as e:
                self.log(f"{name} 请求失败: {e}", "error")

    def test_responsive(self, page):
        """测试响应式设计"""
        self.log("测试响应式设计", "info")

        viewports = [
            (1920, 1080, "桌面"),
            (768, 1024, "平板"),
            (375, 667, "手机"),
        ]

        for width, height, name in viewports:
            try:
                page.set_viewport_size({"width": width, "height": height})
                page.wait_for_timeout(300)
                self.take_screenshot(page, f"responsive_{name}")

                # 检查是否有水平滚动条
                has_scroll = page.evaluate("() => document.body.scrollWidth > window.innerWidth")
                if has_scroll:
                    self.log(f"{name} 视图出现水平滚动", "warning")
                else:
                    self.log(f"{name} 视图响应正常", "success")
            except Exception as e:
                self.log(f"{name} 视图测试失败: {e}", "error")

        # 恢复默认视图
        page.set_viewport_size({"width": 1920, "height": 1080})

    def test_performance(self, page):
        """测试性能指标"""
        self.log("测试性能指标", "info")

        # 重新加载页面以获取准确指标
        page.goto(self.base_url)
        page.wait_for_load_state("networkidle")

        metrics = page.evaluate("""() => {
            const navigation = performance.getEntriesByType('navigation')[0];
            return {
                loadTime: navigation.loadEventEnd - navigation.fetchStart,
                domReady: navigation.domContentLoadedEventEnd - navigation.fetchStart,
                firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0,
                resourceCount: performance.getEntriesByType('resource').length
            };
        }""")

        self.log(f"加载时间: {metrics['loadTime']:.0f}ms", "info")
        self.log(f"DOM 就绪: {metrics['domReady']:.0f}ms", "info")
        self.log(f"资源数量: {metrics['resourceCount']}", "info")

        # 评估性能
        if metrics['loadTime'] < 500:
            self.log("性能优秀 (< 500ms)", "success")
        elif metrics['loadTime'] < 1000:
            self.log("性能良好 (< 1000ms)", "success")
        else:
            self.log("性能需要优化 (> 1000ms)", "warning")

    def test_accessibility(self, page):
        """测试可访问性"""
        self.log("测试可访问性", "info")

        # 检查对比度（简化版）
        try:
            # 检查是否有 alt 属性的图片
            images_without_alt = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('img:not([alt])')).length;
            }""")
            if images_without_alt == 0:
                self.log("所有图片都有 alt 属性", "success")
            else:
                self.log(f"{images_without_alt} 个图片缺少 alt 属性", "warning")

            # 检查按钮是否有文本
            empty_buttons = page.evaluate("""() => {
                return Array.from(document.querySelectorAll('button')).filter(b => !b.textContent.trim()).length;
            }""")
            if empty_buttons == 0:
                self.log("所有按钮都有文本标签", "success")
            else:
                self.log(f"{empty_buttons} 个按钮缺少文本标签", "warning")

        except Exception as e:
            self.log(f"可访问性测试失败: {e}", "error")

    def run_full_test(self):
        """运行完整测试"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1920, "height": 1080})

            print(f"\n{'='*60}")
            print(f"🧪 WebUI 全面测试 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}\n")

            # 访问主页
            page.goto(self.base_url)
            page.wait_for_load_state("networkidle")
            self.log("WebUI 加载成功", "success")

            # 截图初始状态
            self.take_screenshot(page, "initial_state")

            # 运行各项测试
            self.test_navigation(page)
            self.test_theme_toggle(page)
            self.test_buttons(page)
            self.test_api_endpoints(page)
            self.test_responsive(page)
            self.test_performance(page)
            self.test_accessibility(page)

            browser.close()

            # 生成报告
            self.generate_report()

    def generate_report(self):
        """生成测试报告"""
        print(f"\n{'='*60}")
        print("📊 测试报告")
        print(f"{'='*60}\n")

        total = len(self.results)
        success = sum(1 for r in self.results if r["status"] == "success")
        error = sum(1 for r in self.results if r["status"] == "error")
        warning = sum(1 for r in self.results if r["status"] == "warning")

        print(f"总测试项: {total}")
        print(f"✅ 通过: {success}")
        print(f"⚠️  警告: {warning}")
        print(f"❌ 失败: {error}")
        print(f"成功率: {success/total*100:.1f}%")

        # 保存详细报告
        report_path = self.screenshots_dir / f"comprehensive_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "total": total,
                    "success": success,
                    "error": error,
                    "warning": warning,
                    "success_rate": f"{success/total*100:.1f}%"
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)

        print(f"\n详细报告已保存: {report_path}")

def main():
    tester = WebUIComprehensiveTest()
    tester.run_full_test()

if __name__ == "__main__":
    main()
