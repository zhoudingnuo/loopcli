"""
Extract cookies from Edge and save to tmg CLI cookie file
"""
import asyncio
import os
import json
from playwright.async_api import async_playwright

EDGE_USER_DATA = r"C:\Users\Administrator\AppData\Local\Microsoft\Edge\User Data"
COOKIE_FILE = os.path.join(os.path.expanduser("~"), ".tmg-cli", ".cookies")

async def main():
    async with async_playwright() as p:
        print("[1] Launch Edge to extract cookies...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=EDGE_USER_DATA,
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 900},
        )

        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Navigate to developer platform to ensure domain cookies are loaded
        print("[2] Navigate to developer platform...")
        await page.goto("https://developer.open-douyin.com/console?type=1",
                        wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(3000)

        # Get cookies for the developer domain
        print("[3] Extracting cookies...")
        cookies = await browser.cookies(["https://developer.open-douyin.com",
                                          "https://developer.toutiao.com",
                                          "https://microapp.bytedance.com"])

        print(f"  Found {len(cookies)} cookies")

        # Format cookies as cookie string (name=value; name=value)
        cookie_parts = []
        for c in cookies:
            print(f"  {c['name']}={c['value'][:20]}... (domain: {c.get('domain', '')})")
            cookie_parts.append(f"{c['name']}={c['value']}")

        cookie_string = "; ".join(cookie_parts)

        # Save to tmg cookie file
        print(f"[4] Saving cookies to {COOKIE_FILE}...")
        os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
        with open(COOKIE_FILE, "w", encoding="utf-8") as f:
            f.write(cookie_string + "\n")

        print(f"[Done] Cookies saved ({len(cookie_string)} chars)")

        # Also save raw cookies as JSON for reference
        with open(os.path.join(os.path.dirname(COOKIE_FILE), "cookies_debug.json"), "w") as f:
            json.dump(cookies, f, indent=2)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
