# LoopCLI 记忆

## 2026-05-22 轮次335

**WebUI v8.7 深度优化**：
- 性能页响应时间：改为测量 /api/health（不再依赖 /api/usage），从"- ms"修复为实际值(106ms)
- Token消耗：显示"暂无"降级逻辑，当前显示290,589,950真实数据
- 搜索框与导出按钮：flex布局+min-width:0+white-space:nowrap，不再重叠
- 统计卡片标签：--text2从#9ca3af提升至#b0b8c4，对比度提升
- Agent卡片按钮：agent-actions添加justify-content:stretch，按钮均匀分布
- 长期任务文字：添加overflow-wrap:break-word+word-break:break-word，防截断
- Playwright 9/9全通过，API验证全部通过

## 2026-05-22 轮次333

**WebUI v8.6 深度优化**：
- 修复搜索框与导出按钮重叠（改为flex布局并列）
- 修复设置页长期任务编辑区结构错位（longtask-edit移入settings-section内）
- 自动刷新指示器移至右下角（避免与通知冲突）
- 移动端sidebar品牌文字缩小防截断
- 性能页面硬编码变化值改为动态ID
- Playwright 64/64全通过，零JS错误
