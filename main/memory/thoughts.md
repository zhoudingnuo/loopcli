# LoopCLI 工作记忆

## 2026-05-23 轮次341

**三层记忆系统实现完成**：
- 创建 Hot/Warm/Cold 三层架构：MEMORY.md 索引 → facts/ 知识文件 → archive/ 归档
- 迁移 thoughts.md 关键知识到 9 个独立 fact 文件，每个带 [[wiki-link]] 链式关联
- PROMPT.md 已适配新记忆系统：初始化读索引、按需 Grep 搜索、链式回忆流程
- 参考项目：Cog（三层文件记忆）、Claude Code 自身指针索引模式

**深色主题修复**：
- 用户报告深色主题主背景白色，根因是 html 和 .main 缺少显式 background: var(--bg)
- 已修复，已推送微信通知
