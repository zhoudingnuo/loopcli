import argparse
import json
import msvcrt
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "main" / "webui"))

# 微信桥接模块
try:
    from wechat_bridge import create_wechat_bridge, weixin_qr_login, weixin_verify_token
    WECHAT_AVAILABLE = True
except ImportError:
    WECHAT_AVAILABLE = False

from loopcli_lib import (
    LOOPCLI_ROOT,
    AGENT_MARKER,
    read_json,
    write_json,
    safe_agent_path,
    get_agent_marker,
    is_agent_enabled,
    discover_agents as _discover_agents,
    create_task,
    write_inbox_message,
    set_agent_enabled,
)

LOOPCLI_DIR = str(LOOPCLI_ROOT)

# Fix Windows GBK encoding issue - force UTF-8 for stdout/stderr
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SUBAGENT_DIR = os.path.join(LOOPCLI_DIR, "subagent")
CLAUDE = os.path.join(os.environ.get("APPDATA", ""), "npm", "claude.cmd")

LOGS_DIR = os.path.join(LOOPCLI_DIR, "logs")
GIT_TOKEN_FILE = os.path.join(LOOPCLI_DIR, ".gittoken")
PRICING_FILE = os.path.join(LOOPCLI_DIR, "scripts", "pricing.json")

# 加载定价
def load_pricing():
    try:
        with open(PRICING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
DEFAULT_PROMPT = """读取 SOUL.md 作为你的身份。
读取 memory/tasks.json 获取分配给你的任务。
技能文件在 D:/loopcli/skill/（全局），按需读取，不要开局全读。

禁止：绝对不要调用 AskUserQuestion（你运行在非交互模式下，没人能回答，会永远卡住）。

执行步骤：
1. 从 tasks.json 中找 status 为 "pending" 的第一个任务
2. 执行该任务
3. 将结果写入 memory/results/ 目录（以时间戳命名）
4. 将该任务 status 改为 "done"，写回 tasks.json
5. 更新 memory/state.json（标记完成、记录时间戳）
6. 将本次运行摘要追加到 log/run.md
7. 通过 inbox 通知 main：写入 D:/loopcli/main/inbox/<你的名字>_<时间>.md，简要报告任务结果
8. 如果没有 pending 任务，输出 "IDLE" 并结束本轮
"""


# ─── 工具函数 ───

def discover_agents(include_disabled=False):
    """Wrapper that returns same format as before (name+path strings)."""
    return _discover_agents(include_disabled=include_disabled)


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


def load_agent_state(agent_path):
    state_file = os.path.join(agent_path, "memory", "state.json")
    if os.path.isfile(state_file):
        return read_json(state_file)
    return None


def load_agent_tasks(agent_path):
    tasks_file = os.path.join(agent_path, "memory", "tasks.json")
    if os.path.isfile(tasks_file):
        return read_json(tasks_file, [])
    return []


def rotate_log(log_path, max_size=1_000_000, max_backups=3):
    """轮转日志文件：超过 max_size 时依次重命名为 .1 .2 .3，最多保留 max_backups 个归档"""
    if not os.path.isfile(log_path):
        return
    try:
        if os.path.getsize(log_path) < max_size:
            return
    except OSError:
        return
    try:
        oldest = f"{log_path}.{max_backups}"
        if os.path.isfile(oldest):
            os.remove(oldest)
        for i in range(max_backups, 1, -1):
            src = f"{log_path}.{i - 1}"
            dst = f"{log_path}.{i}"
            if os.path.isfile(src):
                os.rename(src, dst)
        os.rename(log_path, f"{log_path}.1")
    except PermissionError:
        # 文件被占用，跳过轮转
        pass
    except OSError as e:
        # 其他错误也静默处理，避免影响主流程
        pass


# ─── 子命令: create ───

def cmd_create(args):
    template_id = args.template
    task_desc = args.task or ""

    tpl_file = find_template(template_id)
    if not tpl_file:
        print(f"[错误] 找不到模板: {template_id}")
        print("用 loopcli templates 查看所有可用模板")
        sys.exit(1)

    with open(tpl_file, "r", encoding="utf-8") as f:
        soul_content = f.read()

    agent_dir = os.path.join(LOOPCLI_DIR, "agents", template_id)
    if os.path.exists(agent_dir):
        print(f"[跳过] Agent 已存在: {agent_dir}")
        if task_desc:
            cmd_task_inner(template_id, task_desc, "")
        return

    os.makedirs(os.path.join(agent_dir, "memory", "results"), exist_ok=True)
    os.makedirs(os.path.join(agent_dir, "log"), exist_ok=True)

    with open(os.path.join(agent_dir, AGENT_MARKER), "w", encoding="utf-8") as f:
        f.write("type: main\n")

    with open(os.path.join(agent_dir, "SOUL.md"), "w", encoding="utf-8") as f:
        f.write(soul_content)

    with open(os.path.join(agent_dir, "PROMPT.md"), "w", encoding="utf-8") as f:
        f.write(DEFAULT_PROMPT)

    state = {"agent": template_id, "status": "idle", "current_task": None, "last_run": None, "run_count": 0, "created": datetime.now().strftime("%Y-%m-%d")}
    write_json(os.path.join(agent_dir, "memory", "state.json"), state)

    tasks = []
    if task_desc:
        tasks.append({"id": 1, "status": "pending", "title": task_desc, "description": task_desc, "created": datetime.now().strftime("%Y-%m-%d"), "assignee": template_id})
    write_json(os.path.join(agent_dir, "memory", "tasks.json"), tasks)

    with open(os.path.join(agent_dir, "log", "run.md"), "w", encoding="utf-8") as f:
        f.write("# 运行日志\n\n| 时间 | 状态 | 任务 | 摘要 |\n|------|------|------|------|\n")

    print(f"[创建成功] {template_id}")
    print(f"  目录: {agent_dir}")
    if task_desc:
        print(f"  任务: {task_desc}")
    print(f"  下一轮 loopcli 将自动启动该 Agent")


# ─── 子命令: task ───

def cmd_task_inner(agent_name, title, desc):
    # Check agents/ folder first, then root for main
    agent_dir = os.path.join(LOOPCLI_DIR, "agents", agent_name)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        agent_dir = os.path.join(LOOPCLI_DIR, agent_name)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        print(f"[错误] 不是有效的 Agent: {agent_name}")
        sys.exit(1)

    task = create_task(
        agent_dir, title,
        description=desc or title,
        assignee=agent_name,
        created=datetime.now().strftime("%Y-%m-%d"),
    )
    print(f"[派发成功] {agent_name} <- #{task['id']} {title}")


def cmd_task(args):
    cmd_task_inner(args.agent, args.title, args.desc)


# ─── 子命令: list ───

def cmd_list(args):
    agents = discover_agents(include_disabled=True)
    if not agents:
        print("没有发现任何 Agent")
        return
    print(f"{'Agent':<45} {'启用':<6} {'状态':<10} {'任务数':<8} {'最后运行'}")
    print("-" * 95)
    for a in agents:
        enabled = "是" if is_agent_enabled(a["path"]) else "否"
        state = load_agent_state(a["path"]) or {}
        tasks = load_agent_tasks(a["path"])
        pending = len([t for t in tasks if t.get("status") == "pending"])
        status = state.get("status", "?")
        last_run = state.get("last_run", "-")
        print(f"{a['name']:<45} {enabled:<6} {status:<10} {pending:<8} {last_run}")


# ─── 子命令: templates ───

def cmd_templates(args):
    found = []
    for dept in sorted(os.listdir(SUBAGENT_DIR)):
        dept_dir = os.path.join(SUBAGENT_DIR, dept)
        if not os.path.isdir(dept_dir):
            continue
        for fname in sorted(os.listdir(dept_dir)):
            if fname.endswith(".md"):
                found.append(fname[:-3])
    if args.filter:
        found = [t for t in found if args.filter.lower() in t.lower()]
    print(f"共 {len(found)} 个模板:")
    for t in found:
        print(f"  {t}")


# ─── 子命令: run（主循环）───

# ANSI 颜色
class C:
    RST = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"


# 分屏全局状态
_ob = [0]          # 输出区底行
_buf = [""]         # 输入缓冲
_lock = threading.Lock()


def out(text=""):
    """往滚动区写一行，光标不动"""
    with _lock:
        sys.stdout.write(f"\033[s")                       # 保存光标
        sys.stdout.write(f"\033[{_ob[0]};1H")             # 移到输出区底
        sys.stdout.write(text + "\n")                      # 写内容（在滚动区内滚动）
        sys.stdout.write(f"\033[u")                        # 恢复光标到输入区
        sys.stdout.flush()


def draw_input():
    """重绘输入区，光标停在 > 后面"""
    with _lock:
        cols = shutil.get_terminal_size().columns
        ob = _ob[0]
        buf = _buf[0][:cols - 25]
        sys.stdout.write(f"\033[{ob+1};1H\033[K{C.CYAN}{'─'*cols}{C.RST}")
        sys.stdout.write(f"\033[{ob+2};1H\033[K{C.CYAN} > {C.RST}{buf}{C.DIM}█{C.RST} {C.DIM}(Enter发送, exit退出){C.RST}")
        # 光标移到 > 后面，紧跟用户输入内容
        sys.stdout.write(f"\033[{ob+2};{4 + len(buf)}H")
        sys.stdout.flush()


def p_sub(text):
    out(f"  {C.DIM}{text}{C.RST}")

def p_agent_header(name, iteration):
    out(f"\n{C.CYAN}{C.BOLD} {name} {C.RST} {C.DIM}iter #{iteration}{C.RST}")


# Agent 颜色池
_AGENT_COLORS = [
    "\033[36m",  # CYAN
    "\033[33m",  # YELLOW
    "\033[32m",  # GREEN
    "\033[35m",  # MAGENTA
    "\033[34m",  # BLUE
    "\033[31m",  # RED
]
_agent_color_map = {}

def _agent_tag(name):
    """返回 [agent名] 彩色标签"""
    if name not in _agent_color_map:
        _agent_color_map[name] = _AGENT_COLORS[len(_agent_color_map) % len(_AGENT_COLORS)]
    c = _agent_color_map[name]
    short = name[:16]
    return f"{c}[{short}]{C.RST}"


def handle_event(agent_name, line):
    line = line.strip()
    if not line:
        return
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        out(f"  {_agent_tag(agent_name)} {C.DIM}{line}{C.RST}")
        return

    event_type = event.get("type", "")
    tag = _agent_tag(agent_name)

    if event_type == "assistant":
        msg = event.get("message", {})
        for block in msg.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    for ln in text.splitlines():
                        out(f"  {tag} {ln}")
            elif block.get("type") == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {})
                detail = ""
                for k in ("file_path", "command", "pattern"):
                    if k in inp:
                        detail = inp[k]
                        break
                out(f"  {tag} {C.YELLOW}●{C.RST} {C.BOLD}{name}{C.RST}({C.DIM}{detail}{C.RST})")

    elif event_type == "tool_result":
        content = event.get("content", "")
        texts = []
        if isinstance(content, list):
            texts = [b.get("text", "") for b in content if b.get("text")]
        elif isinstance(content, str):
            texts = [content]
        for text in texts:
            short = text[:150].replace("\n", " ")
            out(f"  {tag}   {C.DIM}↳ {short}{C.RST}")

    elif event_type == "result":
        text = event.get("result", "")
        if text:
            for ln in text[:300].splitlines():
                out(f"  {tag} {C.GREEN}{ln}{C.RST}")
        duration = event.get("duration_ms", "")
        if duration:
            out(f"  {tag} {C.DIM}⏱ {duration}ms{C.RST}")

    elif event_type == "error":
        out(f"  {tag} {C.RED}✘ {event.get('error', '')}{C.RST}")


def run_agent(agent, iteration, run_log_dir):
    name = agent["name"]
    path = agent["path"]
    prompt_file = os.path.join(path, "PROMPT.md")
    log_file_path = os.path.join(path, "log", "raw.log")
    run_agent_log = os.path.join(run_log_dir, f"{name}.log")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.isfile(prompt_file):
        out(f"  {C.DIM}{name}: 没有 PROMPT.md，跳过{C.RST}")
        return

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read()

    os.makedirs(os.path.join(path, "log"), exist_ok=True)
    rotate_log(log_file_path)
    log_file = open(log_file_path, "a", encoding="utf-8")
    agent_log = open(run_agent_log, "a", encoding="utf-8")

    try:
        header = f"\n[{ts}] --- 开始 (第{iteration}轮) ---\n"
        log_file.write(header)
        agent_log.write(header)
        log_file.flush()
        agent_log.flush()

        env = {**os.environ, "IS_SANDBOX": "1"}

        proc = subprocess.Popen(
            [CLAUDE, "--print", "--verbose", "--output-format", "stream-json", "--dangerously-skip-permissions"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=path,
        )

        proc.stdin.write(prompt.encode("utf-8"))
        proc.stdin.close()

        # 看门狗：5 分钟无输出则杀进程
        last_output = [time.time()]
        stuck = [False]

        def watchdog():
            while proc.poll() is None:
                if time.time() - last_output[0] > 300:  # 5 分钟
                    stuck[0] = True
                    out(f"  {_agent_tag(name)} {C.RED}⏰ 超时（5分钟无输出），正在终止...{C.RST}")
                    proc.kill()
                    try:
                        proc.stdout.close()
                    except Exception:
                        pass
                    return
                time.sleep(10)

        # 后台线程读 stdout，避免 Windows 管道阻塞主线程
        def drain_stdout():
            for line in iter(proc.stdout.readline, b''):
                last_output[0] = time.time()
                decoded = line.decode("utf-8", errors="replace")
                log_file.write(decoded)
                agent_log.write(decoded)
                log_file.flush()
                agent_log.flush()
                handle_event(name, decoded)

        reader = threading.Thread(target=drain_stdout, daemon=True)
        reader.start()

        wd = threading.Thread(target=watchdog, daemon=True)
        wd.start()

        # 并发读 stderr
        stderr_chunks = []
        def drain_stderr():
            for line in proc.stderr:
                stderr_chunks.append(line.decode("utf-8", errors="replace"))

        stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
        stderr_thread.start()

        # 等进程退出
        proc.wait()

        # 进程退出后关 stdout，解除 drain_stdout 阻塞
        try:
            proc.stdout.close()
        except Exception:
            pass

        reader.join(timeout=5)
        stderr_thread.join(timeout=5)
        wd.join(timeout=5)

        stderr_output = "".join(stderr_chunks)
        if stderr_output:
            out(f"  {_agent_tag(name)} {C.RED}STDERR: {stderr_output[:200]}{C.RST}")
            log_file.write(stderr_output)
            agent_log.write(stderr_output)

        if stuck[0]:
            # 超时被杀：记录错误并通知 main
            footer = f"\n[{ts}] --- 超时终止 (killed, 5min no output) ---\n"
            log_file.write(footer)
            agent_log.write(footer)
            # 写错误记录
            err_file = os.path.join(path, "memory", "errors.json")
            errs = read_json(err_file, [])
            errs.append({"time": ts, "agent": name, "error": "timeout", "detail": "5分钟无输出，进程被看门狗终止"})
            write_json(err_file, errs)
            # 通知 main
            inbox_dir = os.path.join(LOOPCLI_DIR, "main", "inbox")
            os.makedirs(inbox_dir, exist_ok=True)
            msg_ts = datetime.now().strftime("%Y%m%d_%H%M")
            msg_file = os.path.join(inbox_dir, f"watchdog_{msg_ts}.md")
            with open(msg_file, "w", encoding="utf-8") as f:
                f.write(f"# 看门狗超时报告\n- 类型：错误\n- 时间：{ts}\n\n## 内容\nAgent `{name}` 超过 5 分钟无输出，已自动终止。\n")
        else:
            footer = f"\n[{ts}] --- 结束 (exit={proc.returncode}) ---\n"
            log_file.write(footer)
            agent_log.write(footer)
        log_file.write(footer)
        agent_log.write(footer)
    finally:
        log_file.close()
        agent_log.close()

    # 更新 state.json
    state_file = os.path.join(path, "memory", "state.json")
    state = load_agent_state(path) or {}
    state["status"] = "idle"
    state["last_run"] = ts
    state["run_count"] = state.get("run_count", 0) + 1
    write_json(state_file, state)

    status = "完成" if proc.returncode == 0 else f"异常(exit={proc.returncode})"
    color = C.GREEN if "完成" in status else C.RED
    sym = "✔" if "完成" in status else "✘"
    out(f"  {color}{sym} {name} {status}{C.RST}")

    # 查询本轮花费
    current = query_model_usage()
    pricing = load_pricing()
    if current is None:
        # API 查询失败，提示用户手动检查
        out(f"  {C.YELLOW}⚠ 花费查询失败，运行: python D:/loopcli/scripts/usage.py{C.RST}")
    elif current and pricing:
        prev = load_last_usage()
        diff = {}
        for model in set(list(prev.keys()) + list(current.keys())):
            d = current.get(model, 0) - prev.get(model, 0)
            if d > 0:
                diff[model] = d
        if diff:
            total_cost, _ = calc_cost(diff, pricing)
            out(f"  {C.DIM}  💰 ${total_cost:.4f}{C.RST}")
        else:
            out(f"  {C.DIM}💰 本轮无新增消耗{C.RST}")
        save_last_usage(current)


def git_push():
    """自动 commit 和 push 到 GitHub"""
    token_file = GIT_TOKEN_FILE
    if not os.path.isfile(token_file):
        return
    with open(token_file, "r") as f:
        token = f.read().strip()
    if not token:
        return
    try:
        git = resolve_git()
        r = subprocess.run([git, "add", "-A"], cwd=LOOPCLI_DIR, capture_output=True, text=True, timeout=30)
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "unknown error").strip()
            out(f"  {C.RED}[git] add 失败: {err}{C.RST}")
            return
        r = subprocess.run(
            [git, "commit", "-m", f"auto: loopcli sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            cwd=LOOPCLI_DIR, capture_output=True, text=True, timeout=30
        )
        if r.returncode != 0 and "nothing to commit" not in (r.stdout or ""):
            err = (r.stderr or r.stdout or "unknown error").strip()
            out(f"  {C.RED}[git] commit 失败: {err}{C.RST}")
            return
        askpass_script = os.path.join(LOOPCLI_DIR, ".git_askpass.bat")
        with open(askpass_script, "w") as f:
            f.write("@echo %GH_TOKEN%\n")
        push_env = {
            **os.environ,
            "GH_TOKEN": token,
            "GIT_ASKPASS": askpass_script,
            "GIT_TERMINAL_PROMPT": "0",
        }
        r = subprocess.run(
            [git, "push", "https://x-access-token@github.com/zhoudingnuo/loopcli.git", "main"],
            cwd=LOOPCLI_DIR, capture_output=True, text=True, timeout=60, env=push_env,
        )
        os.remove(askpass_script)
        if r.returncode != 0:
            err = (r.stderr or r.stdout or "unknown error").strip()
            out(f"  {C.RED}[git] push 失败: {err}{C.RST}")
        else:
            out(f"  {C.GREEN}[git] 已同步到 GitHub{C.RST}")
    except Exception as e:
        out(f"  {C.RED}[git] 同步失败: {e}{C.RST}")


def resolve_git():
    """找到 git.exe 的完整路径"""
    for p in os.environ.get("PATH", "").split(";"):
        candidate = os.path.join(p, "git.exe")
        if os.path.isfile(candidate):
            return candidate
    for d in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        candidate = os.path.join(d, "git.exe")
        if os.path.isfile(candidate):
            return candidate
    return "git"


def _get_api_creds():
    """获取 API 凭证：优先环境变量，其次 .env.json"""
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if base_url and token:
        return base_url, token
    env_file = os.path.join(LOOPCLI_DIR, ".env.json")
    if os.path.isfile(env_file):
        cfg = read_json(env_file, {})
        return cfg.get("ANTHROPIC_BASE_URL", ""), cfg.get("ANTHROPIC_AUTH_TOKEN", "")
    return "", ""


def query_model_usage():
    """查询各模型的 token 用量，返回 {model: totalTokens}"""
    try:
        base_url, token = _get_api_creds()
        if not base_url or not token:
            out(f"  {C.YELLOW}⚠ 花费查询失败: 未设置 ANTHROPIC_BASE_URL 或 ANTHROPIC_AUTH_TOKEN{C.RST}")
            return None

        from urllib.parse import urlparse
        import urllib.parse, urllib.request
        from datetime import timedelta

        parsed = urlparse(base_url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        now = datetime.now()
        start = (now - timedelta(hours=24)).strftime("%Y-%m-%d %H:00:00")
        end = now.strftime("%Y-%m-%d %H:%M:%S")
        params = f"?startTime={urllib.parse.quote(start)}&endTime={urllib.parse.quote(end)}"

        req = urllib.request.Request(
            domain + "/api/monitor/usage/model-usage" + params,
            headers={"Authorization": token, "Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            summary = data.get("data", {}).get("totalUsage", {})
            models = {}
            for m in summary.get("modelSummaryList", []):
                models[m["modelName"]] = m["totalTokens"]
            return models
    except urllib.error.HTTPError as e:
        out(f"  {C.YELLOW}⚠ 花费查询失败: HTTP {e.code} - {e.reason}{C.RST}")
        return None
    except urllib.error.URLError as e:
        out(f"  {C.YELLOW}⚠ 花费查询失败: 网络错误 - {e.reason}{C.RST}")
        return None
    except Exception as e:
        out(f"  {C.YELLOW}⚠ 花费查询失败: {e}{C.RST}")
        return None


def calc_cost(models, pricing):
    """根据模型用量和定价计算总费用"""
    total = 0.0
    details = []
    for model, tokens in models.items():
        p = pricing.get(model, {})
        avg_price = (p.get("input_per_million", 0) + p.get("output_per_million", 0)) / 2
        cost = (tokens / 1_000_000) * avg_price
        total += cost
        details.append((model, tokens, cost))
    return total, details


LAST_USAGE_FILE = os.path.join(LOOPCLI_DIR, "logs", ".last_usage.json")


def load_last_usage():
    """读取上次保存的用量快照"""
    return read_json(LAST_USAGE_FILE, {})


def save_last_usage(usage):
    """保存用量快照到本地"""
    write_json(LAST_USAGE_FILE, usage)


def cmd_run(args):
    agents = discover_agents()
    if not agents:
        print("未发现任何 Agent（需要目录下有 AGENT 标记文件）")
        sys.exit(1)

    # ─── 启动微信桥接 ───
    wechat_handler = None
    if WECHAT_AVAILABLE:
        config_file = os.path.join(LOOPCLI_DIR, ".wechat_config.json")
        wechat_token = getattr(args, 'wechat_token', None)
        if not wechat_token and os.path.exists(config_file):
            cfg = read_json(config_file, {})
            wechat_token = cfg.get("token")

        if wechat_token:
            try:
                wechat_handler = create_wechat_bridge(
                    token=wechat_token,
                    inbox_dir="D:/loopcli/main/inbox",
                    report_dir="D:/loopcli/main/report",
                )
                print(f"[微信] 桥接已启动", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"[微信] 启动失败: {e}", file=sys.stderr, flush=True)

    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_log_dir = os.path.join(LOGS_DIR, run_id)
    os.makedirs(run_log_dir, exist_ok=True)

    meta = {
        "run_id": run_id,
        "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "iterations": args.iterations or "无限",
        "agents": [a["name"] for a in agents],
        "wechat": wechat_handler is not None,
    }
    write_json(os.path.join(run_log_dir, "meta.json"), meta)

    # ─── 分屏终端设置 ───
    rows, cols = shutil.get_terminal_size().lines, shutil.get_terminal_size().columns
    _ob[0] = rows - 2  # 输出区底行

    sys.stdout.write("\033[?25l")              # 隐藏光标
    sys.stdout.write(f"\033[1;{_ob[0]}r")   # 滚动区域：1 到 rows-2
    sys.stdout.write(f"\033[1;1H")
    sys.stdout.flush()

    out(f"{C.BOLD}{C.CYAN}LoopCLI 启动 | {len(agents)} Agents | {run_id}{C.RST}")

    msg_queue = queue.Queue()
    stop_event = threading.Event()

    draw_input()

    def input_listener():
        while not stop_event.is_set():
            try:
                ch = msvcrt.getwch()
                if ch == '\r':
                    line = _buf[0].strip()
                    _buf[0] = ""
                    draw_input()
                    if line == "exit":
                        msg_queue.put("__EXIT__")
                        return
                    if line:
                        msg_queue.put(line)
                        out(f"  {C.GREEN}✔ -> main/inbox/{C.RST}")
                elif ch == '\x03':
                    msg_queue.put("__EXIT__")
                    return
                elif ch == '\x08':
                    _buf[0] = _buf[0][:-1]
                    draw_input()
                elif len(ch) == 1 and ord(ch) >= 32:
                    _buf[0] += ch
                    draw_input()
            except Exception:
                pass

    listener = threading.Thread(target=input_listener, daemon=True)
    listener.start()

    def process_queue():
        while True:
            try:
                msg = msg_queue.get_nowait()
            except queue.Empty:
                break
            if msg == "__EXIT__":
                return False
            inbox_dir = os.path.join(LOOPCLI_DIR, "main", "inbox")
            os.makedirs(inbox_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M")
            msg_file = os.path.join(inbox_dir, f"user_{ts}.md")
            with open(msg_file, "w", encoding="utf-8") as f:
                f.write(f"# 来自 zhoudingnuo 的消息\n- 类型：指令\n- 时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n## 内容\n{msg}\n")
        return True

    # ─── 主循环 ───
    pricing = load_pricing()
    count = 0
    while args.iterations == 0 or count < args.iterations:
        count += 1
        agents = discover_agents()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        iter_label = f"{count}/{args.iterations}" if args.iterations else str(count)

        out(f"{C.BOLD}{C.CYAN}══ Loop {iter_label} | {len(agents)} Agents | {ts} ══{C.RST}")

        threads = []
        for agent in agents:
            p_agent_header(agent["name"], count)
            t = threading.Thread(target=run_agent, args=(agent, count, run_log_dir))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        git_push()

        # 查询用量，和上次保存的做差
        current = query_model_usage()
        if current and pricing:
            prev = load_last_usage()
            diff = {}
            for model in set(list(prev.keys()) + list(current.keys())):
                d = current.get(model, 0) - prev.get(model, 0)
                if d > 0:
                    diff[model] = d
            if diff:
                total_cost, details = calc_cost(diff, pricing)
                for model, tokens, cost in details:
                    out(f"  {C.DIM}  {model}: +{tokens:,} tokens → ${cost:.4f}{C.RST}")
                out(f"  {C.BOLD}💰 本轮花费: ${total_cost:.4f}{C.RST}")
            else:
                out(f"  {C.DIM}💰 本轮无新增 token 消耗{C.RST}")
            save_last_usage(current)

        if not process_queue():
            break

        if args.iterations == 0 or count < args.iterations:
            draw_input()
            for _ in range(args.wait):
                if not process_queue():
                    stop_event.set()
                    break
                time.sleep(1)

    # 清理
    stop_event.set()
    if wechat_handler:
        wechat_handler.bridge.stop()
    sys.stdout.write("\033[?25h")              # 恢复光标
    sys.stdout.write(f"\033[r")
    sys.stdout.write(f"\033[{rows};1H")
    sys.stdout.flush()

    meta["finished"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta["total_iterations"] = count
    write_json(os.path.join(run_log_dir, "meta.json"), meta)
    print(f"运行结束，日志保存在: {run_log_dir}")


# ─── CLI 入口 ───

parser = argparse.ArgumentParser(description="LoopCLI — 多 Agent 自治系统")
sub = parser.add_subparsers(dest="command")

p_run = sub.add_parser("run", help="启动 Agent 循环（默认）")
p_run.add_argument("-n", "--iterations", type=int, default=0, help="迭代次数，0=无限")
p_run.add_argument("-w", "--wait", type=int, default=10, help="每轮间隔秒数（默认 10）")
p_run.add_argument("--wechat-token", default="", help="微信 ilink bot token")

p_create = sub.add_parser("create", help="从模板创建新 Agent")
p_create.add_argument("template", help="模板 ID，如 engineering-frontend-developer")
p_create.add_argument("--task", "-t", help="初始任务描述")

p_task = sub.add_parser("task", help="给 Agent 派发任务")
p_task.add_argument("agent", help="Agent 目录名")
p_task.add_argument("title", help="任务标题")
p_task.add_argument("--desc", "-d", default="", help="任务描述")

sub.add_parser("list", help="列出所有 Agent 及状态")

p_tpl = sub.add_parser("templates", help="列出可用模板")
p_tpl.add_argument("--filter", "-f", default="", help="按关键词筛选")

def cmd_enable(args):
    # Check agents/ folder first, then root for main
    agent_dir = os.path.join(LOOPCLI_DIR, "agents", args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        agent_dir = os.path.join(LOOPCLI_DIR, args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        print(f"[错误] 不是有效的 Agent: {args.agent}")
        sys.exit(1)
    set_agent_enabled(agent_dir, True)
    print(f"[已启用] {args.agent}")


def cmd_disable(args):
    if args.agent == "main":
        print("[错误] 不能禁用 main Agent")
        sys.exit(1)
    # Check agents/ folder first, then root for main
    agent_dir = os.path.join(LOOPCLI_DIR, "agents", args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        agent_dir = os.path.join(LOOPCLI_DIR, args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        print(f"[错误] 不是有效的 Agent: {args.agent}")
        sys.exit(1)
    set_agent_enabled(agent_dir, False)
    print(f"[已禁用] {args.agent}（loopcli run 将跳过此 Agent）")


p_msg = sub.add_parser("msg", help="给 Agent 发消息")
p_msg.add_argument("content", help="消息内容")
p_msg.add_argument("--agent", "-a", default="main", help="目标 Agent（默认 main）")

p_enable = sub.add_parser("enable", help="启用 Agent（可被 loopcli run 调度）")
p_enable.add_argument("agent", help="Agent 目录名")

p_disable = sub.add_parser("disable", help="禁用 Agent（跳过调度，节省 token）")
p_disable.add_argument("agent", help="Agent 目录名")

p_weixin = sub.add_parser("weixin", help="微信扫码登录/配置")
p_weixin.add_argument("action", nargs="?", default="setup", choices=["setup", "show", "bind"], help="操作: setup(扫码), show(查看), bind(绑定token)")
p_weixin.add_argument("--token", default="", help="ilink bot token（bind 模式使用）")


def cmd_weixin(args):
    """微信配置命令"""
    if not WECHAT_AVAILABLE:
        print("[错误] wechat_bridge 模块未找到")
        sys.exit(1)

    config_file = os.path.join(LOOPCLI_DIR, ".wechat_config.json")

    if args.action == "show":
        if os.path.exists(config_file):
            cfg = read_json(config_file, {})
            t = cfg.get("token", "")
            if t:
                masked = t[:8] + "..." + t[-4:] if len(t) > 12 else "***"
                print(f"[微信配置]")
                print(f"  Token: {masked}")
                print(f"  User ID: {cfg.get('user_id', '未知')}")
            else:
                print("[微信] 未配置 token")
        else:
            print("[微信] 未配置，运行 loopcli weixin setup 扫码登录")
        return

    if args.action == "bind":
        if not args.token:
            print("[错误] bind 需要指定 --token")
            sys.exit(1)
        print("[微信] 验证 token...")
        if weixin_verify_token(DEFAULT_BASE_URL, args.token):
            cfg = {"token": args.token}
            write_json(config_file, cfg)
            print(f"[微信] Token 已保存，运行 loopcli run 启动")
        else:
            print("[微信] Token 验证失败，请检查是否正确")
        return

    # setup: 扫码登录
    print("[微信] 开始扫码登录...")
    try:
        result = weixin_qr_login()
        cfg = {
            "token": result["token"],
            "base_url": result["base_url"],
            "user_id": result["user_id"],
            "bot_id": result["bot_id"],
        }
        write_json(config_file, cfg)
        print(f"\n[微信] 配置已保存到 {config_file}")
        print(f"[微信] 现在运行 loopcli run 即可启用微信桥接")
    except Exception as e:
        print(f"\n[微信] 扫码登录失败: {e}")
        sys.exit(1)


def cmd_msg(args):
    # Check agents/ folder first, then root for main
    agent_dir = os.path.join(LOOPCLI_DIR, "agents", args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        agent_dir = os.path.join(LOOPCLI_DIR, args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        print(f"[错误] 不是有效的 Agent: {args.agent}")
        sys.exit(1)
    msg_file = write_inbox_message(agent_dir, "user", args.content)
    print(f"[已发送] -> {args.agent}/inbox/  {args.content}")


if sys.argv[1:] and sys.argv[1] not in ("run", "create", "task", "list", "templates", "msg", "enable", "disable", "weixin", "-h", "--help"):
    sys.argv.insert(1, "run")

args = parser.parse_args()

if args.command == "create":
    cmd_create(args)
elif args.command == "task":
    cmd_task(args)
elif args.command == "list":
    cmd_list(args)
elif args.command == "templates":
    cmd_templates(args)
elif args.command == "msg":
    cmd_msg(args)
elif args.command == "enable":
    cmd_enable(args)
elif args.command == "disable":
    cmd_disable(args)
elif args.command == "weixin":
    cmd_weixin(args)
else:
    if not hasattr(args, "iterations"):
        args.iterations = 0
    if not hasattr(args, "wait"):
        args.wait = 10
    cmd_run(args)
