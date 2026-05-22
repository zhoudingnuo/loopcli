---
name: system-modification-rules
type: rule
created: 2026-05-22
---

# 系统本体修改规则

修改以下文件前**必须先运行测试**：
- `run.py` — 主入口
- `.claude.json` — MCP 配置
- `webui/loopcli_lib.py` — agent 框架核心

测试命令：`python tests/test_core_changes.py`

**Why:** 2026-05-22 事故：MCP 服务器故障阻塞整个系统。测试能快速发现语法错误、导入失败、子进程卡死。

**Related:** [[cost-control]]
