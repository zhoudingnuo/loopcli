import os
import sys
from datetime import datetime

from .colors import C
from .terminal import out
from loopcli_lib import (
    LOOPCLI_ROOT,
    AGENT_MARKER,
    read_json,
    write_json,
    create_task,
    write_inbox_message,
    set_agent_enabled,
    is_agent_enabled,
    discover_agents as _discover_agents,
)

LOOPCLI_DIR = str(LOOPCLI_ROOT)
SUBAGENT_DIR = os.path.join(LOOPCLI_DIR, "agent template")


def discover_agents(include_disabled=False):
    return _discover_agents(include_disabled=include_disabled)


def find_template(template_id):
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


def cmd_create(args, default_prompt):
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
        f.write(default_prompt)

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


def cmd_task_inner(agent_name, title, desc):
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


def cmd_enable(args):
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
    agent_dir = os.path.join(LOOPCLI_DIR, "agents", args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        agent_dir = os.path.join(LOOPCLI_DIR, args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        print(f"[错误] 不是有效的 Agent: {args.agent}")
        sys.exit(1)
    set_agent_enabled(agent_dir, False)
    print(f"[已禁用] {args.agent}（loopcli run 将跳过此 Agent）")


def cmd_msg(args):
    agent_dir = os.path.join(LOOPCLI_DIR, "agents", args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        agent_dir = os.path.join(LOOPCLI_DIR, args.agent)
    if not os.path.isfile(os.path.join(agent_dir, AGENT_MARKER)):
        print(f"[错误] 不是有效的 Agent: {args.agent}")
        sys.exit(1)
    msg_file = write_inbox_message(agent_dir, "user", args.content)
    print(f"[已发送] -> {args.agent}/inbox/  {args.content}")


def cmd_weixin(args, wechat_available, default_base_url):
    if not wechat_available:
        print("[错误] wechat_bridge 模块未找到")
        sys.exit(1)

    from wechat_bridge import weixin_qr_login, weixin_verify_token

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
        if weixin_verify_token(default_base_url, args.token):
            cfg = {"token": args.token}
            write_json(config_file, cfg)
            print(f"[微信] Token 已保存，运行 loopcli run 启动")
        else:
            print("[微信] Token 验证失败，请检查是否正确")
        return

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
