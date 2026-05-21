# 重构报告：提取共享模块 + SSE 优化 + 错误处理改进

**任务 ID**: 11
**执行时间**: 2026-05-21 08:58:36
**Agent**: engineering-frontend-developer

## 概述

基于 code-reviewer 审查反馈（7.5/10），执行了三项优先级重构，所有 125 个现有测试通过。

## 优先级1：提取共享模块 ✅

### 创建 `D:/loopcli/main/webui/loopcli_lib.py`

提取了以下共享函数：

| 函数 | 说明 | 原位置 |
|------|------|--------|
| `read_json()` | JSON 文件读取 | server.py + run.py 内联 |
| `write_json()` | 线程安全 JSON 写入 | server.py |
| `safe_agent_path()` | 路径遍历防护 | server.py `_safe_agent_path` |
| `get_agent_marker()` | 读取 AGENT 标记 | run.py |
| `is_agent_enabled()` | 检查启用状态 | run.py |
| `discover_agents()` | Agent 目录发现 | server.py + run.py |
| `scan_agents()` | 完整 Agent 扫描（含元数据） | server.py |
| `create_task()` | 统一任务创建（自动递增 ID） | server.py + run.py |
| `write_inbox_message()` | 收件箱消息写入 | server.py + run.py |
| `set_agent_enabled()` | Agent 启用/禁用 | server.py + run.py |
| `get_agent_tasks()` | 获取 Agent 任务 | server.py |
| `get_all_agent_tasks()` | 聚合所有 Agent 任务 | server.py |
| `get_recent_lines()` | 读取文件尾部 N 行 | server.py |
| `read_file_tail_incremental()` | 增量读取新增内容 | 新增（SSE 优化） |
| `next_task_id()` | 统一任务 ID 生成 | 从两文件提取 |

### 重构后文件变化

- **server.py**: 674 行 → ~380 行（减少 ~44%），所有共享逻辑通过 `from loopcli_lib import ...` 引入
- **run.py**: 617 行 → ~480 行（减少 ~22%），保留 CLI 特有逻辑（subprocess 管理、事件处理等）
- **loopcli_lib.py**: ~210 行新模块

## 优先级2：SSE 性能优化 ✅

### 变更前
```python
# 每秒读取整个文件，即使只有少量新增内容
last_size = 0
if current_size != last_size:
    lines = get_recent_lines(log_path, 500)  # 读全部
```

### 变更后
```python
# 使用 seek+tell 增量读取，只读新增内容
last_pos = 0
lines, last_pos = read_file_tail_incremental(log_path, last_pos)
```

新增 `read_file_tail_incremental()` 函数：
- 基于 `seek(last_pos)` 只读新增内容
- 自动检测文件轮转（size < last_pos 时从头读）
- 每个 SSE 连接维护独立的 `last_pos`，多客户端互不干扰
- 从每秒读整个文件 → 只读新增字节，性能大幅提升

## 优先级3：错误处理改进 ✅

### `_read_body()` JSON 解析错误
```python
# 变更前：静默返回空字典
except (json.JSONDecodeError, UnicodeDecodeError):
    return {}

# 变更后：返回 400 错误
except (json.JSONDecodeError, UnicodeDecodeError) as e:
    self._send_json({"error": f"Invalid JSON: {e}"}, status=400)
    return None
```

### 任务 ID 生成统一
`next_task_id()` 提取到 `loopcli_lib.py`，server.py 和 run.py 共用同一逻辑。

## 测试验证

```
125 passed in 30.51s
```

- test_server.py: 所有 API 端点测试通过
- test_run.py: Agent 发现、任务管理、文件锁测试通过
- test_integration.py: 端到端集成测试通过（含安全测试）

## 影响范围

- `server.py`: 重构为 loopcli_lib 的消费者
- `run.py`: 重构为 loopcli_lib 的消费者
- `loopcli_lib.py`: 新增共享模块
- `test_server.py`: 更新 import 路径
- `test_integration.py`: 更新 import 路径
- 所有功能行为不变，API 兼容
