# LoopCLI 记忆

## 2026-05-22 轮次333

**WebUI v8.6 深度优化**：
- 修复搜索框与导出按钮重叠（改为flex布局并列）
- 修复设置页长期任务编辑区结构错位（longtask-edit移入settings-section内）
- 自动刷新指示器移至右下角（避免与通知冲突）
- 移动端sidebar品牌文字缩小防截断
- 性能页面硬编码变化值改为动态ID
- Playwright 64/64全通过，零JS错误

## 2026-05-22 轮次331

**WebUI v8.5 图表美化**：
- 圆环图：加大size(160)、圆角stroke-linecap、drop-shadow、百分比图例、gapAngle分隔
- 进度条：卡片化(surface2背景+border-radius:10px)、渐变bar+box-shadow、百分比高亮
- 用量面板：grid卡片统计(居中大字)、额度左border色条卡片、模型明细flex-wrap
- 容器：border-radius:16px、box-shadow、标题前加色条装饰
- Playwright 14/14全通过，零JS错误
