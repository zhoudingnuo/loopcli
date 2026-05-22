---
name: cost-control
type: rule
tags: [token, agent-disable, budget, rotation, cost]
created: 2026-05-22
---

# 成本控制铁律

## 禁用空闲 Agent
- 没任务的 Agent 立即在 AGENT 文件中添加 `disabled: true`
- 路径：`D:/loopcli/agents/<agent名>/AGENT`
- 启用时删除 disabled 行

## Token 预算
- thoughts.md ≤ 8000 字，超过就压缩
- state.json ≤ 5 行
- 每轮只做一件有价值的事

## 轮转策略
- raw.log > 1MB 触发轮转
- inbox 处理完归档到 archive/
- thoughts.md 超 50 行压缩为最近 5 轮 + 关键决策

**Why:** 2026-05-22 曾因 agent 空转浪费大量 token。

**Related:** [[system-modification-rules]]
