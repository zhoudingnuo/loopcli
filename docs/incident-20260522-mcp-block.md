# 事故报告：lean-ctx MCP 服务器导致主进程阻塞

**日期**：2026-05-22
**严重程度**：高（系统完全不可用）
**状态**：已解决（卸载 lean-ctx）

---

## 现象

`python run.py run` 运行时，main agent 在处理 inbox 消息时频繁卡死，整轮不结束也不输出，需要手动终止进程。同时出现微信 bridge 的 DNS 错误信息混入终端输入区域。

## 根因

### 1. MCP 并发请求丢响应（核心问题）

lean-ctx.exe 是一个 PyInstaller 打包的 Python MCP 服务器（65MB）。当 Claude CLI 子进程（agent）发出 **超过 2 个并发的 ctx_read 请求** 时，部分请求永远不会返回响应，导致 agent 无限等待。

**复现场景**：main agent 同时读取 4 条 inbox 消息（4 个并发 ctx_read），只有部分返回，进程卡死。

**证据**：`D:\loopcli\logs\run_20260522_040738\main.log` 第 24-27 行发出 4 个 ctx_read 调用，日志到此为止，无任何 response。

### 2. GBK 编码崩溃（加剧因素）

lean-ctx.exe 内部使用 Python 的 `subprocess.Popen(text=True)` 处理子进程。在中文 Windows（系统编码 GBK/CP936）上，`text=True` 默认用 GBK 解码。当子进程输出包含非 GBK 字符（如 UTF-8 中文）时，后台读取线程崩溃：

```
UnicodeDecodeError: 'gbk' codec can't decode byte 0xaf in position 1011: illegal multibyte sequence
```

读取线程崩溃后，主线程可能因等待该线程而死锁，进一步加剧 MCP 无响应问题。

**相同问题也存在于**：
- `bash_compress.py`（token optimizer hook）第 1087 行：`subprocess.run(..., text=True)` 未指定 `encoding='utf-8'`

### 3. 微信 bridge 日志污染终端

wechat_bridge.py 的日志使用 `print()` 输出到 stdout。run.py 的交互式终端界面通过光标定位控制输入/输出区域，stdout/stderr 输出会绕过定位逻辑，直接显示在光标当前位置（输入框区域）。

## 时间线

| 时间 | 事件 |
|------|------|
| 05-21 19:10 | lean-ctx 首次启用，运行正常 |
| 05-22 03:28 | main agent 因 ctx_tree 扫描 276 个子模板导致输出过大，触发卡顿 |
| 05-22 03:37 | 添加 AskUserQuestion 禁止、MCP 并发限制到 PROMPT.md |
| 05-22 03:44 | 微信 bridge 上线，开始出现 DNS 错误 |
| 05-22 03:52 | 两个 agent 并发调用 lean-ctx，MCP 事件日志显示交错执行 |
| 05-22 04:07 | main agent 4 个并发 ctx_read 全部无响应，确认 MCP 并发问题 |
| 05-22 ~04:15 | 分析 events.jsonl、context_radar.jsonl，发现 GBK 编码崩溃 |
| 05-22 ~04:20 | 修复 bash_compress.py 加 encoding='utf-8'，lean-ctx 加 PYTHONUTF8=1 |
| 05-22 ~04:30 | 问题未解决，lean-ctx 并发问题为架构限制 |
| 05-22 ~04:35 | 卸载 lean-ctx MCP，清理相关配置和规则文件 |

## 修复措施

| 措施 | 文件 | 说明 |
|------|------|------|
| 卸载 lean-ctx | `.claude.json` | 移除 mcpServers 配置 |
| 清空 lean-ctx 指令 | `.claude/CLAUDE.md` | 移除 ctx_read/ctx_shell 替代规则 |
| 删除 lean-ctx 规则 | `.claude/rules/lean-ctx.md` | 已删除 |
| 修复 GBK 编码 | `.claude/token-optimizer/.../bash_compress.py` | subprocess.run 加 `encoding="utf-8"` |
| 微信日志改写文件 | `wechat_bridge.py` | `_log()` 从 stderr 改为写 `~/.loopcli/wechat.log` |

## 教训

1. **MCP 服务器是单点故障** — agent 完全依赖 MCP 响应，MCP 卡死 = agent 卡死 = 整个系统卡死
2. **中文 Windows 兼容性** — Python `text=True` 默认 GBK，所有涉及 subprocess 的代码必须显式指定 `encoding='utf-8'`
3. **并发上限应在代码层面保证** — 提示词限制（"最多 2 个并发"）不可靠，模型不一定遵守
4. **日志隔离** — 后台线程的日志不应写 stdout/stderr，应写独立日志文件

## 改进建议

- [ ] run.py 中为 agent 子进程添加 MCP 调用超时机制（如 60s 无响应则重启 agent）
- [ ] 考虑用原生工具替代 lean-ctx 的文件读取功能（已通过卸载实现）
- [ ] 所有 Python subprocess 调用统一加 `encoding='utf-8'` 或设置 `PYTHONUTF8=1`
