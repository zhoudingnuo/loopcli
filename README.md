# LoopCLI — 全天候多 Agent 自治系统

LoopCLI 是一个基于 Claude Code 的循环驱动多 Agent 框架。通过 `while` 循环不断将 PROMPT 喂给 `claude --print`，实现 Agent 的持续自主运行。内置 WebUI 控制台，提供 Agent 管理、任务调度、实时日志和消息通信功能。

## 架构概览

```
                    ┌──────────────────────────────────────────┐
                    │            WebUI 控制台 (:8080)           │
                    │  ┌────────┐ ┌────────┐ ┌──────┐ ┌─────┐ │
                    │  │仪表盘  │ │Agent   │ │任务  │ │日志 │ │
                    │  │        │ │管理    │ │调度  │ │流   │ │
                    │  └────────┘ └────────┘ └──────┘ └─────┘ │
                    └─────────────────┬────────────────────────┘
                                      │ REST API + SSE
                    ┌─────────────────┴────────────────────────┐
                    │           server.py + loopcli_lib.py      │
                    └─────────────────┬────────────────────────┘
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           │                          │                          │
    ┌──────┴──────┐          ┌───────┴──────┐          ┌───────┴──────┐
    │  main Agent │          │  Agent #N    │          │  Agent #M    │
    │  (调度中心)  │          │  (前端开发)   │          │  (代码审查)   │
    │  SOUL.md    │          │  SOUL.md     │          │  SOUL.md     │
    │  PROMPT.md  │          │  PROMPT.md   │          │  PROMPT.md   │
    │  memory/    │          │  memory/     │          │  memory/     │
    └─────────────┘          └──────────────┘          └──────────────┘
```

## 工作原理

```
while True:
    PROMPT.md → claude --print → 执行任务 → 写回状态 → 下一轮
```

每次 `claude` 调用都是独立会话。Agent 通过文件系统（`memory/`）在轮次之间持久化状态，实现"记忆"。

## 目录结构

```
D:\loopcli\
├── run.py                     # CLI 入口 & 主循环
├── start.bat                  # 一键启动脚本
├── README.md                  # 本文件
├── docs/
│   └── CONFIGURATION.md       # 配置文档
├── main/                      # 主 Agent
│   ├── SOUL.md                # Agent 身份与行为准则
│   ├── PROMPT.md              # 每轮执行指令
│   ├── AGENT                  # Agent 标记文件
│   ├── webui/
│   │   ├── server.py          # WebUI 后端服务器
│   │   ├── loopcli_lib.py     # 共享模块（JSON I/O、Agent 发现、任务管理）
│   │   ├── watchdog.py        # 进程看门狗（自动重启）
│   │   ├── index.html         # WebUI 前端单页应用
│   │   ├── startup-hidden.vbs  # 后台启动 WebUI 的 VBS 脚本
│   │   ├── data.json          # WebUI 运行数据
│   │   └── loop_state.json    # Loop 进程状态
│   ├── memory/
│   │   ├── state.json         # 运行状态
│   │   ├── tasks.json         # 任务队列
│   │   ├── errors.json        # 错误记录
│   │   └── results/           # 任务结果
│   ├── inbox/                 # 收件箱（接收其他 Agent 消息）
│   ├── log/
│   │   └── run.md             # 运行日志
│   ├── tests/                 # 单元测试 & 集成测试
│   └── requirements-dev.txt   # 开发依赖
├── skill/                     # 全局技能文件
│   ├── report.md              # 汇报状态
│   ├── inbox.md / outbox.md   # 消息收发
│   ├── create-agent.md        # 创建 Agent
│   ├── assign-task.md         # 派发任务
│   ├── list-agents.md         # 列出 Agent
│   └── token-saving.md        # Token 节省策略
├── subagent/                  # Agent 模板库（按部门分类）
│   ├── engineering/           # 工程类模板
│   ├── design/                # 设计类模板
│   ├── academic/              # 学术类模板
│   └── ...                    # 其他部门
└── <agent-name>/              # 子 Agent 目录（结构与 main 相同）
```

## 快速开始

### 前置条件

- Python 3.10+
- [Claude Code CLI](https://claude.ai/code) 已安装并登录（`claude` 命令可用）
- Windows 10/11

### 1. 一键启动（推荐）

双击 `start.bat` 或在项目根目录运行：

```bat
start.bat
```

该脚本将启动 WebUI 服务器和 watchdog 进程。

### 2. 手动启动

**启动 WebUI：**

```bash
python D:\loopcli\main\webui\server.py
```

**启动主循环（CLI 模式）：**

```bash
python D:\loopcli\run.py run
```

**后台启动 WebUI（Windows）：**

```powershell
wscript D:\loopcli\main\webui\startup-hidden.vbs
```

### 3. 访问 WebUI

启动后浏览器打开 http://127.0.0.1:8080

## CLI 命令参考

```bash
# 启动 Agent 循环
python run.py run                          # 无限循环，每轮间隔 10 秒
python run.py run -n 5                     # 运行 5 轮
python run.py run -w 30                    # 每轮间隔 30 秒

# Agent 管理
python run.py list                         # 列出所有 Agent 及状态
python run.py templates                    # 列出可用模板
python run.py templates -f frontend        # 按关键词筛选模板
python run.py create engineering-frontend-developer --task "开发登录页面"
python run.py enable <agent-name>          # 启用 Agent
python run.py disable <agent-name>         # 禁用 Agent

# 任务管理
python run.py task <agent-name> "任务标题" --desc "任务描述"

# 发送消息
python run.py msg "消息内容" --agent main
```

## 多 Agent 架构

每个 Agent 是一个独立的目录，拥有自己的 SOUL、PROMPT 和 memory：

```
D:\loopcli\
├── main/                                # 主 Agent — 调度决策
├── engineering-frontend-developer/      # 前端开发 Agent
├── engineering-code-reviewer/           # 代码审查 Agent
└── ...                                  # 其他 Agent
```

### Agent 生命周期

1. **创建**：从模板 `subagent/<部门>/<模板>.md` 创建，自动生成 SOUL.md、PROMPT.md、memory 结构
2. **调度**：`run.py run` 自动发现所有启用的 Agent 并行执行
3. **通信**：Agent 之间通过 `inbox/` 目录发送消息
4. **状态**：每轮结束更新 `state.json`，结果写入 `memory/results/`

### 创建新 Agent

```bash
python run.py create engineering-backend-architect --task "设计 REST API"
```

系统会从 `subagent/engineering/engineering-backend-architect.md` 读取模板，在 `D:\loopcli\engineering-backend-architect\` 创建完整目录结构。

## WebUI 功能

### 仪表盘
- Agent 总览、运行状态、待处理任务统计
- Agent 卡片展示（展开查看任务列表）

### Agent 管理
- 查看/筛选所有 Agent
- 启用/禁用 Agent
- 启动单个 Agent 执行

### 任务管理
- 创建任务并指派 Agent
- 按 Agent 筛选任务
- 任务状态追踪

### 实时日志
- SSE 日志流（按 Agent 筛选）
- 日志搜索、暂停/继续、自动滚动

### 控制面板
- Loop 进程控制（启动/停止/重启）
- 一键派发任务并执行
- 进程状态监控（PID、运行时长、迭代次数）

### 消息发送
- 向任意 Agent 发送消息
- 消息历史记录

## API 端点

### GET

| 端点 | 说明 |
|------|------|
| `GET /` | WebUI 前端页面 |
| `GET /api/agents` | 获取所有 Agent 列表及元数据 |
| `GET /api/tasks` | 获取任务列表（`?agent=<id>` 或 `?agent=__all__`） |
| `GET /api/agents/<id>/tasks` | 获取指定 Agent 的任务 |
| `GET /api/logs` | 获取日志（`?n=100&agent=<id>`） |
| `GET /api/logs/stream` | SSE 日志流（`?agent=<id>`） |
| `GET /api/loopcli/status` | 获取 Loop 进程状态 |

### POST（需要 API Key，如果已配置）

| 端点 | 说明 | Body |
|------|------|------|
| `POST /api/tasks` | 创建任务 | `{title, description?, assignee?}` |
| `POST /api/agents/start` | 启动 Agent | `{agent}` |
| `POST /api/agents/enable` | 启用 Agent | `{agent}` |
| `POST /api/agents/disable` | 禁用 Agent | `{agent}` |
| `POST /api/loopcli/start` | 启动 Loop | `{iterations?}` |
| `POST /api/loopcli/stop` | 停止 Loop | — |
| `POST /api/loopcli/restart` | 重启 Loop | `{iterations?}` |
| `POST /api/loopcli/dispatch` | 派发任务并执行 | `{agent, title, description?}` |
| `POST /api/messages/send` | 发送消息 | `{agent?, content}` |

## 安全特性

- **API 鉴权**：通过 `LOOPCLI_API_KEY` 环境变量启用，所有 POST 请求需携带 `X-API-Key` 头
- **路径遍历防护**：所有 Agent ID 输入经过严格校验，防止目录遍历攻击
- **请求体限制**：10KB 请求体大小限制，防止超大负载攻击
- **CORS 白名单**：通过 `CORS_ORIGINS` 配置允许的跨域来源
- **并发控制**：写入操作信号量限制（10 并发），SSE 连接数上限（10 连接）
- **UUID 文件名**：inbox 消息文件使用 UUID 防止文件名冲突和猜测
- **绑定地址**：默认绑定 `127.0.0.1`，仅本地访问

## 测试

```bash
# 运行所有测试
cd D:\loopcli\main
python -m pytest tests/ -v

# 仅运行单元测试
python -m pytest tests/test_server.py tests/test_run.py -v

# 运行集成测试
python -m pytest tests/test_integration.py -v
```

## 停止服务

- WebUI：`Ctrl+C` 终止前台进程
- 主循环：`Ctrl+C` 或在 WebUI 控制面板点击"停止"
- 后台进程：通过 WebUI 控制面板停止，或使用 `python run.py list` 查找进程后手动终止特定 PID

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python 3 标准库（http.server, threading, json） |
| 前端 | 原生 HTML/CSS/JS（零依赖） |
| AI 引擎 | Claude Code CLI (`claude --print`) |
| 通信 | REST API + Server-Sent Events |
| 持久化 | 文件系统（JSON + Markdown） |
| 测试 | pytest |

## 许可

MIT License
