# LoopCLI — 全天候多 Agent 自治系统

LoopCLI 是一个基于 Claude Code 的循环驱动多 Agent 框架。通过 `while` 循环不断将 PROMPT 喂给 `claude --print`，实现 Agent 的持续自主运行。

## 工作原理

```
while True:
    PROMPT.md → claude --print → 执行任务 → 写回状态 → 下一轮
```

每次 `claude` 调用都是独立会话。Agent 通过文件系统（memory/）在轮次之间持久化状态，实现"记忆"。

## 目录结构

```
D:\loopcli\
├── run.py                # Python 启动脚本（主循环）
├── run.ps1               # PowerShell 启动脚本（备选）
├── main/                 # 主 Agent
│   ├── SOUL.md           # Agent 身份与行为准则
│   ├── PROMPT.md         # 每轮执行指令
│   ├── memory/
│   │   ├── state.json    # 运行状态
│   │   ├── tasks.md      # 任务队列
│   │   └── errors.json   # 错误记录
│   └── log/
│       ├── run.md        # 运行日志
│       └── raw.log       # 原始输出日志
```

## 核心文件说明

| 文件 | 作用 |
|------|------|
| `SOUL.md` | 定义 Agent 的身份、职责和行为边界 |
| `PROMPT.md` | 每轮循环喂给 claude 的指令，引用 SOUL 和 memory |
| `state.json` | JSON 格式的运行状态，每轮读写 |
| `tasks.md` | Markdown 任务队列，Agent 逐条消费 |

## 快速开始

1. 在 `memory/tasks.md` 中添加任务
2. 启动主循环：

```bash
python D:\loopcli\run.py
```

3. 后台常驻运行：

```powershell
Start-Process python -ArgumentList "D:\loopcli\run.py" -WindowStyle Hidden
```

## 执行流程

每轮循环：

1. 读取 `PROMPT.md` 作为输入
2. Agent 读取 `SOUL.md` 确认身份
3. 读取 `state.json` 恢复上下文
4. 从 `tasks.md` 取出下一个任务并执行
5. 结果写入 `memory/results/`
6. 更新 `state.json`，追加 `log/run.md`
7. 队列空则输出 IDLE，结束本轮

## 异常处理

- 正常完成：等待 10 秒后进入下一轮
- 执行异常：等待 60 秒后退避重试
- 错误记录到 `memory/errors.json`
- 所有原始输出追加到 `log/raw.log`

## 扩展：多 Agent

每个 Agent 是一个独立的目录，拥有自己的 SOUL、PROMPT 和 memory：

```
D:\loopcli\
├── main/       # 主 Agent — 调度决策
├── reviewer/   # 审查 Agent — 代码审查
└── worker/     # 工作 Agent — 执行具体任务
```

各 Agent 通过共享文件系统协调，避免资源冲突。

## 停止

`Ctrl+C` 终止前台进程，或：

```powershell
# 找到并终止后台进程
Stop-Process -Name python -Force
```
