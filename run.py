import argparse
import json
import msvcrt
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, r"D:\loopcli\main\webui")
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
读取 D:/loopcli/skill/ 下所有技能文件（全局技能）。
读取 memory/tasks.json 获取分配给你的任务。

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

def handle_event(agent_name, line):
    line = line.strip()
    if not line:
        return
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        print(f"[{agent_name}] {line}", flush=True)
        return

    event_type = event.get("type", "")

    if event_type == "assistant":
        msg = event.get("message", {})
        for block in msg.get("content", []):
            if block.get("type") == "text":
                text = block.get("text", "")
                if text:
                    print(f"[{agent_name}] {text}", flush=True)
            elif block.get("type") == "tool_use":
                name = block.get("name", "")
                inp = block.get("input", {})
                detail = ""
                for k in ("file_path", "command", "pattern"):
                    if k in inp:
                        detail = inp[k]
                        break
                print(f"[{agent_name}] ● {name}({detail})", flush=True)

    elif event_type == "tool_result":
        content = event.get("content", "")
        texts = []
        if isinstance(content, list):
            texts = [b.get("text", "") for b in content if b.get("text")]
        elif isinstance(content, str):
            texts = [content]
        for text in texts:
            print(f"[{agent_name}]   ↳ {text[:200]}", flush=True)

    elif event_type == "result":
        text = event.get("result", "")
        if text:
            print(f"[{agent_name}] [结果] {text[:500]}", flush=True)
        cost = event.get("cost_usd", "")
        duration = event.get("duration_ms", "")
        if cost or duration:
            print(f"[{agent_name}] [统计] 耗时: {duration}ms, 费用: ${cost}", flush=True)

    elif event_type == "error":
        print(f"[{agent_name}] [错误] {event.get('error', '')}", flush=True)


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

    # 更新 state.json (with file lock)
    state_file = os.path.join(path, "memory", "state.json")
    with open(state_file, "a+") as f:
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
        try:
            f.seek(0)
            try:
                state = json.load(f)
            except (json.JSONDecodeError, ValueError):
                state = {}
            state["status"] = "idle"
            state["last_run"] = ts
            state["run_count"] = state.get("run_count", 0) + 1
            f.seek(0)
            f.truncate()
            json.dump(state, f, indent=2, ensure_ascii=False)
        finally:
            msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

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

    print(f"运行 ID: {run_id}")
    print(f"日志目录: {run_log_dir}")
    print(f"发现 {len(agents)} 个 Agent: {', '.join(a['name'] for a in agents)}")

    count = 0
    while args.iterations == 0 or count < args.iterations:
        count += 1
        agents = discover_agents()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n{'='*60}")
        print(f"[{ts}] 第 {count}{'/' + str(args.iterations) if args.iterations else ''} 轮 | {len(agents)} 个 Agent")
        print(f"{'='*60}")

        threads = []
        for agent in agents:
            print(f"\n--- 启动 [{agent['name']}] ---", flush=True)
            t = threading.Thread(target=run_agent, args=(agent, count, run_log_dir))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        git_push()

        if args.iterations == 0 or count < args.iterations:
            print(f"\n{'─'*60}", flush=True)
            print(f"输入消息发给 main（直接回车跳过，输入 exit 停止）:", flush=True)
            try:
                user_input = input(f"  > ").strip()
                if user_input.lower() == "exit":
                    print("用户终止运行")
                    break
                if user_input:
                    msg_file = write_inbox_message(
                        os.path.join(LOOPCLI_DIR, "main"),
                        "user",
                        user_input,
                    )
                    print(f"  [已发送] -> main/inbox/", flush=True)
            except EOFError:
                pass
            print(f"  等待 {args.wait} 秒后进入下一轮...", flush=True)
            time.sleep(args.wait)
    meta["finished"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    meta["total_iterations"] = count
    write_json(os.path.join(run_log_dir, "meta.json"), meta)

    print(f"\n运行结束，日志保存在: {run_log_dir}")


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
