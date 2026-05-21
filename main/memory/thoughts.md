# 思考日志

## 2026-05-22 05:34 - Agent 禁用

**操作**：禁用 content-generator（空闲）
**原因**：无任务，节省成本
**状态**：financial-monitor 运行中（金融监控）

## 2026-05-22 05:35 - Bug 修复

**用户反馈**：
1. run.py 花费不显示
2. webui Main Agent 状态一直显示"检测中"

**修复**：
- run.py: API 失败时显示提示信息，而非静默
- webui/server.py: 优化状态检测逻辑，信任 state.json + 5分钟阈值

**验证**：测试通过
