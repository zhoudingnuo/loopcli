---
name: current-architecture
type: reference
tags: [webui, agent, run.py, prompt, wechat, architecture]
created: 2026-05-23
---

# 当前架构

## WebUI v8.7
- 单文件 `webui/index.html`，内联 CSS + JS
- 三主题：深色（默认）、浅色、赛博朋克
- API 端点：`/api/health`、`/api/agents`、`/api/usage`
- Playwright 自动化测试

## Agent 框架
- 主 Agent：`main/` — 循环调度核心
- 工程类 Agent：`engineering-*` — 代码审查、前端、安全等
- 分析类 Agent：`market-analyst/`、`content-generator/`
- 每个 Agent 有 `PROMPT.md`、`SOUL.md`、`memory/`

## 运行机制
- `run.py` 循环调用 Claude CLI
- `PROMPT.md` 是系统提示词，每轮重新注入
- 微信集成：inbox/ 接收消息，report/ 发送通知
- 长期任务：`D:/loopcli/longtask.md`

**Related:** [[webui-pitfalls]] [[agent-scheduling]] [[key-decisions]] [[open-issues]] [[system-modification-rules]]
