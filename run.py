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
SUBAGENT_DIR = os.path.join(LOOPCLI_DIR, "subagent")
CLAUDE = os.path.join(os.environ.get("APPDATA", ""), "npm", "claude.cmd")

LOGS_DIR = os.path.join(LOOPCLI_DIR, "logs")
GIT_TOKEN_FILE = os.path.join(LOOPCLI_DIR, ".gittoken")
DEFAULT_PROMPT = """读取 SOUL.md 作为你的身份。
读取 memory/tasks.json 获取分配给你的任务。
技能文件在 D:/loopcli/skill/（全局），按需读取，不要开局全读。

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
    oldest = f"{log_path}.{max_backups}"
    if os.path.isfile(oldest):
        os.remove(oldest)
    for i in range(max_backups, 1, -1):
        src = f"{log_path}.{i - 1}"
        dst = f"{log_path}.{i}"
        if os.path.isfile(src):
            os.rename(src, dst)
    os.rename(log_path, f"{log_path}.1")


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

    agent_dir = os.path.join(LOOPCLI_DIR, template_id)
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


# 全局分屏状态（由 cmd_run 设置）
_output_bottom = [0]  # 输出区底行号
_print_lock = threading.Lock()


def out(text=""):
    """输出到滚动区域，然后光标回到输入区"""
    with _print_lock:
        # 移到输出区底部，打印
        sys.stdout.write(f"\033[{_output_bottom[0]};1H")
        print(text, flush=True)
        # 重绘输入区，光标留在输入行
        _draw_input()


def _draw_input():
    """重绘底部输入区，光标留在输入行"""
    rows, cols = shutil.get_terminal_size().lines, shutil.get_terminal_size().columns
    ob = _output_bottom[0]
    buf = _input_buffer[0][:cols - 25] if _input_buffer else ""
    sys.stdout.write(f"\033[{ob + 1};1H\033[K{C.CYAN}{'─' * cols}{C.RST}")
    sys.stdout.write(f"\033[{ob + 2};1H\033[K{C.CYAN} > {C.RST}{buf}{C.DIM}█{C.RST} {C.DIM}(Enter发送, exit退出){C.RST}")
    # 光标留在输入行，不回输出区
    sys.stdout.write(f"\033[{ob + 2};{4 + len(buf)}H")
    sys.stdout.flush()


_input_buffer = [""]


def handle_event(agent_name, line):
    line = line.strip()
    if not line:
        return
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        print(f"  {C.DIM}{line}{C.RST}", flush=True)
        return

    event_type = event.get("type", "")

    if event_type == "assistant":
        msg = event.get("message", {})
        for block in msg.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    for ln in text.splitlines():
                        print(f"  {ln}", flush=True)
            elif block.get("type") == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {})
                detail = ""
                for k in ("file_path", "command", "pattern"):
                    if k in inp:
                        detail = inp[k]
                        break
                print(f"  {C.YELLOW}●{C.RST} {C.BOLD}{name}{C.RST}({C.DIM}{detail}{C.RST})", flush=True)

    elif event_type == "tool_result":
        content = event.get("content", "")
        texts = []
        if isinstance(content, list):
            texts = [b.get("text", "") for b in content if b.get("text")]
        elif isinstance(content, str):
            texts = [content]
        for text in texts:
            short = text[:150].replace("\n", " ")
            print(f"    {C.DIM}↳ {short}{C.RST}", flush=True)

    elif event_type == "result":
        text = event.get("result", "")
        if text:
            for ln in text[:300].splitlines():
                print(f"  {C.GREEN}{ln}{C.RST}", flush=True)
        cost = event.get("cost_usd", "")
        duration = event.get("duration_ms", "")
        if cost or duration:
            print(f"  {C.DIM}⏱ {duration}ms  💰 ${cost}{C.RST}", flush=True)

    elif event_type == "error":
        print(f"  {C.RED}✘ {event.get('error', '')}{C.RST}", flush=True)


def p_sub(text):
    print(f"  {C.DIM}{text}{C.RST}", flush=True)

def p_agent_header(name, iteration):
    tag = f" {name} "
    print(f"\n{C.CYAN}{C.BOLD}{tag}{C.RST} {C.DIM}iter #{iteration}{C.RST}", flush=True)


def run_agent(agent, iteration, run_log_dir):
    name = agent["name"]
    path = agent["path"]
    prompt_file = os.path.join(path, "PROMPT.md")
    log_file_path = os.path.join(path, "log", "raw.log")
    run_agent_log = os.path.join(run_log_dir, f"{name}.log")
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if not os.path.isfile(prompt_file):
        print(f"[{name}] 没有 PROMPT.md，跳过", flush=True)
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

        for line in proc.stdout:
            decoded = line.decode("utf-8", errors="replace")
            log_file.write(decoded)
            agent_log.write(decoded)
            log_file.flush()
            agent_log.flush()
            handle_event(name, decoded)

        stderr_output = proc.stderr.read().decode("utf-8", errors="replace")
        if stderr_output:
            print(f"[{name}] [STDERR] {stderr_output}", flush=True)
            log_file.write(stderr_output)
            agent_log.write(stderr_output)

        proc.wait()

        footer = f"\n[{ts}] --- 结束 (exit={proc.returncode}) ---\n"
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
    print(f"[{name}] 本轮{status}", flush=True)


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
        subprocess.run([git, "add", "memory/", "log/", "inbox/"], cwd=LOOPCLI_DIR, capture_output=True, timeout=30)
        subprocess.run(
            [git, "commit", "-m", f"auto: loopcli sync {datetime.now().strftime('%Y-%m-%d %H:%M')}"],
            cwd=LOOPCLI_DIR, capture_output=True, timeout=30
        )
        askpass_script = os.path.join(LOOPCLI_DIR, ".git_askpass.bat")
        with open(askpass_script, "w") as f:
            f.write("@echo %GH_TOKEN%\n")
        push_env = {
            **os.environ,
            "GH_TOKEN": token,
            "GIT_ASKPASS": askpass_script,
            "GIT_TERMINAL_PROMPT": "0",
        }
        subprocess.run(
            [git, "push", "https://x-access-token@github.com/zhoudingnuo/loopcli.git", "main"],
            cwd=LOOPCLI_DIR, capture_output=True, timeout=60, env=push_env,
        )
        os.remove(askpass_script)
        print("[git] 已同步到 GitHub", flush=True)
    except Exception as e:
        print(f"[git] 同步失败: {e}", flush=True)


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


def cmd_run(args):
    agents = discover_agents()
    if not agents:
        print("未发现任何 Agent（需要目录下有 AGENT 标记文件）")
        sys.exit(1)

    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    run_log_dir = os.path.join(LOGS_DIR, run_id)
    os.makedirs(run_log_dir, exist_ok=True)

    meta = {
        "run_id": run_id,
        "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "iterations": args.iterations or "无限",
        "agents": [a["name"] for a in agents],
    }
    write_json(os.path.join(run_log_dir, "meta.json"), meta)

    # ─── 分屏终端设置 ───
    rows, cols = shutil.get_terminal_size().lines, shutil.get_terminal_size().columns
    INPUT_ROWS = 2  # 底部输入区行数（分隔线 + 输入行）
    output_bottom = rows - INPUT_ROWS  # 输出区底部行号

    # 设置滚动区域：第1行到 output_bottom 行
    sys.stdout.write(f"\033[1;{output_bottom}r")
    sys.stdout.write(f"\033[1;1H")
    sys.stdout.flush()

    print(f"LoopCLI 启动 | {len(agents)} Agents | 运行ID: {run_id}")

    # 输入状态
    msg_queue = queue.Queue()
    stop_event = threading.Event()
    input_buffer = [""]  # 用 list 以便在闭包中修改

    def draw_input():
        """重绘底部输入区域"""
        buf = input_buffer[0][:cols - 25]
        # 分隔线（在滚动区域外）
        sys.stdout.write(f"\033[{output_bottom + 1};1H\033[K{C.CYAN}{'─' * cols}{C.RST}")
        # 输入行
        sys.stdout.write(f"\033[{output_bottom + 2};1H\033[K{C.CYAN} > {C.RST}{buf}{C.DIM}█{C.RST} {C.DIM}(Enter发送, exit退出){C.RST}")
        # 光标回到输出区底部，让 print 正常工作
        sys.stdout.write(f"\033[{output_bottom};1H")
        sys.stdout.flush()

    draw_input()

    def input_listener():
        while not stop_event.is_set():
            try:
                ch = msvcrt.getwch()
                if ch == '\r':
                    line = input_buffer[0].strip()
                    input_buffer[0] = ""
                    draw_input()
                    if line == "exit":
                        msg_queue.put("__EXIT__")
                        return
                    if line:
                        msg_queue.put(line)
                        # 在输出区显示发送确认
                        sys.stdout.write(f"\033[{output_bottom};1H")
                        print(f"  {C.GREEN}✔ 消息已发送 -> main/inbox/{C.RST}")
                        draw_input()
                elif ch == '\x03':
                    msg_queue.put("__EXIT__")
                    return
                elif ch == '\x08':
                    input_buffer[0] = input_buffer[0][:-1]
                    draw_input()
                elif len(ch) == 1 and ord(ch) >= 32:
                    input_buffer[0] += ch
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
    count = 0
    while args.iterations == 0 or count < args.iterations:
        count += 1
        agents = discover_agents()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        iter_label = f"{count}/{args.iterations}" if args.iterations else str(count)

        # 输出到滚动区域
        sys.stdout.write(f"\033[{output_bottom};1H")
        print(f"\n{C.BOLD}{C.CYAN}══ Loop {iter_label} | {len(agents)} Agents | {ts} ══{C.RST}")

        threads = []
        for agent in agents:
            sys.stdout.write(f"\033[{output_bottom};1H")
            p_agent_header(agent["name"], count)
            t = threading.Thread(target=run_agent, args=(agent, count, run_log_dir))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        git_push()

        if not process_queue():
            break

        if args.iterations == 0 or count < args.iterations:
            draw_input()
            for _ in range(args.wait):
                if not process_queue():
                    stop_event.set()
                    break
                time.sleep(1)

    # 清理：恢复滚动区域
    stop_event.set()
    sys.stdout.write(f"\033[r")  # 重置滚动区域
    sys.stdout.write(f"\033[{rows};1H")  # 光标到底部
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


def cmd_msg(args):
    agent_dir = os.path.join(LOOPCLI_DIR, args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        print(f"[错误] 不是有效的 Agent: {args.agent}")
        sys.exit(1)
    msg_file = write_inbox_message(agent_dir, "user", args.content)
    print(f"[已发送] -> {args.agent}/inbox/  {args.content}")


if sys.argv[1:] and sys.argv[1] not in ("run", "create", "task", "list", "templates", "msg", "enable", "disable", "-h", "--help"):
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
else:
    if not hasattr(args, "iterations"):
        args.iterations = 0
    if not hasattr(args, "wait"):
        args.wait = 10
    cmd_run(args)
