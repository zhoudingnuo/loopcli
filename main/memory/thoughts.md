# LoopCLI 记忆

## 2026-05-22 轮次327

**WebUI 布局优化 + Playwright全面测试**：
- **Agent卡片前置**：原来Agent列表在页面最底部（图表和用量之后），用户需要大量滚动。重排后顺序：统计卡片→长期任务→Agent列表→图表→用量统计，视口内可见2个Agent卡片（之前0个）
- **按钮ID补全**：给创建Agent、刷新、导出按钮添加了id属性，便于测试和交互
- **Playwright测试38/38全部通过**：导航6页、Agent卡片、搜索、所有按钮、性能指标、设置主题、6个API端点、长期任务卡片
- **确认非bug项**：Token格式实际正确(266,973,354)、任务页空是因tasks.json无数据、Token趋势图有渲染但需滚动查看
- **性能页结构**：page-performance与page-agents分离正确，full_page截图会包含隐藏页面导致分析误导

**经验**：Playwright full_page=True会截取所有隐藏页面元素，分析截图时要用viewport-only截图。测试按钮时用page.evaluate()调用JS关闭函数比找DOM元素更可靠。

## 2026-05-22 轮次324

**WebUI 深度优化 — 性能页面修复**：
- **Token趋势图空数据根因**：`/api/usage/trend` 返回 `{data:[...]}` 但 `loadPerformance()` 用 `Array.isArray(trendData)` 检查，永远为 false。修复：`Array.isArray(trendRaw) ? trendRaw : (trendRaw.data || [])`
- **ChartManager冲突**：`main.js` 的 `ChartManager.initTokenTrend()` 用 `RealTimeChartUpdater` 每10秒用随机数据覆盖真实图表。修复：从 `initAll()` 移除 `token-trend-chart`
- **响应时间/Token消耗**：改为用 `performance.now()` 测量实际 API 延迟，Token 从 `/api/usage` 读取
- **稀疏数据处理**：7天趋势中6天为0时显示 "近7天暂无显著任务数据"
- **主题切换**：Settings 页面用 `<select id="theme-selector">`，不是 `data-theme-btn` 按钮
- Playwright 测试 21/23 通过，修复后 100% 通过，零 JS 错误

**经验**：API 返回 `{data:[...]}` 包装是常见模式，JS 端必须兼容数组和对象两种格式。多个组件操作同一 canvas 会互相覆盖。

## 2026-05-22 轮次323

**WebUI用量统计增强**：
- 后端query_usage_summary()新增weekly字段（7天Token/调用统计），独立try不影响主数据
- 前端新增彩色进度条（barColor用硬编码hex色值，不用CSS变量以确保可见性）
- 经验：进度条CSS变量(var(--green))在某些场景下不可见，用硬编码hex色值更可靠
