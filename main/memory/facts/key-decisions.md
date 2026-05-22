---
name: key-decisions
type: reference
tags: [decision, architecture, trade-off, design-choice]
created: 2026-05-23
---

# 关键决策记录

## 单文件 WebUI 架构
- **决策**：WebUI 全部内联在 index.html 中
- **原因**：简化部署，无需构建工具，Claude 可直接编辑
- **代价**：文件较大（3000+ 行），但编辑时用 offset/limit 按需读取

## 三层记忆系统
- **决策**：采用文件记忆而非向量数据库
- **原因**：CLI 环境无数据库服务器，文件记忆零依赖
- **参考**：Cog 项目、Claude Code 自身记忆模式

## 禁止 AskUserQuestion
- **决策**：所有子 Agent 禁止使用 AskUserQuestion
- **原因**：子 Agent 运行在非交互模式（--print），问问题会永久卡死系统
- **教训**：2026-05-22 曾因此导致系统阻塞

**Related:** [[memory-system-design]] [[current-architecture]] [[cost-control]] [[agent-scheduling]]
