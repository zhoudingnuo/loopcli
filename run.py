import argparse
import json
import msvcrt
import os
import queue
import shutil
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "main" / "webui"))

from loopcli_lib import read_json, write_json, LOOPCLI_ROOT, is_agent_enabled

# Fix Windows GBK encoding
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

LOOPCLI_DIR = str(LOOPCLI_ROOT)
CLAUDE = os.path.join(os.environ.get("APPDATA", ""), "npm", "claude.cmd")

try:
    from wechat_bridge import create_wechat_bridge
    WECHAT_AVAILABLE = True
except ImportError:
    WECHAT_AVAILABLE = False

from lib.colors import C
from lib.terminal import out, draw_input, p_agent_header, _ob, _buf
from lib.runner import run_agent
from lib.usage import load_pricing, query_model_usage, load_last_usage, save_last_usage, calc_cost
from lib.git_sync import git_push
from lib.cli import (
    discover_agents, cmd_create, cmd_task, cmd_list, cmd_templates,
    cmd_enable, cmd_disable, cmd_msg, cmd_weixin, load_agent_tasks,
)

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


def cmd_run(args):
    agents = discover_agents()
    if not agents:
        print("未发现任何 Agent（需要目录下有 AGENT 标记文件）")
        sys.exit(1)

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
    run_log_dir = os.path.join(LOOPCLI_DIR, "logs", run_id)
    os.makedirs(run_log_dir, exist_ok=True)

    meta = {
        "run_id": run_id,
        "started": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "iterations": args.iterations or "无限",
        "agents": [a["name"] for a in agents],
        "wechat": wechat_handler is not None,
    }
    write_json(os.path.join(run_log_dir, "meta.json"), meta)

    rows, cols = shutil.get_terminal_size().lines, shutil.get_terminal_size().columns
    _ob[0] = rows - 2

    sys.stdout.write("\033[?25l")
    sys.stdout.write(f"\033[1;{_ob[0]}r")
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

    pricing = load_pricing()
    count = 0
    while args.iterations == 0 or count < args.iterations:
        # 北京时间 14:00-18:00 高峰期暂停
        bj_hour = (datetime.utcnow().hour + 8) % 24
        if 14 <= bj_hour < 18:
            out(f"{C.YELLOW}⏸ 北京时间 {bj_hour}:00，高峰期暂停迭代（14:00-18:00）{C.RST}")
            if not process_queue():
                break
            time.sleep(300)
            continue

        count += 1
        agents = discover_agents()
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        iter_label = f"{count}/{args.iterations}" if args.iterations else str(count)

        out(f"{C.BOLD}{C.CYAN}══ Loop {iter_label} | {len(agents)} Agents | {ts} ══{C.RST}")

        threads = {}  # {thread: agent_name}
        activity = {}
        for agent in agents:
            p_agent_header(agent["name"], count)
            t = threading.Thread(target=run_agent, args=(agent, count, run_log_dir, CLAUDE, activity))
            t.start()
            threads[t] = agent["name"]

        # 持续监控：等待完成 + 实时激活新被指派的 agent
        while threads:
            # 清理已完成的线程
            finished = [t for t in threads if not t.is_alive()]
            for t in finished:
                del threads[t]

            # 检查超时
            for t, aname in list(threads.items()):
                if not t.is_alive():
                    continue
                last_active = activity.get(aname, 0)
                if last_active > 0 and time.time() - last_active > 600:
                    out(f"  {C.RED}⚠ {aname} 10分钟无输出，跳过等待{C.RST}")
                    del threads[t]

            # 实时激活：检查不在运行中的 agent 是否有新 pending 任务
            running_names = set(threads.values())
            for a in discover_agents():
                if a["name"] in running_names:
                    continue
                tasks = load_agent_tasks(a["path"])
                if any(t.get("status") == "pending" for t in tasks):
                    p_agent_header(a["name"], count)
                    nt = threading.Thread(target=run_agent, args=(a, count, run_log_dir, CLAUDE, activity))
                    nt.start()
                    threads[nt] = a["name"]
                    out(f"  {C.CYAN}⚡ {a['name']} 被实时激活{C.RST}")

            if threads:
                time.sleep(1)

        git_push()

        current = query_model_usage(out)
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
            # 有 longtask 时用默认间隔，无任务时隔 15 分钟
            lt_path = os.path.join(LOOPCLI_DIR, "longtask.md")
            has_longtask = os.path.isfile(lt_path) and os.path.getsize(lt_path) > 10
            wait_secs = args.wait if has_longtask else 900
            if not has_longtask:
                out(f"  {C.DIM}无长期任务，15 分钟后开始下一轮{C.RST}")
            draw_input()
            for _ in range(wait_secs):
                if not process_queue():
                    stop_event.set()
                    break
                time.sleep(1)

    stop_event.set()
    if wechat_handler:
        wechat_handler.bridge.stop()
    sys.stdout.write("\033[?25h")
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
p_create.add_argument("template", help="模板 ID")
p_create.add_argument("--task", "-t", help="初始任务描述")

p_task = sub.add_parser("task", help="给 Agent 派发任务")
p_task.add_argument("agent", help="Agent 目录名")
p_task.add_argument("title", help="任务标题")
p_task.add_argument("--desc", "-d", default="", help="任务描述")

sub.add_parser("list", help="列出所有 Agent 及状态")

p_tpl = sub.add_parser("templates", help="列出可用模板")
p_tpl.add_argument("--filter", "-f", default="", help="按关键词筛选")

p_msg = sub.add_parser("msg", help="给 Agent 发消息")
p_msg.add_argument("content", help="消息内容")
p_msg.add_argument("--agent", "-a", default="main", help="目标 Agent（默认 main）")

p_enable = sub.add_parser("enable", help="启用 Agent")
p_enable.add_argument("agent", help="Agent 目录名")

p_disable = sub.add_parser("disable", help="禁用 Agent")
p_disable.add_argument("agent", help="Agent 目录名")

p_weixin = sub.add_parser("weixin", help="微信扫码登录/配置")
p_weixin.add_argument("action", nargs="?", default="setup", choices=["setup", "show", "bind"])
p_weixin.add_argument("--token", default="", help="ilink bot token（bind 模式使用）")

if sys.argv[1:] and sys.argv[1] not in ("run", "create", "task", "list", "templates", "msg", "enable", "disable", "weixin", "-h", "--help"):
    sys.argv.insert(1, "run")

args = parser.parse_args()

if args.command == "create":
    cmd_create(args, DEFAULT_PROMPT)
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
    cmd_weixin(args, WECHAT_AVAILABLE, "https://ilinkai.weixin.qq.com")
else:
    if not hasattr(args, "iterations"):
        args.iterations = 0
    if not hasattr(args, "wait"):
        args.wait = 10
    cmd_run(args)
