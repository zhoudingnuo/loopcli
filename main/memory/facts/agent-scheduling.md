---
name: agent-scheduling
type: experience
tags: [agent, parallel, disable, scheduling, loopcli-create]
created: 2026-05-22
---

# Agent 调度经验

## 并行调度
- 用 Agent tool 并行派出多个 subagent，提高效率
- 独立任务用不同 agent 类型：Explore（搜索）、general-purpose（研究）

## 禁用策略
- 没任务的 Agent 立即禁用，这是铁律
- 方法：在 AGENT 文件添加 `disabled: true`

## 创建 Agent
- 用命令行 `loopcli create <template>`
- 禁止扫描 `D:/loopcli/subagent/` 目录（276个模板，数据量太大）
- 子 Agent PROMPT.md 必须包含"禁止 AskUserQuestion"

**Related:** [[cost-control]] [[current-architecture]] [[key-decisions]] [[wechat-notification]]
