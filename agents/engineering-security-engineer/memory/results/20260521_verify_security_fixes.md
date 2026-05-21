# 安全验证报告：frontend-developer #7 修复验证 + Medium 问题检查

**日期**：2026-05-21 | **审计员**：安全工程师 | **目标**：server.py

## 验证对象

frontend-developer 完成的 #7 安全修复：
1. 请求体大小限制（10KB → 413）
2. 统一 POST 认证（无 API Key → 401）
3. 时序安全 API Key 比较

---

## 验证结果总览

| # | 验证项 | 状态 | 严重性 |
|---|--------|------|--------|
| 1 | 请求体大小限制 | ✅ PASS | - |
| 2 | 统一 POST 认证 | ✅ PASS | - |
| 3 | 时序安全比较 | ✅ PASS | - |
| 4 | CORS 白名单 | ⚠️ PARTIAL | Medium |
| 5 | 并发竞态条件 | ⚠️ PRESENT | Medium |
| 6 | 文件名冲突 | ⚠️ PRESENT | Low |

---

## 详细验证

### 1. 请求体大小限制 — ✅ PASS

**验证方法**：静态代码分析 `_read_body()` 方法

**代码位置**：`server.py:28, 259-265`

```python
MAX_BODY_SIZE = 10 * 1024  # 10KB

def _read_body(self):
    length = int(self.headers.get("Content-Length", 0))
    if length == 0:
        return {}
    if length > MAX_BODY_SIZE:
        self._send_json({"error": "Request body too large"}, status=413)
        return None
```

**结论**：
- 所有 POST 端点统一通过 `_read_body()` 读取请求体（共 7 处调用：`_handle_create_task`, `_handle_agent_start`, `_handle_loopcli_start`, `_handle_loopcli_restart`, `_handle_loopcli_dispatch`, `_handle_message_send`, `_handle_agent_enable`）
- 超过 10KB 返回 HTTP 413
- Python `http.server` 不支持 chunked 编码，攻击者无法通过分块传输绕过 Content-Length 检查
- **验证通过** ✓

---

### 2. 统一 POST 认证 — ✅ PASS

**验证方法**：静态代码分析所有 POST 路由

**代码位置**：`server.py:408-413`

```python
def _do_POST_impl(self):
    parsed = urlparse(self.path)
    path = parsed.path

    if not self._require_auth():
        return
```

**结论**：
- `_require_auth()` 是 `_do_POST_impl()` 的第一个操作，所有 POST 端点必须先通过认证
- 认证失败返回 401
- 以下所有 POST 端点均在认证之后：
  - `/api/tasks` → `_handle_create_task()`
  - `/api/agents/start` → `_handle_agent_start()`
  - `/api/loopcli/start` → `_handle_loopcli_start()`
  - `/api/loopcli/stop` → `_handle_loopcli_stop()`
  - `/api/loopcli/restart` → `_handle_loopcli_restart()`
  - `/api/loopcli/dispatch` → `_handle_loopcli_dispatch()`
  - `/api/messages/send` → `_handle_message_send()`
  - `/api/agents/enable` / `/api/agents/disable` → `_handle_agent_enable()`
- 无认证绕过路径
- 开发模式（`API_KEY` 为空时）跳过认证，可接受
- **验证通过** ✓

---

### 3. 时序安全 API Key 比较 — ✅ PASS

**验证方法**：静态代码分析 `_require_auth()` 方法

**代码位置**：`server.py:265-272`

```python
def _require_auth(self):
    if not API_KEY:
        return True
    key = self.headers.get("X-API-Key", "") or parse_qs(urlparse(self.path).query).get("key", [""])[0]
    if not hmac.compare_digest(key, API_KEY):
        self._send_json({"error": "Unauthorized"}, status=401)
        return False
    return True
```

**结论**：
- 使用 `hmac.compare_digest()` 进行常量时间比较，防止时序攻击
- 未发现任何使用 `==` 进行 Key 比较的代码
- **验证通过** ✓

**补充说明（Informational）**：
- API Key 可通过 `?key=` 查询参数传递（line 268），这意味着 Key 可能出现在：
  - 服务器访问日志
  - 浏览器历史记录
  - HTTP Referer 头
- 建议：未来版本考虑移除查询参数传递方式，仅支持 Header 传递

---

## Medium 问题状态检查

### 4. CORS 策略 — ⚠️ PARTIAL（Medium）

**代码位置**：`server.py:30, 274-283`

```python
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()]
```

**当前行为**：
- ✅ `CORS_ORIGINS` 环境变量设置时：白名单模式，严格校验 Origin
- ⚠️ `CORS_ORIGINS` 未设置时（**默认**）：回退到 `Access-Control-Allow-Origin: *`（允许所有来源）

**风险评估**：
- LoopCLI 作为本地开发工具，默认 `*` 在开发阶段可接受
- 但如果部署到网络可达环境，`*` 允许任意恶意网站向 WebUI 发起跨域请求
- **未设置 `Access-Control-Allow-Credentials`**，因此跨域请求不会携带 Cookie — 降低了风险

**建议**：
```python
# 改为默认只允许 localhost
CORS_ORIGINS = [o.strip() for o in os.environ.get("CORS_ORIGINS", "http://localhost:8080").split(",") if o.strip()]
```

---

### 5. 并发文件操作竞态条件 — ⚠️ PRESENT（Medium）

**代码位置**：`server.py:49-51, 453-465`

**问题**：Semaphore 限制并发 POST 请求为 10 个，但文件读写操作（tasks.json）不是原子的。

**攻击场景**：
```
请求 A: 读取 tasks.json → [{id:1}, {id:2}]
请求 B: 读取 tasks.json → [{id:1}, {id:2}]  (同一时刻)
请求 A: new_id = 3, 写入 [{id:1}, {id:2}, {id:3, title:"Task A"}]
请求 B: new_id = 3, 写入 [{id:1}, {id:2}, {id:3, title:"Task B"}]  ← 覆盖了请求 A 的结果
```

**影响**：
- 并发创建任务时可能导致任务 ID 冲突或任务丢失
- 影响端点：`/api/tasks`, `/api/loopcli/dispatch`

**建议**：
```python
import fcntl  # Linux
# 或使用 msvcrt（Windows，run.py 已有此模式）

# 在 write_json/read_json 中添加文件锁
def write_json_locked(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "r+", encoding="utf-8") as f:
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        try:
            f.seek(0)
            f.truncate()
            f.write(json.dumps(data, ensure_ascii=False, indent=2))
        finally:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
```

---

### 6. 消息文件名冲突 — ⚠️ PRESENT（Low）

**代码位置**：`server.py:614`

```python
ts = now.strftime("%Y%m%d_%H%M")
msg_file = inbox_dir / f"webui_{ts}.md"
```

**问题**：时间戳精确到分钟，同一分钟内的多条消息会互相覆盖。

**影响**：消息丢失。

**建议**：
```python
import uuid
ts = now.strftime("%Y%m%d_%H%M%S")
msg_file = inbox_dir / f"webui_{ts}_{uuid.uuid4().hex[:6]}.md"
```

---

## 其他观察（Informational）

| # | 发现 | 说明 |
|---|------|------|
| I-1 | API Key 通过 URL 查询参数传递 | Key 可能泄露到日志/历史记录 |
| I-2 | 无 HTTPS | 本地开发工具可接受，部署时需要 TLS |
| I-3 | SSE 连接管理 | 正确实现：锁保护计数器 + 超时 + 最大连接数限制 ✓ |
| I-4 | 路径遍历防护 | `_safe_agent_path()` 在所有路径都正确使用 ✓ |

---

## 结论

frontend-developer 的 #7 安全修复**全部验证通过**：
1. ✅ 请求体大小限制已正确实现
2. ✅ 统一 POST 认证已正确实现
3. ✅ 时序安全比较已正确实现

**Medium 问题状态**：
- CORS：部分修复（白名单可用，但默认仍为 `*`）
- 并发竞态：**未修复**，文件操作缺少原子锁
- 文件名冲突：**未修复**，同一分钟消息会覆盖

**优先级建议**：
1. **并发竞态**（Medium）：添加文件锁，防止任务数据丢失
2. **CORS 默认值**（Medium）：将默认值从 `*` 改为 `localhost`
3. **文件名冲突**（Low）：添加秒级/随机后缀
