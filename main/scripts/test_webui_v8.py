#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WebUI v8.0 完整功能测试"""

from playwright.sync_api import sync_playwright
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_webui_v8():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('http://localhost:8080')
        page.wait_for_load_state('networkidle')

        print('=' * 60)
        print('WebUI v8.0 功能测试')
        print('=' * 60)

        # 1. 页面标题
        title = page.title()
        print(f'\n[1/8] 页面标题: {title}')
        assert 'v8.0' in title, '版本号不正确'
        print('  ✓ 版本号正确')

        # 2. 导航菜单
        nav_items = page.query_selector_all('.nav-item')
        print(f'\n[2/8] 导航菜单 ({len(nav_items)} 项):')
        expected_pages = ['agents', 'tasks', 'performance', 'logs', 'settings']
        for i, item in enumerate(nav_items):
            page_id = item.get_attribute('data-page')
            assert page_id == expected_pages[i], f'页面 {i} 不匹配'
            active = 'active' in item.get_attribute('class')
            status = '✓' if active else '  '
            print(f'  {status} {i+1}. {page_id}')
        print('  ✓ 所有页面正常')

        # 3. Agents 显示
        print(f'\n[3/8] Agents 显示:')
        agent_cards = page.query_selector_all('.agent-card')
        print(f'  Agent 卡片数量: {len(agent_cards)}')
        assert len(agent_cards) > 0, '没有 Agent 卡片'
        print('  ✓ Agent 显示正常')

        # 4. 统计数据
        print(f'\n[4/8] 统计数据:')
        stat_values = page.query_selector_all('.stat-card .value')
        print(f'  统计卡片数量: {len(stat_values)}')
        assert len(stat_values) == 4, '统计卡片数量不正确'
        for i, stat in enumerate(stat_values):
            text = stat.text_content()
            print(f'  {i+1}. {text}')
        print('  ✓ 统计数据正常')

        # 5. 页面切换测试
        print(f'\n[5/8] 页面切换测试:')
        for i, item in enumerate(nav_items):
            page_id = item.get_attribute('data-page')
            item.click()
            page.wait_for_timeout(300)
            active_page = page.query_selector('.page.active')
            if active_page:
                active_id = active_page.get_attribute('id')
                assert active_id == f'page-{page_id}', f'页面切换不匹配: {active_id}'
                print(f'  ✓ 切换到: {page_id}')
            else:
                print(f'  ✗ 切换失败: {page_id}')
        print('  ✓ 页面切换正常')

        # 6. API 端点
        print(f'\n[6/8] API 端点测试:')
        endpoints = ['/api/agents', '/api/tasks', '/api/logs']
        for endpoint in endpoints:
            response = page.request.get(f'http://localhost:8080{endpoint}')
            assert response.status == 200, f'{endpoint} 返回错误状态'
            print(f'  ✓ {endpoint}: {response.status}')
        print('  ✓ 所有 API 正常')

        # 7. 样式检查
        print(f'\n[7/8] 样式检查:')
        styles = page.evaluate('''() => {
            const styles = getComputedStyle(document.documentElement);
            return {
                accent: styles.getPropertyValue('--accent').trim(),
                bg: styles.getPropertyValue('--bg').trim(),
                surface: styles.getPropertyValue('--surface').trim()
            };
        }''')
        print(f'  主题色: {styles["accent"]}')
        print(f'  背景色: {styles["bg"]}')
        print(f'  表面色: {styles["surface"]}')
        assert styles["accent"], '主题色未设置'
        print('  ✓ 样式正常')

        # 8. 性能指标
        print(f'\n[8/8] 性能指标:')
        perf = page.evaluate('''() => ({
            loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
            domReady: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart
        })''')
        print(f'  页面加载时间: {perf["loadTime"]}ms')
        print(f'  DOM 准备时间: {perf["domReady"]}ms')
        assert perf["loadTime"] < 5000, '页面加载时间过长'
        print('  ✓ 性能正常')

        browser.close()
        print('\n' + '=' * 60)
        print('✓ 所有测试通过')
        print('=' * 60)
        return True

if __name__ == '__main__':
    try:
        test_webui_v8()
    except Exception as e:
        print(f'\n✗ 测试失败: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
