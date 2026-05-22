"""
LoopCLI WebUI Backend Server
REST API + static file hosting for the Agent control console.
"""

import hmac
import json
import os
import signal
import subprocess
import sys
import time
import threading
import uuid
import urllib.request
import urllib.parse
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path
from urllib.parse import urlparse, parse_qs

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from loopcli_lib import (
    LOOPCLI_ROOT,
    AGENT_MARKER,
    read_json,
    write_json,
    safe_agent_path,
    scan_agents,
    create_task,
    get_agent_tasks,
    get_all_agent_tasks,
    write_inbox_message,
    set_agent_enabled,
    get_recent_lines,
    read_file_tail_incremental,
)

# Import create agent functions from run.py
# Agent 模板目录
SUBAGENT_DIR = str(LOOPCLI_ROOT / "agent template")

DEFAULT_PROMPT = """# 身份与初始化
- 所有回答用中文
- 读取 inbox/ 下用户消息（最高优先级）
- 读取 SOUL.md 作为身份
- 读取 memory/state.json 了解当前状态
- 读取 memory/tasks.json 了解任务
- 技能文件按需读取

# 执行流程

1. **处理用户消息**（有就立即处理）
2. **做一件最有价值的事**（按优先级选择）
3. **更新记录**：thoughts.md、state.json、log/run.md

# 成本控制

- 禁用空闲 Agent
- 压缩 memory
- 清理 inbox
"""

def find_template(template_id):
    """在 subagent 目录下搜索模板文件"""
    for dept in os.listdir(SUBAGENT_DIR):
        dept_dir = os.path.join(SUBAGENT_DIR, dept)
        if not os.path.isdir(dept_dir):
            continue
        candidate = os.path.join(dept_dir, f"{template_id}.md")
        if os.path.isfile(candidate):
            return candidate
    return None

def list_templates():
    """列出所有可用的 Agent 模板"""
    templates = []
    for dept in sorted(os.listdir(SUBAGENT_DIR)):
        dept_dir = os.path.join(SUBAGENT_DIR, dept)
        if not os.path.isdir(dept_dir):
            continue
        for fname in sorted(os.listdir(dept_dir)):
            if fname.endswith(".md"):
                template_id = fname[:-3]
                template_path = os.path.join(dept_dir, fname)
                # 读取第一行作为描述
                desc = ""
                try:
                    with open(template_path, "r", encoding="utf-8") as f:
                        first_line = f.readline()
                        if first_line.startswith("#"):
                            desc = first_line.strip().lstrip("#").strip()
                except:
                    pass
                templates.append({
                    "id": template_id,
                    "category": dept,
                    "description": desc or template_id
                })
    return templates

WEBUI_DIR = Path(__file__).parent.resolve()
MAIN_DIR = LOOPCLI_ROOT / "main"
SERVER_START_TIME = time.time()
LOOP_STATE_FILE = WEBUI_DIR / "loop_state.json"

_loop_proc = None
_loop_lock = threading.Lock()
API_KEY = os.environ.get("LOOPCLI_API_KEY", "")
MAX_BODY_SIZE = 10 * 1024  # 10KB

_raw_cors = os.environ.get("CORS_ORIGINS", "").strip()
if _raw_cors:
    CORS_ORIGINS = [o.strip() for o in _raw_cors.split(",") if o.strip()]
else:
    CORS_ORIGINS = ["http://localhost:3000"]

_write_semaphore = threading.Semaphore(10)

_sse_connections = 0
_sse_lock = threading.Lock()
SSE_MAX_CONNECTIONS = 10
SSE_TIMEOUT_SECONDS = 300
SSE_HEARTBEAT_INTERVAL = 30


def get_main_tasks():
    return read_json(MAIN_DIR / "memory" / "tasks.json", [])


# --- Agent Activity Detection ---

def get_main_agent_activity():
    """Get main agent's real-time activity status based on log file and state.json."""
    log_path = MAIN_DIR / "log" / "run.md"
    state_path = MAIN_DIR / "memory" / "state.json"
    result = {
        "agent_id": "main",
        "status": "idle",  # idle, running, error
        "last_log_time": None,
        "last_log_entry": None,
        "log_file_exists": False,
        "seconds_since_last_update": None,
        "latest_output": []
    }

    if not log_path.exists():
        return result

    result["log_file_exists"] = True

    try:
        # Get file modification time
        mtime = os.path.getmtime(log_path)
        last_update = datetime.fromtimestamp(mtime)
        result["last_log_time"] = last_update.isoformat()
        result["seconds_since_last_update"] = int((datetime.now() - last_update).total_seconds())

        # Check state.json for more accurate status
        state = read_json(state_path, {})
        state_status = state.get("status", "idle")
        last_action = state.get("last_action", "")

        # Determine status: trust state.json primarily
        if state_status == "running":
            result["status"] = "running"
        elif state_status == "error":
            result["status"] = "error"
        else:  # idle or unknown
            # 如果有最近的活动（日志更新<5分钟或 last_action 很新），判定为活跃
            is_recently_active = (
                result["seconds_since_last_update"] <= 300 or  # 5分钟内有日志更新
                (last_action and "activated" in last_action.lower())  # 或最近激活了任务
            )
            if is_recently_active:
                result["status"] = "running" if result["seconds_since_last_update"] <= 120 else "active"
            else:
                result["status"] = "idle"

        # Get last few log entries
        lines = get_recent_lines(log_path, 20)
        # Filter to get the actual log entries (skip header)
        log_entries = []
        for line in lines:
            if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("|---") and not line.strip().startswith("| 时间"):
                if line.strip().startswith("|"):
                    log_entries.append(line.strip())

        if log_entries:
            # Get the most recent log entry (last one in the list)
            last_entry = log_entries[-1] if log_entries else None
            if last_entry:
                result["last_log_entry"] = last_entry

            # Return last 5 entries as latest output
            result["latest_output"] = log_entries[-5:] if len(log_entries) >= 5 else log_entries

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _get_api_creds():
    """获取 API 凭证：优先环境变量，其次 .env.json"""
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if base_url and token:
        return base_url, token
    env_file = LOOPCLI_ROOT / ".env.json"
    if env_file.exists():
        cfg = read_json(env_file, {})
        return cfg.get("ANTHROPIC_BASE_URL", ""), cfg.get("ANTHROPIC_AUTH_TOKEN", "")
    return "", ""


def _query_api(path, params_str=""):
    """通用 API 查询辅助"""
    base_url, token = _get_api_creds()
    if not base_url or not token:
        return None, "Missing credentials"
    parsed = urlparse(base_url)
    domain = f"{parsed.scheme}://{parsed.netloc}"
    url = domain + path + params_str
    req = urllib.request.Request(url, headers={"Authorization": token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode()).get("data", {}), None


def query_usage_summary():
    """查询 token 使用摘要（24h模型用量 + 配额）"""
    try:
        now = datetime.now()
        start = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:00:00")
        end = now.strftime("%Y-%m-%d %H:%M:%S")
        params = f"?startTime={urllib.parse.quote(start)}&endTime={urllib.parse.quote(end)}"

        # 模型用量
        model_data, err = _query_api("/api/monitor/usage/model-usage", params)
        if err:
            return {"error": err}
        summary = model_data.get("totalUsage", {})
        total_tokens = summary.get("totalTokensUsage", 0)
        call_count = summary.get("totalModelCallCount", 0)
        models = [
            {"name": m.get("modelName", "?"), "tokens": m.get("totalTokens", 0)}
            for m in summary.get("modelSummaryList", [])
        ]

        # 工具用量
        tool_data, _ = _query_api("/api/monitor/usage/tool-usage", params)
        tool_summary = tool_data.get("totalUsage", {})
        tools = [
            {"name": t.get("toolCode", "?"), "count": t.get("totalUsageCount", 0)}
            for t in tool_summary.get("toolSummaryList", [])
        ]

        # 配额
        quota_data, _ = _query_api("/api/monitor/usage/quota/limit", "")
        quotas = []
        for item in quota_data.get("limits", []):
            t = item.get("type", "?")
            unit = item.get("unit", 0)
            pct = item.get("percentage", 0)
            cur = item.get("currentValue", 0)
            total = item.get("usage", "?")
            if "TOKEN" in t:
                if unit == 3:
                    quotas.append({"type": "token_5h", "percentage": round(pct, 1), "current": cur, "total": total, "label": "Token 配额 (5h)"})
                elif unit == 6:
                    quotas.append({"type": "token_weekly", "percentage": round(pct, 1), "current": cur, "total": total, "label": "Token 配额 (周)"})
                else:
                    quotas.append({"type": f"token_u{unit}", "percentage": round(pct, 1), "current": cur, "total": total, "label": f"Token 配额 (unit={unit})"})
            elif "TIME" in t:
                quotas.append({"type": "mcp_month", "percentage": round(pct, 1), "current": cur, "total": total, "label": f"MCP 配额 (月)"})

        # 每周用量（7天汇总，单独 try 不影响主数据）
        weekly = {}
        try:
            week_start = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:00:00")
            week_params = f"?startTime={urllib.parse.quote(week_start)}&endTime={urllib.parse.quote(end)}"
            week_data, _ = _query_api("/api/monitor/usage/model-usage", week_params)
            week_summary = week_data.get("totalUsage", {})
            weekly = {"tokens": week_summary.get("totalTokensUsage", 0), "calls": week_summary.get("totalModelCallCount", 0), "days": 7}
        except Exception:
            pass

        return {
            "total_tokens": total_tokens,
            "call_count": call_count,
            "models": models,
            "tools": tools,
            "quotas": quotas,
            "weekly": weekly,
            "time_range": f"{start} ~ {end}"
        }
    except Exception as e:
        return {"error": str(e)}


def get_usage_trend():
    """获取最近7天的token消耗趋势"""
    try:
        run_log_path = LOOPCLI_ROOT / "main" / "log" / "run.md"
        if not run_log_path.exists():
            return {"data": [], "summary": "暂无数据"}

        with open(run_log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # 解析日志数据
        daily_data = {}
        for line in lines:
            if "|" not in line:
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 4:
                continue

            # 解析日期（格式：2026-05-22 17:19）
            date_part = parts[1].split(" ")[0] if " " in parts[1] else parts[1]

            # 累计每天的任务数作为活跃度指标
            if date_part not in daily_data:
                daily_data[date_part] = 0

            # 状态为done的任务计数
            if "done" in parts[2].lower():
                daily_data[date_part] += 1

        # 生成最近7天的数据
        trend_data = []
        today = datetime.now().date()

        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            value = daily_data.get(date_str, 0)

            # 格式化标签
            if i == 0:
                label = "今天"
            elif i == 1:
                label = "昨天"
            else:
                label = date.strftime("%m/%d")

            trend_data.append({
                "label": label,
                "date": date_str,
                "value": value
            })

        total = sum(d["value"] for d in trend_data)
        avg = total / 7 if trend_data else 0

        return {
            "data": trend_data,
            "summary": f"7天累计 {total} 次任务，平均 {avg:.1f} 次/天"
        }
    except Exception as e:
        return {"error": str(e), "data": [], "summary": "数据加载失败"}


# --- Loop Process Management ---

def get_loop_state():
    return read_json(LOOP_STATE_FILE, {
        "status": "stopped", "pid": None,
        "started_at": None, "iterations": 0, "total_iterations": 0,
    })


def set_loop_state(state):
    write_json(LOOP_STATE_FILE, state)


def _is_pid_alive(pid):
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, PermissionError, OSError):
        return False


def _monitor_loopcli(proc):
    proc.wait()
    with _loop_lock:
        state = get_loop_state()
        if state.get("pid") == proc.pid:
            state["status"] = "stopped"
            state["pid"] = None
            state["ended_at"] = datetime.now().isoformat()
            set_loop_state(state)


def start_loopcli_process(iterations=0):
    global _loop_proc
    with _loop_lock:
        state = get_loop_state()
        if state.get("status") == "running" and _is_pid_alive(state.get("pid")):
            return {"error": "Already running"}, 409

        cmd = [sys.executable, str(LOOPCLI_ROOT / "run.py"), "run"]
        if iterations > 0:
            cmd.extend(["-n", str(iterations)])

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        _loop_proc = proc

        state = {
            "status": "running",
            "pid": proc.pid,
            "started_at": datetime.now().isoformat(),
            "iterations": iterations,
            "total_iterations": 0,
        }
        set_loop_state(state)

        t = threading.Thread(target=_monitor_loopcli, args=(proc,), daemon=True)
        t.start()
        return state, 200


def stop_loopcli_process():
    global _loop_proc
    with _loop_lock:
        state = get_loop_state()
        pid = state.get("pid")
        if not pid or not _is_pid_alive(pid):
            state["status"] = "stopped"
            state["pid"] = None
            set_loop_state(state)
            return {"error": "Not running"}, 409

        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        if _loop_proc and _loop_proc.pid == pid:
            try:
                _loop_proc.terminate()
            except OSError:
                pass
            _loop_proc = None

        state["status"] = "stopped"
        state["pid"] = None
        state["ended_at"] = datetime.now().isoformat()
        set_loop_state(state)
        return {"status": "stopped"}, 200


class WebUIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEBUI_DIR), **kwargs)

    def log_message(self, format, *args):
        ts = datetime.now().strftime("%H:%M:%S")
        sys.stdout.write(f"[{ts}] {format % args}\n")
        sys.stdout.flush()

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        if length > MAX_BODY_SIZE:
            self._send_json({"error": "Request body too large"}, status=413)
            return None
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            self._send_json({"error": f"Invalid JSON: {e}"}, status=400)
            return None

    def _require_auth(self):
        if not API_KEY:
            return True
        key = self.headers.get("X-API-Key", "") or parse_qs(urlparse(self.path).query).get("key", [""])[0]
        if not hmac.compare_digest(key, API_KEY):
            self._send_json({"error": "Unauthorized"}, status=401)
            return False
        return True

    def _cors_headers(self):
        origin = self.headers.get("Origin", "")
        if CORS_ORIGINS:
            if origin in CORS_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
        else:
            self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    # ---------- SSE helpers ----------

    def _send_sse_event(self, data):
        payload = f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
        self.wfile.write(payload.encode("utf-8"))
        self.wfile.flush()

    def _handle_sse_logs(self):
        global _sse_connections
        with _sse_lock:
            if _sse_connections >= SSE_MAX_CONNECTIONS:
                return self._send_json({"error": "Max SSE connections reached"}, status=503)
            _sse_connections += 1

        params = parse_qs(urlparse(self.path).query)
        agent_id = params.get("agent", [None])[0]
        if agent_id:
            agent_dir = safe_agent_path(agent_id)
            if not agent_dir:
                with _sse_lock:
                    _sse_connections -= 1
                return self._send_json({"error": "Invalid agent"}, status=400)
            log_path = agent_dir / "log" / "run.md"
        else:
            log_path = MAIN_DIR / "log" / "run.md"

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self._cors_headers()
        self.end_headers()

        last_pos = 0
        start_time = time.time()
        last_heartbeat = time.time()
        try:
            while True:
                now = time.time()
                if now - start_time > SSE_TIMEOUT_SECONDS:
                    self._send_sse_event({"event": "timeout", "ts": datetime.now().isoformat()})
                    break
                if now - last_heartbeat >= SSE_HEARTBEAT_INTERVAL:
                    self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
                    last_heartbeat = now
                if log_path.exists():
                    lines, last_pos = read_file_tail_incremental(log_path, last_pos)
                    if lines:
                        self._send_sse_event({
                            "agent": agent_id,
                            "lines": lines,
                            "ts": datetime.now().isoformat(),
                        })
                else:
                    if last_pos != -1:
                        self._send_sse_event({"agent": agent_id, "lines": [], "ts": datetime.now().isoformat()})
                        last_pos = -1
                time.sleep(1)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _sse_lock:
                _sse_connections -= 1

    # ---------- GET routes ----------

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/agents":
            return self._send_json(scan_agents())

        if path == "/api/tasks":
            params = parse_qs(parsed.query)
            agent_id = params.get("agent", [None])[0]
            if agent_id == "__all__":
                return self._send_json(get_all_agent_tasks())
            if agent_id:
                tasks = get_agent_tasks(agent_id)
                if tasks is None:
                    return self._send_json({"error": "Invalid agent"}, status=400)
                return self._send_json(tasks)
            return self._send_json(get_main_tasks())

        if path.startswith("/api/agents/") and path.endswith("/tasks"):
            agent_id = path[len("/api/agents/"):-len("/tasks")]
            tasks = get_agent_tasks(agent_id)
            if tasks is None:
                return self._send_json({"error": "Invalid agent"}, status=400)
            return self._send_json(tasks)

        if path == "/api/logs":
            params = parse_qs(parsed.query)
            n = int(params.get("n", ["100"])[0])
            agent_id = params.get("agent", [None])[0]
            if agent_id:
                agent_dir = safe_agent_path(agent_id)
                if not agent_dir:
                    return self._send_json({"error": "Invalid agent"}, status=400)
                log_path = agent_dir / "log" / "run.md"
            else:
                log_path = MAIN_DIR / "log" / "run.md"
            lines = get_recent_lines(log_path, n)
            return self._send_json({"agent": agent_id, "lines": lines})

        if path == "/api/logs/stream":
            return self._handle_sse_logs()

        if path == "/api/agent/activity":
            return self._send_json(get_main_agent_activity())

        if path == "/api/usage/trend":
            return self._send_json(get_usage_trend())

        if path == "/api/usage":
            return self._send_json(query_usage_summary())

        if path == "/api/templates":
            return self._send_json(list_templates())

        if path == "/api/loopcli/status":
            return self._handle_loopcli_status()

        if path == "/api/longtask":
            return self._handle_longtask_get()

        if path == "/api/messages":
            return self._handle_messages_get()

        if path == "/api/stats":
            return self._handle_stats_get()

        if path == "/api/screenshots":
            return self._handle_screenshots_get()

        if path == "/api/health":
            return self._handle_health_get()

        # Static files
        super().do_GET()

    # ---------- POST routes ----------

    def do_POST(self):
        if not _write_semaphore.acquire(timeout=5):
            return self._send_json({"error": "Server busy, try again"}, status=503)
        try:
            self._do_POST_impl()
        finally:
            _write_semaphore.release()

    def _do_POST_impl(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if not self._require_auth():
            return

        if path == "/api/tasks":
            return self._handle_create_task()
        if path == "/api/agents/create":
            return self._handle_agent_create()
        if path == "/api/agents/start":
            return self._handle_agent_start()
        if path == "/api/loopcli/start":
            return self._handle_loopcli_start()
        if path == "/api/loopcli/stop":
            return self._handle_loopcli_stop()
        if path == "/api/loopcli/restart":
            return self._handle_loopcli_restart()
        if path == "/api/loopcli/dispatch":
            return self._handle_loopcli_dispatch()
        if path == "/api/messages/send":
            return self._handle_message_send()
        if path == "/api/agents/enable":
            return self._handle_agent_enable("enable")
        if path == "/api/agents/disable":
            return self._handle_agent_enable("disable")
        if path == "/api/automation/cleanup-logs":
            return self._handle_automation_cleanup_logs()
        if path == "/api/automation/compress-memory":
            return self._handle_automation_compress_memory()
        if path == "/api/automation/disable-idle-agents":
            return self._handle_automation_disable_idle_agents()
        if path == "/api/automation/health-check":
            return self._handle_automation_health_check()
        if path == "/api/automation/git-sync":
            return self._handle_automation_git_sync()
        if path == "/api/longtask/clear":
            return self._handle_longtask_clear()
        if path == "/api/longtask/update":
            return self._handle_longtask_update()

        self._send_json({"error": "Not found"}, status=404)

    # ---------- OPTIONS (CORS preflight) ----------

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.end_headers()

    # ---------- Handlers ----------

    def _handle_create_task(self):
        body = self._read_body()
        if body is None:
            return
        title = body.get("title", "").strip()
        if not title:
            return self._send_json({"error": "title is required"}, status=400)

        assignee = body.get("assignee") or "main"
        task = create_task(
            MAIN_DIR, title,
            description=body.get("description", ""),
            assignee=assignee,
        )
        self._send_json(task, status=201)

    def _handle_agent_start(self):
        body = self._read_body()
        if body is None:
            return
        agent_id = body.get("agent", "").strip()
        if not agent_id:
            return self._send_json({"error": "agent is required"}, status=400)

        agent_dir = safe_agent_path(agent_id)
        if not agent_dir:
            return self._send_json({"error": "Invalid agent"}, status=400)

        prompt_file = agent_dir / "PROMPT.md"
        if not prompt_file.exists():
            return self._send_json({"error": f"Agent '{agent_id}' not found or no PROMPT.md"}, status=404)

        prompt = prompt_file.read_text(encoding="utf-8")
        proc = subprocess.Popen(
            ["claude", "--print"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(agent_dir),
        )
        proc.stdin.write(prompt.encode("utf-8"))
        proc.stdin.close()

        self._send_json({
            "agent": agent_id,
            "pid": proc.pid,
            "status": "started",
        })

    def _handle_agent_create(self):
        body = self._read_body()
        if body is None:
            return

        template_id = body.get("template", "").strip()
        if not template_id:
            return self._send_json({"error": "template is required"}, status=400)

        task_desc = body.get("task", "").strip()

        # 查找模板
        tpl_file = find_template(template_id)
        if not tpl_file:
            return self._send_json({"error": f"Template not found: {template_id}"}, status=404)

        # 读取模板内容
        try:
            with open(tpl_file, "r", encoding="utf-8") as f:
                soul_content = f.read()
        except Exception as e:
            return self._send_json({"error": f"Failed to read template: {str(e)}"}, status=500)

        # 创建 Agent 目录
        agent_dir = LOOPCLI_ROOT / "agents" / template_id
        if agent_dir.exists():
            # Agent 已存在，如果有任务则添加任务
            if task_desc:
                create_task(
                    agent_dir, task_desc,
                    description=task_desc,
                    assignee=template_id,
                )
            return self._send_json({
                "agent": template_id,
                "status": "existed",
                "message": "Agent already existed, task added if provided"
            }, status=200)

        # 创建目录结构
        try:
            (agent_dir / "memory" / "results").mkdir(parents=True, exist_ok=True)
            (agent_dir / "log").mkdir(parents=True, exist_ok=True)

            # 写入 AGENT 标记
            with open(agent_dir / AGENT_MARKER, "w", encoding="utf-8") as f:
                f.write("type: main\n")

            # 写入 SOUL.md
            with open(agent_dir / "SOUL.md", "w", encoding="utf-8") as f:
                f.write(soul_content)

            # 写入 PROMPT.md
            with open(agent_dir / "PROMPT.md", "w", encoding="utf-8") as f:
                f.write(DEFAULT_PROMPT)

            # 写入 state.json
            state = {
                "agent": template_id,
                "status": "idle",
                "current_task": None,
                "last_run": None,
                "run_count": 0,
                "created": datetime.now().strftime("%Y-%m-%d")
            }
            write_json(agent_dir / "memory" / "state.json", state)

            # 写入 tasks.json
            tasks = []
            if task_desc:
                tasks.append({
                    "id": 1,
                    "status": "pending",
                    "title": task_desc,
                    "description": task_desc,
                    "created": datetime.now().strftime("%Y-%m-%d"),
                    "assignee": template_id
                })
            write_json(agent_dir / "memory" / "tasks.json", tasks)

            # 初始化日志
            with open(agent_dir / "log" / "run.md", "w", encoding="utf-8") as f:
                f.write("# 运行日志\n\n")

            return self._send_json({
                "agent": template_id,
                "status": "created",
                "message": "Agent created successfully"
            }, status=201)

        except Exception as e:
            return self._send_json({"error": f"Failed to create agent: {str(e)}"}, status=500)

    # --- Loop control handlers ---

    def _handle_loopcli_status(self):
        state = get_loop_state()
        pid = state.get("pid")
        if state.get("status") == "running" and pid and not _is_pid_alive(pid):
            state["status"] = "stopped"
            state["pid"] = None
            state["ended_at"] = datetime.now().isoformat()
            set_loop_state(state)

        uptime = 0
        if state.get("started_at"):
            try:
                started = datetime.fromisoformat(state["started_at"])
                uptime = int((datetime.now() - started).total_seconds())
            except (ValueError, TypeError):
                pass
        state["uptime_seconds"] = uptime

        # 从日志文件获取实际迭代次数
        try:
            log_path = MAIN_DIR / "log" / "run.md"
            if log_path.exists():
                lines = get_recent_lines(log_path, 1000)
                # 统计包含 | 的行数（表格行）
                iter_count = sum(1 for line in lines if "|" in line and not line.strip().startswith("#") and not line.strip().startswith("|-"))
                state["total_iterations"] = iter_count
        except Exception:
            pass

        self._send_json(state)

    def _handle_loopcli_start(self):
        body = self._read_body()
        if body is None:
            return
        iterations = int(body.get("iterations", 0))
        data, status = start_loopcli_process(iterations)
        self._send_json(data, status)

    def _handle_loopcli_stop(self):
        data, status = stop_loopcli_process()
        self._send_json(data, status)

    def _handle_loopcli_restart(self):
        body = self._read_body()
        if body is None:
            return
        stop_loopcli_process()
        time.sleep(0.5)
        iterations = int(body.get("iterations", 0))
        data, status = start_loopcli_process(iterations)
        self._send_json(data, status)

    def _handle_loopcli_dispatch(self):
        body = self._read_body()
        if body is None:
            return
        agent_id = body.get("agent", "").strip()
        title = body.get("title", "").strip()
        if not agent_id or not title:
            return self._send_json({"error": "agent and title are required"}, status=400)

        agent_dir = safe_agent_path(agent_id)
        if not agent_dir or not (agent_dir / "AGENT").exists():
            return self._send_json({"error": f"Agent '{agent_id}' not found"}, status=404)

        task = create_task(
            agent_dir, title,
            description=body.get("description", ""),
            assignee=agent_id,
        )

        # Start claude process for this agent
        prompt_file = agent_dir / "PROMPT.md"
        prompt = ""
        if prompt_file.exists():
            prompt = prompt_file.read_text(encoding="utf-8")

        proc = subprocess.Popen(
            ["claude", "--print", "--dangerously-skip-permissions"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(agent_dir),
        )
        if prompt:
            proc.stdin.write(prompt.encode("utf-8"))
            proc.stdin.close()

        self._send_json({
            "task": task,
            "pid": proc.pid,
            "status": "dispatched",
        }, status=201)

    def _handle_message_send(self):
        body = self._read_body()
        if body is None:
            return
        content = body.get("content", "").strip()
        if not content:
            return self._send_json({"error": "content is required"}, status=400)

        agent_id = body.get("agent", "main").strip() or "main"
        agent_dir = safe_agent_path(agent_id)
        if not agent_dir:
            return self._send_json({"error": "Invalid agent"}, status=400)
        if not (agent_dir / "AGENT").exists():
            return self._send_json({"error": f"Agent '{agent_id}' not found"}, status=404)

        msg_file = write_inbox_message(agent_dir, "webui", content)
        self._send_json({"status": "sent", "agent": agent_id, "file": msg_file.name}, status=201)

    def _handle_agent_enable(self, action):
        body = self._read_body()
        if body is None:
            return
        agent_id = body.get("agent", "").strip()
        if not agent_id:
            return self._send_json({"error": "agent is required"}, status=400)
        if agent_id == "main":
            return self._send_json({"error": "cannot disable main agent"}, status=400)

        agent_dir = safe_agent_path(agent_id)
        if not agent_dir:
            return self._send_json({"error": "Invalid agent"}, status=400)
        if not (agent_dir / "AGENT").exists():
            return self._send_json({"error": f"Agent '{agent_id}' not found"}, status=404)

        set_agent_enabled(agent_dir, action == "enable")
        self._send_json({"status": "ok", "agent": agent_id, "enabled": action == "enable"})

    def _handle_automation_cleanup_logs(self):
        """清理大型日志文件（超过 1MB）"""
        log_dir = MAIN_DIR / "log"
        results = []
        for log_file in log_dir.glob("*.log"):
            try:
                size_mb = log_file.stat().st_size / (1024 * 1024)
                if size_mb > 1:
                    # 重命名为 .bak
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{log_file.stem}_{timestamp}.log.bak"
                    backup_path = log_file.parent / backup_name
                    log_file.rename(backup_path)
                    results.append({"file": log_file.name, "size_mb": round(size_mb, 2), "action": "archived", "backup": backup_name})
            except Exception as e:
                results.append({"file": log_file.name, "error": str(e)})
        self._send_json({"action": "cleanup_logs", "results": results})

    def _handle_automation_compress_memory(self):
        """压缩 thoughts.md（保留最近 5 轮）"""
        thoughts_file = MAIN_DIR / "thoughts.md"
        if not thoughts_file.exists():
            return self._send_json({"action": "compress_memory", "status": "no_file"})
        lines = thoughts_file.read_text(encoding="utf-8").split("\n")
        if len(lines) <= 50:
            return self._send_json({"action": "compress_memory", "status": "not_needed", "lines": len(lines)})
        # 保留最近 5 轮（约 50 行）
        compressed = "\n".join(lines[-50:])
        thoughts_file.write_text(compressed, encoding="utf-8")
        self._send_json({"action": "compress_memory", "status": "compressed", "original_lines": len(lines), "new_lines": len(compressed.split("\n"))})

    def _handle_automation_disable_idle_agents(self):
        """禁用空闲的 agents（没有任务且状态为 idle）"""
        agents_dir = LOOPCLI_ROOT / "agents"
        disabled = []
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            agent_file = agent_dir / "AGENT"
            if not agent_file.exists():
                continue
            # 检查是否已禁用
            content = agent_file.read_text(encoding="utf-8")
            if "disabled: true" in content or "disabled" in content:
                continue
            # 检查状态
            state_file = agent_dir / "memory" / "state.json"
            if state_file.exists():
                state = read_json(state_file, {})
                if state.get("status") == "idle":
                    # 禁用 agent
                    agent_file.write_text(content + "\ndisabled: true\n", encoding="utf-8")
                    disabled.append(agent_dir.name)
        self._send_json({"action": "disable_idle_agents", "disabled": disabled, "count": len(disabled)})

    def _handle_automation_health_check(self):
        """系统健康检查"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "main_agent": {},
            "logs": {},
            "agents": {},
            "disk": {}
        }
        # Main agent 状态
        state = read_json(MAIN_DIR / "memory" / "state.json", {})
        health["main_agent"] = {
            "status": state.get("status", "unknown"),
            "last_run": state.get("last_run", "never"),
            "run_count": state.get("run_count", 0)
        }
        # 日志检查
        log_dir = MAIN_DIR / "log"
        for log_file in log_dir.glob("*.log"):
            size_mb = log_file.stat().st_size / (1024 * 1024)
            health["logs"][log_file.name] = {
                "size_mb": round(size_mb, 2),
                "needs_rotation": size_mb > 1
            }
        # Agents 统计
        agents_dir = LOOPCLI_ROOT / "agents"
        enabled = 0
        disabled = 0
        for agent_dir in agents_dir.iterdir():
            if not agent_dir.is_dir():
                continue
            agent_file = agent_dir / "AGENT"
            if agent_file.exists():
                content = agent_file.read_text(encoding="utf-8")
                if "disabled: true" in content or "disabled" in content:
                    disabled += 1
                else:
                    enabled += 1
        health["agents"] = {"enabled": enabled, "disabled": disabled, "total": enabled + disabled}
        self._send_json({"action": "health_check", "health": health})

    def _handle_automation_git_sync(self):
        """执行 Git 同步"""
        git_dir = LOOPCLI_ROOT
        try:
            # Git add
            result_add = subprocess.run(
                ["git", "add", "-A"],
                cwd=str(git_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            # Git commit
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result_commit = subprocess.run(
                ["git", "commit", "-m", f"auto: loopcli sync {timestamp}"],
                cwd=str(git_dir),
                capture_output=True,
                text=True,
                timeout=30
            )
            # Git push
            result_push = subprocess.run(
                ["git", "push"],
                cwd=str(git_dir),
                capture_output=True,
                text=True,
                timeout=60
            )
            self._send_json({
                "action": "git_sync",
                "status": "success",
                "commit": result_commit.stdout,
                "push": result_push.stdout
            })
        except subprocess.TimeoutExpired:
            self._send_json({"action": "git_sync", "status": "timeout", "error": "命令超时"}, status=500)
        except Exception as e:
            self._send_json({"action": "git_sync", "status": "error", "error": str(e)}, status=500)

    def _handle_longtask_get(self):
        """获取长期任务内容"""
        longtask_file = LOOPCLI_ROOT / "longtask.md"
        if not longtask_file.exists():
            return self._send_json({"exists": False, "content": ""})
        try:
            content = longtask_file.read_text(encoding="utf-8")
            return self._send_json({"exists": True, "content": content})
        except Exception as e:
            return self._send_json({"error": str(e)}, status=500)

    def _handle_messages_get(self):
        """获取所有 agent 的消息列表"""
        messages = []
        agents_dir = LOOPCLI_ROOT / "agents"

        # 扫描 agents 目录
        if agents_dir.is_dir():
            for child in agents_dir.iterdir():
                if not child.is_dir() or not (child / "AGENT").exists():
                    continue
                inbox_dir = child / "inbox"
                if not inbox_dir.is_dir():
                    continue
                # 读取 inbox 中的消息文件
                for msg_file in sorted(inbox_dir.glob("*.md"), reverse=True):
                    try:
                        content = msg_file.read_text(encoding="utf-8")
                        # 提取消息元数据
                        lines = content.splitlines()
                        sender = "unknown"
                        msg_type = "消息"
                        time_str = ""
                        msg_content = ""
                        for line in lines:
                            if line.startswith("# 来自"):
                                sender = line.split()[2] if len(line.split()) > 2 else "unknown"
                            elif line.startswith("- 类型："):
                                msg_type = line.split("：")[1] if "：" in line else "消息"
                            elif line.startswith("- 时间："):
                                time_str = line.split("：")[1] if "：" in line else ""
                            elif line.startswith("## 内容"):
                                break
                        # 获取实际内容
                        content_start = content.find("## 内容")
                        if content_start != -1:
                            msg_content = content[content_start + 6:].strip()

                        messages.append({
                            "id": msg_file.stem,
                            "agent": child.name,
                            "sender": sender,
                            "type": msg_type,
                            "time": time_str,
                            "content": msg_content[:200] + "..." if len(msg_content) > 200 else msg_content,
                            "file": msg_file.name
                        })
                    except Exception as e:
                        continue

        # 也检查 main agent 的 inbox
        main_dir = LOOPCLI_ROOT / "main"
        if main_dir.is_dir() and (main_dir / "AGENT").exists():
            inbox_dir = main_dir / "inbox"
            if inbox_dir.is_dir():
                for msg_file in sorted(inbox_dir.glob("*.md"), reverse=True):
                    try:
                        content = msg_file.read_text(encoding="utf-8")
                        lines = content.splitlines()
                        sender = "unknown"
                        msg_type = "消息"
                        time_str = ""
                        msg_content = ""
                        for line in lines:
                            if line.startswith("# 来自"):
                                sender = line.split()[2] if len(line.split()) > 2 else "unknown"
                            elif line.startswith("- 类型："):
                                msg_type = line.split("：")[1] if "：" in line else "消息"
                            elif line.startswith("- 时间："):
                                time_str = line.split("：")[1] if "：" in line else ""
                            elif line.startswith("## 内容"):
                                break
                        content_start = content.find("## 内容")
                        if content_start != -1:
                            msg_content = content[content_start + 6:].strip()

                        messages.append({
                            "id": msg_file.stem,
                            "agent": "main",
                            "sender": sender,
                            "type": msg_type,
                            "time": time_str,
                            "content": msg_content[:200] + "..." if len(msg_content) > 200 else msg_content,
                            "file": msg_file.name
                        })
                    except Exception as e:
                        continue

        return self._send_json({"messages": messages[:50]})  # 限制返回最近 50 条

    def _handle_stats_get(self):
        """获取系统统计信息"""
        try:
            # 统计 agents
            all_agents = scan_agents()
            enabled_agents = [a for a in all_agents if a.get("status") != "disabled"]
            disabled_agents = [a for a in all_agents if a.get("status") == "disabled"]

            # 统计任务
            all_tasks = get_all_agent_tasks()
            done_tasks = sum(1 for t in all_tasks if t.get("status") == "done")
            pending_tasks = sum(1 for t in all_tasks if t.get("status") == "pending")

            # 统计消息
            total_messages = 0
            agents_dir = LOOPCLI_ROOT / "agents"
            if agents_dir.is_dir():
                for child in agents_dir.iterdir():
                    if not child.is_dir():
                        continue
                    inbox_dir = child / "inbox"
                    if inbox_dir.is_dir():
                        total_messages += len(list(inbox_dir.glob("*.md")))

            # 获取运行时间
            main_state = read_json(LOOPCLI_ROOT / "main" / "memory" / "state.json", {})
            run_count = main_state.get("run_count", 0)
            last_run = main_state.get("last_run", "未知")

            # 获取日志大小
            import os
            total_log_size = 0
            for child in LOOPCLI_ROOT.iterdir():
                if child.is_dir() and (child / "log").is_dir():
                    for log_file in (child / "log").glob("*.md"):
                        total_log_size += log_file.stat().st_size

            return self._send_json({
                "agents": {
                    "total": len(all_agents),
                    "enabled": len(enabled_agents),
                    "disabled": len(disabled_agents)
                },
                "tasks": {
                    "total": len(all_tasks),
                    "done": done_tasks,
                    "pending": pending_tasks
                },
                "messages": total_messages,
                "runtime": {
                    "run_count": run_count,
                    "last_run": last_run
                },
                "storage": {
                    "log_size_mb": round(total_log_size / 1024 / 1024, 2)
                }
            })
        except Exception as e:
            return self._send_json({"error": str(e)}, status=500)

    def _handle_screenshots_get(self):
        """获取截图列表"""
        try:
            screenshots_dir = WEBUI_DIR / "screenshots"
            if not screenshots_dir.exists():
                return self._send_json({"screenshots": [], "total": 0})

            screenshots = []
            for png_file in sorted(screenshots_dir.glob("*.png"), key=lambda p: p.stat().st_mtime, reverse=True):
                stat = png_file.stat()
                screenshots.append({
                    "name": png_file.name,
                    "size": round(stat.st_size / 1024, 2),  # KB
                    "modified": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                    "url": f"/screenshots/{png_file.name}"
                })

            return self._send_json({
                "screenshots": screenshots[:50],  # 最多返回50个
                "total": len(screenshots)
            })
        except Exception as e:
            return self._send_json({"error": str(e)}, status=500)

    def _handle_health_get(self):
        """健康检查端点"""
        try:
            # WebUI运行状态
            uptime = time.time() - SERVER_START_TIME

            # Agent状态
            agents = scan_agents()
            active_agents = [a for a in agents if not a.get("disabled", False)]
            disabled_agents = [a for a in agents if a.get("disabled", False)]

            # 日志大小
            log_size = 0
            log_path = MAIN_DIR / "log" / "run.md"
            if log_path.exists():
                log_size = log_path.stat().st_size

            response_data = {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "uptime_seconds": round(uptime, 2),
                "agents": {
                    "total": len(agents),
                    "active": len(active_agents),
                    "disabled": len(disabled_agents)
                },
                "webui": {
                    "port": 8080,
                    "log_size_bytes": log_size
                }
            }

            # 如果psutil可用，添加系统信息
            if HAS_PSUTIL:
                try:
                    cpu_percent = psutil.cpu_percent(interval=0.1)
                    memory = psutil.virtual_memory()
                    disk = psutil.disk_usage(str(LOOPCLI_ROOT))

                    response_data["system"] = {
                        "cpu_percent": cpu_percent,
                        "memory_percent": memory.percent,
                        "memory_available_gb": round(memory.available / (1024**3), 2),
                        "disk_percent": disk.percent,
                        "disk_free_gb": round(disk.free / (1024**3), 2)
                    }
                except Exception as e:
                    response_data["system"] = {"error": str(e)}

            return self._send_json(response_data)

        except Exception as e:
            return self._send_json({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, status=500)

    def _handle_longtask_clear(self):
        """清空长期任务"""
        longtask_file = LOOPCLI_ROOT / "longtask.md"
        try:
            if longtask_file.exists():
                longtask_file.unlink()
                return self._send_json({"status": "cleared", "message": "长期任务已取消"})
            else:
                return self._send_json({"status": "no_task", "message": "无长期任务"})
        except Exception as e:
            return self._send_json({"error": str(e)}, status=500)

    def _handle_longtask_update(self):
        """更新长期任务内容"""
        body = self._read_body()
        if body is None:
            return
        content = body.get("content", "")
        print(f"[DEBUG] _handle_longtask_update called, content: {content}")
        longtask_file = LOOPCLI_ROOT / "longtask.md"
        try:
            longtask_file.write_text(content, encoding="utf-8")
            return self._send_json({"status": "updated", "message": "长期任务已更新", "content": content})
        except Exception as e:
            return self._send_json({"error": str(e)}, status=500)


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True


def main():
    host = os.environ.get("LOOPCLI_HOST", "127.0.0.1")
    port = 8080
    server = ThreadedHTTPServer((host, port), WebUIHandler)
    print(f"LoopCLI WebUI Server running on http://{host}:{port}")
    print(f"Static files served from: {WEBUI_DIR}")
    print(f"Agent root: {LOOPCLI_ROOT}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.server_close()


if __name__ == "__main__":
    main()
