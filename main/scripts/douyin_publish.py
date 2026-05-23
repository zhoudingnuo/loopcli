"""
抖音小游戏发布自动化脚本 - v3
使用 domcontentloaded 而非 networkidle 避免超时
"""
import asyncio
import os
import sys
import json
import subprocess
from pathlib import Path
from playwright.async_api import async_playwright

GAME_DIR = "D:/games/match3-xiaoxiaoxiao"
CONSOLE_URL = "https://developer.open-douyin.com/console?type=1"
EDGE_USER_DATA = r"C:\Users\Administrator\AppData\Local\Microsoft\Edge\User Data"
SCREENSHOT_DIR = "D:/loopcli/main/report"
APP_ID = "tte7a1911c79c6fc8302"

async def main():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)

    # 关闭现有 Edge 进程
    print("[0] 关闭现有 Edge 进程...")
    subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"], capture_output=True)
    await asyncio.sleep(3)

    async with async_playwright() as p:
        print("[1] 启动 Edge...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=EDGE_USER_DATA,
            channel="msedge",
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        # 导航到开发者控制台
        print("[2] 导航到开发者控制台...")
        try:
            await page.goto(CONSOLE_URL, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"  导航警告: {e}")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/douyin_step1_console.png")
        print(f"  截图: douyin_step1_console.png, URL: {page.url}")

        # 检查是否需要登录
        if "login" in page.url.lower() or "passport" in page.url.lower():
            print("  [!] 需要登录，等待60秒请手动扫码...")
            await page.wait_for_timeout(60000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/douyin_after_login.png")
            print(f"  URL: {page.url}")

        # 导航到版本管理页面
        print("[3] 进入版本管理...")
        version_url = f"https://developer.open-douyin.com/console/miniapp/{APP_ID}/version"
        try:
            await page.goto(version_url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"  导航警告: {e}")
        await page.wait_for_timeout(5000)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/douyin_step2_version.png")
        print(f"  截图: douyin_step2_version.png, URL: {page.url}")

        # 保存页面HTML
        html_content = await page.content()
        with open(f"{SCREENSHOT_DIR}/douyin_version_page.html", "w", encoding="utf-8") as f:
            f.write(html_content)

        # 分析页面元素
        print("[4] 分析页面元素...")
        elements = await page.query_selector_all("button, a, [role='button'], span[class*='btn'], div[class*='upload']")
        for elem in elements:
            try:
                text = (await elem.text_content() or "").strip()
                tag = await elem.evaluate("el => el.tagName")
                cls = await elem.get_attribute("class") or ""
                if text and len(text) < 80:
                    print(f"  [{tag}] {text[:60]} | class={cls[:40]}")
            except:
                pass

        # 尝试不同的管理页面URL
        pages_to_try = [
            f"https://developer.open-douyin.com/console/miniapp/{APP_ID}",
            f"https://developer.open-douyin.com/console/miniapp/{APP_ID}/package",
            f"https://developer.open-douyin.com/console/miniapp/{APP_ID}/code",
        ]

        for url in pages_to_try:
            print(f"\n[尝试] {url}")
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            except:
                pass
            await page.wait_for_timeout(3000)
            await page.screenshot(path=f"{SCREENSHOT_DIR}/douyin_explore_{url.split('/')[-1] or 'index'}.png")
            print(f"  URL: {page.url}")

        # 最终截图
        await page.screenshot(path=f"{SCREENSHOT_DIR}/douyin_final.png")
        print(f"\n[完成] 所有截图已保存到 {SCREENSHOT_DIR}/")

        await page.wait_for_timeout(10000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
