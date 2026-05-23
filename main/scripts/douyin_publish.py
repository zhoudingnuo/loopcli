"""
抖音小游戏发布 - v7: 用JS直接操作表格找到游戏并点击操作按钮
"""
import asyncio
import os
from playwright.async_api import async_playwright

EDGE_USER_DATA = r"C:\Users\Administrator\AppData\Local\Microsoft\Edge\User Data"
SS = "D:/loopcli/main/report"
APP_ID = "tte7a1911c79c6fc8302"
GAME_ZIP = "D:/games/match3-xiaoxiaoxiao.zip"
BASE_URL = "https://developer.open-douyin.com"

def sp(text):
    try: print(text)
    except: print(text.encode("gbk", errors="replace").decode("gbk"))

async def main():
    async with async_playwright() as p:
        print("[1] Launch Edge...")
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=EDGE_USER_DATA,
            channel="msedge",
            headless=False,
            viewport={"width": 1280, "height": 900},
            locale="zh-CN",
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        # Navigate to game management
        print("[2] Open game management...")
        await page.goto(f"{BASE_URL}/game-console/1065926/game-manage",
                        wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(10000)  # Wait for table to load

        # Use JS to analyze the page structure and find the game
        print("[3] Analyze page with JS...")
        page_info = await page.evaluate("""() => {
            const result = {texts: [], links: [], tableRows: [], actionButtons: []};

            // Find all visible text content that contains game name or AppID
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
            while (walker.nextNode()) {
                const text = walker.currentNode.textContent.trim();
                if (text.includes('消消消') || text.includes('tte7a1911c79c6fc8302') || text.includes('match3')) {
                    const parent = walker.currentNode.parentElement;
                    result.texts.push({
                        text: text.substring(0, 100),
                        tag: parent?.tagName,
                        class: parent?.className?.substring(0, 60),
                        visible: parent?.offsetParent !== null
                    });
                }
            }

            // Find all links
            document.querySelectorAll('a[href]').forEach(a => {
                if (a.offsetParent !== null) {
                    result.links.push({
                        text: a.textContent?.trim()?.substring(0, 50),
                        href: a.href
                    });
                }
            });

            // Find table rows
            document.querySelectorAll('tr, [class*="table-row"], [class*="semi-table-row"]').forEach(row => {
                const text = row.textContent?.trim() || '';
                if (text.includes('消消消') || text.includes('tte7a1911c79c6fc8302')) {
                    result.tableRows.push(text.substring(0, 300));
                    // Find action buttons in this row
                    row.querySelectorAll('a, button, [role="button"], span[class*="link"], span[class*="action"]').forEach(btn => {
                        if (btn.offsetParent !== null) {
                            result.actionButtons.push({
                                text: btn.textContent?.trim()?.substring(0, 30),
                                tag: btn.tagName,
                                href: btn.href || '',
                                class: btn.className?.substring(0, 60)
                            });
                        }
                    });
                }
            });

            // Also check for any element with "操作" or "管理" text near game
            document.querySelectorAll('[class*="semi-table"]').forEach(table => {
                const cells = table.querySelectorAll('td, [class*="semi-table-td"]');
                cells.forEach(cell => {
                    const text = cell.textContent?.trim() || '';
                    if (text.length < 30 && text.length > 0) {
                        const links = cell.querySelectorAll('a, button');
                        links.forEach(l => {
                            result.actionButtons.push({
                                text: l.textContent?.trim()?.substring(0, 30),
                                tag: l.tagName,
                                href: l.href || '',
                                class: l.className?.substring(0, 60),
                                cellContext: text
                            });
                        });
                    }
                });
            });

            return result;
        }""")

        sp(f"  Found {len(page_info['texts'])} text matches")
        for t in page_info['texts']:
            sp(f"    Text: '{t['text'][:50]}' [{t['tag']}] vis={t['visible']}")
        sp(f"  Found {len(page_info['links'])} links")
        for l in page_info['links'][:10]:
            sp(f"    Link: '{l['text'][:30]}' -> {l['href'][:60]}")
        sp(f"  Found {len(page_info['tableRows'])} table rows")
        for r in page_info['tableRows'][:3]:
            sp(f"    Row: {r[:100]}")
        sp(f"  Found {len(page_info['actionButtons'])} action buttons")
        for b in page_info['actionButtons'][:10]:
            sp(f"    Action: [{b['tag']}] '{b['text']}' href={b.get('href','')[:40]}")

        await page.screenshot(path=f"{SS}/v7_step1.png")

        # Try to click on the game operation button
        print("[4] Try clicking game operations...")
        clicked = await page.evaluate("""() => {
            // Strategy 1: Find table row with game name, then find action link
            const rows = document.querySelectorAll('tr, [class*="semi-table-row"]');
            for (const row of rows) {
                const text = row.textContent || '';
                if (text.includes('消消消') || text.includes('tte7a1911c79c6fc8302')) {
                    // Find all clickable elements in this row
                    const clickables = row.querySelectorAll('a, button, [role="button"], [class*="link"]');
                    const results = [];
                    for (const el of clickables) {
                        results.push({
                            text: el.textContent?.trim()?.substring(0, 30),
                            tag: el.tagName,
                            href: el.href || '',
                        });
                        // Click the first actionable element that looks like a manage/config link
                        if (el.offsetParent !== null) {
                            const t = el.textContent?.trim() || '';
                            if (t.includes('管理') || t.includes('配置') || t.includes('开发') || t.includes('版本') || t.includes('操作')) {
                                el.click();
                                return {clicked: true, text: t, tag: el.tagName, href: el.href || ''};
                            }
                        }
                    }
                    // If no specific button found, click any visible link in the row
                    for (const el of clickables) {
                        if (el.offsetParent !== null && el.textContent?.trim()) {
                            el.click();
                            return {clicked: true, text: el.textContent?.trim(), tag: el.tagName, href: el.href || '', fallback: true};
                        }
                    }
                    return {clicked: false, rowText: text.substring(0, 100), elements: results};
                }
            }

            // Strategy 2: Click on the game name directly
            const spans = document.querySelectorAll('span, a, div');
            for (const el of spans) {
                if (el.textContent?.trim() === '消消消大作战' && el.offsetParent !== null) {
                    el.click();
                    return {clicked: true, strategy: 'name_click', text: '消消消大作战'};
                }
            }

            return {clicked: false, reason: 'game not found in table'};
        }""")

        sp(f"  Click result: {clicked}")

        await page.wait_for_timeout(5000)
        await page.screenshot(path=f"{SS}/v7_step2_after_click.png")
        sp(f"  URL: {page.url}")

        # Check if we navigated to a new page or a panel opened
        if page.url != f"{BASE_URL}/game-console/1065926/game-manage?tab=game-manage":
            sp("  Page changed! Analyzing new page...")
            await page.wait_for_timeout(3000)

            # Look for version management on the new page
            for kw in ["版本管理", "版本", "开发版本", "上传", "代码管理"]:
                try:
                    loc = page.get_by_text(kw)
                    if await loc.count() > 0:
                        for i in range(await loc.count()):
                            if await loc.nth(i).is_visible():
                                sp(f"  Found '{kw}' on new page")
                                break
                except:
                    pass

        # Save final state
        await page.screenshot(path=f"{SS}/v7_final.png")
        html = await page.content()
        with open(f"{SS}/v7_final.html", "w", encoding="utf-8") as f:
            f.write(html)
        sp(f"\n[Done] Final URL: {page.url}")

        await page.wait_for_timeout(3000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
