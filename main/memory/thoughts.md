# LoopCLI 记忆

## 2026-05-22 轮次315

**WebUI深度优化**：
- 修复Logs页面关键bug：API返回`{lines:[...]}`对象但JS当数组用，导致`logs.slice is not a function`
- Playwright 6/6页面全部通过，零console错误
- 所有按钮功能正常：搜索、创建任务、长期任务编辑/取消、主题切换、刷新
- 5个API端点全部200 OK

**技术要点**：Logs API返回`{agent:null, lines:["|time|status|task|msg|"]}`格式，需要提取lines并解析表格行

**成本控制**：所有agent保持disabled，无空闲agent浪费
