# LoopCLI 记忆

## 2026-05-22 轮次331

**WebUI v8.5 图表美化**：
- 圆环图：加大size(160)、圆角stroke-linecap、drop-shadow、百分比图例、gapAngle分隔
- 进度条：卡片化(surface2背景+border-radius:10px)、渐变bar+box-shadow、百分比高亮
- 用量面板：grid卡片统计(居中大字)、额度左border色条卡片、模型明细flex-wrap
- 容器：border-radius:16px、box-shadow、标题前加色条装饰
- Playwright 14/14全通过，零JS错误

**用户未处理反馈**：微信通知坏了，正在排查

## 2026-05-22 轮次329

**WebUI 关键Bug修复**：
- 图表区域越界修复（widgets移入page-agents内）
- Agent状态标签汉化
- 经验：HTML中div嵌套错误会导致内容在多个页面重复显示
