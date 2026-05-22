# LoopCLI 记忆

## 2026-05-22 轮次329

**WebUI 关键Bug修复**：
- **图表区域越界**：Agent状态分布/任务进度/用量统计面板在所有页面div之外，导致每个页面都显示重复内容。修复：将widgets移入page-agents内
- **Agent状态标签汉化**：raw状态(idle/disabled)改为中文(空闲/已禁用)
- **日志过滤修复**：原有filter条件正确，日志实际可加载50条（之前空是因为HTML缓存）
- **Playwright 34/34全通过**：导航6页、Agent卡片、状态标签、图表归属、日志条目、6个API端点、零JS错误

**经验**：HTML中div嵌套错误会导致内容在多个页面重复显示。用`element.closest('.page')?.id`验证元素归属非常有效。

## 2026-05-22 轮次327

**WebUI 布局优化 + Playwright全面测试**：
- Agent卡片前置，按钮ID补全，Playwright 38/38全通过
- 经验：Playwright full_page=True会截取所有隐藏页面元素

## 2026-05-22 轮次324

**WebUI 性能页修复**：
- Token趋势图空数据根因：`/api/usage/trend`返回`{data:[...]}`但代码用`Array.isArray()`检查
- ChartManager冲突：RealTimeChartUpdater每10秒覆盖真实图表
- 经验：API返回`{data:[...]}`包装时，JS端必须兼容数组和对象两种格式
