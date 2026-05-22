# LoopCLI 记忆

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
