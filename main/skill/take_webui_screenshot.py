#!/usr/bin/env python3
"""WebUI 截图工具 - 使用 Playwright 截取当前 WebUI 状态"""

import asyncio
import os
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright
except ImportError:
    print("错误：未安装 playwright")
    print("运行: pip install playwright")
    print("运行: python -m playwright install chromium")
    exit(1)

SCREENSHOT_DIR = Path("D:/loopcli/main/memory/webui_screenshots")
WEBUI_URL = "http://localhost:8080/"

async def take_screenshot():
    """截取 WebUI 截图"""
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    screenshot_path = SCREENSHOT_DIR / f"webui_{timestamp}.png"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        try:
            await page.goto(WEBUI_URL, wait_until="networkidle", timeout=10000)
            await page.screenshot(path=str(screenshot_path), full_page=True)
            print(f"[OK] Screenshot saved: {screenshot_path}")
            return str(screenshot_path)
        except Exception as e:
            print(f"[ERROR] Screenshot failed: {e}")
            return None
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(take_screenshot())
