# LoopCLI 配置文档

## 环境变量

### 服务器配置

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LOOPCLI_HOST` | `127.0.0.1` | WebUI 服务器绑定地址。设为 `0.0.0.0` 可允许局域网访问（不推荐，有安全风险） |
| `LOOPCLI_API_KEY` | （空） | API 密钥。设置后所有 POST 请求必须携带 `X-API-Key` 头。留空则不鉴权 |
| `CORS_ORIGINS` | `http://localhost:3000` | 允许的 CORS 来源，多个用逗号分隔。留空则允许所有来源 |

### WebUI 服务器内部参数

以下参数在 `server.py` 中硬编码，如需修改请编辑源文件：

| 参数 | 默认值 | 位置 | 说明 |
|------|--------|------|------|
| `MAX_BODY_SIZE` | `10240` (10KB) | `server.py:44` | 请求体最大字节数 |
| `SSE_MAX_CONNECTIONS` | `10` | `server.py:56` | SSE 最大并发连接数 |
| `SSE_TIMEOUT_SECONDS` | `300` | `server.py:57` | SSE 连接超时时间（秒） |
| 写入并发信号量 | `10` | `server.py:51` | 同时处理的写入请求数 |

### 主循环配置

以下参数在 `run.py` 中硬编码：

| 参数 | 默认值 | 位置 | 说明 |
|------|--------|------|------|
| `LOOPCLI_ROOT` | `D:\loopcli` | `loopcli_lib.py:10` | 项目根目录 |
| `CLAUDE` | `%APPDATA%\npm\claude.cmd` | `run.py:30` | Claude CLI 路径 |
| 日志轮转大小 | `1,000,000` (1MB) | `run.py:83` | 单个日志文件最大大小 |
| 日志轮转归档数 | `3` | `run.py:83` | 最多保留的归档文件数 |

## CLI 参数

### `run` 命令

```bash
python run.py run [选项]
```

| 参数 | 简写 | 默认值 | 说明 |
|------|------|--------|------|
| `--iterations` | `-n` | `0` (无限) | 迭代次数 |
| `--wait` | `-w` | `10` | 每轮间隔秒数 |

### 其他命令

```bash
python run.py create <模板ID> [--task "任务描述"]
python run.py task <Agent名> "任务标题" [--desc "描述"]
python run.py list
python run.py templates [--filter "关键词"]
python run.py msg "消息内容" [--agent <Agent名>]
python run.py enable <Agent名>
python run.py disable <Agent名>
```

## Agent 配置

### Agent 目录结构

每个 Agent 必须包含以下文件：

```
<agent-name>/
├── AGENT                  # 标记文件（内容为 "type: main"）
├── SOUL.md                # 身份与行为准则
├── PROMPT.md              # 每轮执行指令
├── memory/
│   ├── state.json         # 运行状态
│   ├── tasks.json         # 任务队列
│   └── results/           # 任务结果
├── inbox/                 # 收件箱
└── log/
    └── run.md             # 运行日志
```

### state.json 格式

```json
{
  "agent": "agent-name",
  "status": "idle",
  "current_task": null,
  "last_run": "2026-05-21 10:00:00",
  "run_count": 42,
  "created": "2026-05-21"
}
```

### tasks.json 格式

```json
[
  {
    "id": 1,
    "status": "pending",
    "title": "任务标题",
    "description": "详细描述",
    "created": "2026-05-21",
    "assignee": "agent-name",
    "completed": "2026-05-21 10:00:00"
  }
]
```

### 启用/禁用 Agent

禁用 Agent 会在 `AGENT` 标记文件中添加 `disabled: true`：

```
# 启用状态
type: main

# 禁用状态
type: main
disabled: true
```

`run.py run` 会自动跳过禁用的 Agent。

## WebUI 自定义

### 端口修改

编辑 `server.py` 底部的 `main()` 函数：

```python
port = 8080  # 修改为你需要的端口
```

### 主题与样式

WebUI 前端样式全部内联在 `index.html` 的 `<style>` 标签中。CSS 变量定义在 `:root` 选择器：

```css
:root {
  --bg: #0f1117;        /* 背景色 */
  --surface: #1a1d27;   /* 表面色 */
  --accent: #6c5ce7;    /* 主色调 */
  --green: #00b894;     /* 运行中状态色 */
  /* ... */
}
```

### 轮询间隔

- Agent/任务数据刷新：`index.html` 中 `setInterval(loadData, 10000)` — 默认 10 秒
- Loop 进程状态刷新：`setInterval(loadLoopStatus, 3000)` — 默认 3 秒
- SSE 日志流推送间隔：`server.py` 中 `time.sleep(1)` — 默认 1 秒

## 安全配置

### 启用 API 鉴权

```bat
set LOOPCLI_API_KEY=your-secret-key-here
python D:\loopcli\main\webui\server.py
```

之后所有 POST 请求需携带 Header：

```
X-API-Key: your-secret-key-here
```

GET 请求无需鉴权。

### 配置 CORS

```bat
set CORS_ORIGINS=http://localhost:3000,https://your-domain.com
python D:\loopcli\main\webui\server.py
```

### 网络绑定

默认仅本地访问（`127.0.0.1`）。如需局域网访问：

```bat
set LOOPCLI_HOST=0.0.0.0
```

**警告**：局域网暴露时务必设置 `LOOPCLI_API_KEY`。

## Watchdog 配置

`watchdog.py` 在 `server.py` 崩溃时自动重启，相关参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `RESTART_DELAY` | `5` 秒 | 重启间隔 |

### 设置为 Windows 服务（可选）

使用 Windows 任务计划程序设置开机自动启动：

```powershell
# 创建开机启动任务
schtasks /create /tn "LoopCLI-WebUI" /tr "wscript D:\loopcli\main\webui\startup-hidden.vbs" /sc onstart /ru SYSTEM
```

## Git 同步

`run.py` 支持自动 Git push（需配置）：

1. 创建 `D:\loopcli\.gittoken` 文件，写入 GitHub Personal Access Token
2. 每轮结束后自动 commit 并 push `memory/`、`log/`、`inbox/` 目录
