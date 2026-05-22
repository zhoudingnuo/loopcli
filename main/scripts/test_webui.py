#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WebUI 功能测试脚本"""

from playwright.sync_api import sync_playwright
import json
import time
import sys
import io

# 设置输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_webui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("=" * 50)
        print("WebUI 功能测试开始")
        print("=" * 50)

        # 1. 访问首页
        print("\n[1/6] 访问首页...")
        page.goto('http://localhost:8080')
        page.wait_for_load_state('networkidle')
        title = page.title()
        print(f"  ✓ 页面标题: {title}")

        # 2. 获取导航菜单
        print("\n[2/6] 检查导航菜单...")
        nav_items = page.eval_on_selector_all('.nav-item', 'items => items.map(i => i.textContent)')
        print(f"  ✓ 导航菜单 ({len(nav_items)} 项):")
        for i, item in enumerate(nav_items, 1):
            print(f"    {i}. {item}")

        # 3. 检查 Agents 显示
        print("\n[3/6] 检查 Agents 显示...")
        agent_cards = page.query_selector_all('.agent-card')
        print(f"  ✓ Agent 卡片数量: {len(agent_cards)}")

        if agent_cards:
            for i, card in enumerate(agent_cards[:3], 1):
                try:
                    name = card.query_selector('.agent-name').text_content()
                    status = card.query_selector('.status-badge').text_content()
                    print(f"    Agent {i}: {name} - {status}")
                except:
                    pass

        # 4. 测试页面切换
        print("\n[4/6] 测试页面切换...")
        for i in range(min(3, len(nav_items))):
            try:
                page.click(f'.nav-item:nth-child({i+1})')
                page.wait_for_timeout(500)
                active = page.eval_on_selector('.nav-item.active', 'el => el.textContent')
                print(f"  ✓ 切换到: {active}")
            except Exception as e:
                print(f"  ✗ 切换失败: {e}")

        # 5. 检查 API 端点
        print("\n[5/6] 检查 API 端点...")
        api_endpoints = ['/api/agents', '/api/tasks', '/api/logs']
        for endpoint in api_endpoints:
            try:
                response = page.request.get(f'http://localhost:8080{endpoint}')
                print(f"  ✓ {endpoint}: {response.status}")
            except Exception as e:
                print(f"  ✗ {endpoint}: {e}")

        # 6. 性能指标
        print("\n[6/6] 性能指标...")
        metrics = page.evaluate('() => ({})')
        perf_timing = page.evaluate('() => performance.timing')
        load_time = perf_timing['loadEventEnd'] - perf_timing['navigationStart']
        print(f"  ✓ 页面加载时间: {load_time}ms")

        browser.close()
        print("\n" + "=" * 50)
        print("测试完成")
        print("=" * 50)

if __name__ == '__main__':
    test_webui()
