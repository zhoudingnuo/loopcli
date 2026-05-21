---
name: self-improving-agent
description: 自动记忆优化系统。分析MEMORY.md模式，提升学习为规则，提取重复解决方案为技能。用于：(1)审查项目学习 (2)提升模式为规则 (3)调试方案转技能 (4)检查内存健康
---

# Self-Improving Agent - 记忆优化系统

## 核心价值

Claude Code 的 auto-memory 自动记录项目模式，但缺乏判断力：
- 哪些学习是临时 vs 永久
- 哪些模式应成为强制规则
- 200行限制是否被陈旧条目浪费
- 哪些解决方案值得成为可复用技能

本技能添加智能层：分析学习 → 提升为规则 → 提取为技能

## 快速参考

| 命令 | 功能 |
|------|------|
| `/si:review` | 分析 MEMORY.md - 找提升候选、陈旧条目、合并机会 |
| `/si:promote` | 将模式从 MEMORY.md → CLAUDE.md 或 .claude/rules/ |
| `/si:extract` | 将验证过的模式转为独立技能 |
| `/si:status` | 内存健康看板 - 行数、主题文件、建议 |
| `/si:remember` | 显式保存重要知识到 auto-memory |

## 记忆架构

### 文件位置

| 文件 | 谁写 | 范围 | 加载 |
|------|------|------|------|
| `./CLAUDE.md` | 你 (+ /si:promote) | 项目规则 | 完整文件，每会话 |
| `~/.claude/CLAUDE.md` | 你 | 全局偏好 | 完整文件，每会话 |
| `~/.claude/projects/<id>/memory/MEMORY.md` | Claude (auto) | 项目学习 | 前200行 |
| `~/.claude/projects/<id>/memory/*.md` | Claude (overflow) | 主题笔记 | 按需 |
| `.claude/rules/*.md` | 你 (+ /si:promote) | 作用域规则 | 匹配文件时 |

### 提升生命周期

```
1. Claude 发现模式 → auto-memory (MEMORY.md)
2. 模式重复 2-3x → /si:review 标记为提升候选
3. 你批准 → /si:promote 提升到 CLAUDE.md 或 rules/
4. 模式成为强制规则，不仅是笔记
5. 删除 MEMORY.md 条目 → 释放新学习空间
```

## 核心概念

### Auto-memory 是捕获，非管理

Auto-memory 擅长记录，但缺乏判断：
- 临时 vs 永久学习
- 哪些模式应成为强制规则
- 200行限制是否浪费在陈旧条目
- 哪些解决方案值得成为技能

### 提升 = 毕业

提升学习时，它从 Claude 草稿纸 (MEMORY.md) 移到项目规则系统 (CLAUDE.md 或 .claude/rules/)：

- **MEMORY.md**: "我注意到这个项目用 pnpm"（背景上下文）
- **CLAUDE.md**: "使用 pnpm，不是 npm"（强制指令）

提升规则优先级更高，完整加载（不在200行截断）。

### 规则目录用于作用域知识

不是所有都属于 CLAUDE.md。用 `.claude/rules/` 存储仅适用于特定文件类型的模式：

```yaml
# .claude/rules/api-testing.md
---
paths:
- "src/api/**/*.test.ts"
- "tests/api/**/*"
---
- 用 supertest 测试 API 端点
- 用 msw 模拟外部服务
- 始终测试错误响应，不仅是快乐路径
```

仅在 Claude 处理 API 测试文件时加载 - 否则零开销。

## Agents

### memory-analyst

分析 MEMORY.md 和主题文件识别：
- 跨会话重复的条目（提升候选）
- 引用已删除文件或旧模式的陈旧条目
- 应合并的相关条目
- MEMORY.md 知道与 CLAUDE.md 强制之间的差距

### skill-extractor

取验证过的模式生成完整技能：
- 带正确 frontmatter 的 SKILL.md
- 参考文档
- 示例和边缘情况
- 准备好 `/plugin install` 或发布

## Hooks

### error-capture (PostToolUse → Bash)

监控命令输出的错误。检测到时，追加结构化条目到 auto-memory：
- 失败的命令
- 错误输出（截断）
- 时间戳和上下文
- 建议类别

**Token 开销**: 成功时零。仅检测到错误时 ~30 tokens。

## 使用场景

### 场景 1: 定期内存审查

每 10 轮或当 MEMORY.md 接近 200 行时：

```
/si:review
```

输出：
- 提升候选（重复 2-3x 的模式）
- 陈旧条目（引用不存在的文件）
- 合并机会（相似主题）
- 建议（提升 vs 删除 vs 保留）

### 场景 2: 提升模式为规则

当 /si:review 识别出候选：

```
/si:promote --entry "pnpm-preference" --target "CLAUDE.md"
```

效果：
- 从 MEMORY.md 读取条目
- 重写为强制规则
- 追加到 CLAUDE.md
- 从 MEMORY.md 删除原条目

### 场景 3: 提取技能

当调试方案重复使用：

```
/si:extract --pattern "docker-compose-debugging"
```

输出：
- 新 skill/ 目录
- SKILL.md 带 frontmatter
- 参考资料（日志、解决方案）
- 使用示例

### 场景 4: 内存健康检查

```
/si:status
```

输出：
- MEMORY.md 行数 / 200
- 主题文件数量
- 最近更新时间
- 陈旧条目警告
- 优化建议

## 成本控制

### Token 优化

| 操作 | Token 成本 | 频率 |
|------|-----------|------|
| /si:review | ~500 tokens | 每 10 轮 |
| /si:promote | ~200 tokens | 按需 |
| /si:extract | ~800 tokens | 按需 |
| /si:status | ~150 tokens | 每 5 轮 |

### 自动化策略

```python
# thoughts.md 压缩触发
if thoughts_lines > 50:
    /si:review  # 识别可归档条目
    /si:promote  # 提升关键模式
    # 压缩到最近 5 轮 + 关键决策
```

## 最佳实践

### 提升标准

提升到 CLAUDE.md：
- 跨 3+ 会话重复
- 影响代码正确性
- 用户明确偏好

提升到 .claude/rules/：
- 特定文件类型
- 特定目录
- 条件性规则

保留在 MEMORY.md：
- 单次观察
- 临时背景
- 待验证模式

删除：
- 引用已删除文件
- 过时技术
- 一次性调试会话

## 相关技能

- **cost-optimizer**: Token 使用优化
- **token-control**: Agent 禁用/启用管理
- **create-agent**: 新 Agent 创建
