---
name: memory-system-design
type: reference
created: 2026-05-23
---

# 记忆系统设计（三层架构）

参考：Cog 三层记忆 + Claude Code 指针索引模式

## Hot（热记忆）— 每轮必读
- `MEMORY.md` — 指针索引，≤50 行
- `state.json` — 当前状态
- 读取成本：~300 tokens

## Warm（温记忆）— 按需 Grep 搜索
- `memory/facts/*.md` — 独立事实/经验/决策文件
- 每个文件用 `[[wiki-link]]` 链接相关记忆
- 搜索方式：Grep `memory/facts/` 关键词
- 单文件 ≤100 行

## Cold（冷记忆）— 归档
- `memory/archive/` — 压缩的旧记忆
- 仅在需要历史回顾时搜索

## 链式回忆流程
1. 读 MEMORY.md 索引 → 定位相关文件
2. 读目标 fact 文件 → 发现 [[链接]]
3. 跟踪链接到关联文件 → 形成记忆链

## 新记忆写入规则
- 新事实/经验 → 创建 `facts/<topic>.md`，添加 [[链接]]
- 更新 `MEMORY.md` 索引添加指针
- thoughts.md 仅用于当轮工作记忆，不存长期知识

## 压缩规则
- MEMORY.md 超 50 行时，合并/归档最旧的条目
- fact 文件超 100 行时，提炼核心到新文件，旧文件移入 archive/

**Related:** [[cost-control]]
