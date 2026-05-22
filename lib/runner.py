import json
import os
import subprocess
import threading
import time
from datetime import datetime

from .colors import C
from .terminal import out, _agent_tag
from .usage import query_model_usage, load_pricing, load_last_usage, save_last_usage, calc_cost
from loopcli_lib import read_json, write_json, LOOPCLI_ROOT

LOOPCLI_DIR = str(LOOPCLI_ROOT)
LOGS_DIR = os.path.join(LOOPCLI_DIR, "logs")


def rotate_log(log_path, max_size=1_000_000, max_backups=3):
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
    except (PermissionError, OSError):
        pass


def handle_event(agent_name, line, result_signal=None):
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
        if result_signal is not None:
            result_signal[0] = True
        text = event.get("result", "")
        if text:
            for ln in text[:300].splitlines():
                out(f"  {tag} {C.GREEN}{ln}{C.RST}")
        duration = event.get("duration_ms", "")
        if duration:
            out(f"  {tag} {C.DIM}⏱ {duration}ms{C.RST}")

    elif event_type == "error":
        out(f"  {tag} {C.RED}✘ {event.get('error', '')}{C.RST}")


def run_agent(agent, iteration, run_log_dir, claude_cmd, activity=None):
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

    proc = None
    stuck = [False]

    # 启动前立即写入 running 状态，让 web UI 能实时检测
    state_file = os.path.join(path, "memory", "state.json")
    state = _load_agent_state(path) or {}
    state["status"] = "running"
    state["current_iteration"] = iteration
    state["last_run"] = ts
    write_json(state_file, state)

    try:
        header = f"\n[{ts}] --- 开始 (第{iteration}轮) ---\n"
        log_file.write(header)
        agent_log.write(header)
        log_file.flush()
        agent_log.flush()

        env = {**os.environ, "IS_SANDBOX": "1"}

        proc = subprocess.Popen(
            [claude_cmd, "--print", "--verbose", "--output-format", "stream-json", "--dangerously-skip-permissions"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=path,
        )

        proc.stdin.write(prompt.encode("utf-8"))
        proc.stdin.close()

        last_output = [time.time()]
        got_result = [False]

        def watchdog():
            while proc.poll() is None:
                timeout = 30 if got_result[0] else 1800
                if time.time() - last_output[0] > timeout:
                    stuck[0] = True
                    label = "30秒（agent已输出结果）" if got_result[0] else "30分钟无输出"
                    out(f"  {_agent_tag(name)} {C.RED}⏰ 超时（{label}），正在终止...{C.RST}")
                    proc.kill()
                    try:
                        proc.stdout.close()
                    except Exception:
                        pass
                    return
                time.sleep(5 if got_result[0] else 10)

        def _touch():
            last_output[0] = time.time()
            if activity is not None:
                activity[name] = last_output[0]

        def drain_stdout():
            for line in iter(proc.stdout.readline, b''):
                _touch()
                decoded = line.decode("utf-8", errors="replace")
                log_file.write(decoded)
                agent_log.write(decoded)
                log_file.flush()
                agent_log.flush()
                handle_event(name, decoded, got_result)

        reader = threading.Thread(target=drain_stdout, daemon=True)
        reader.start()

        wd = threading.Thread(target=watchdog, daemon=True)
        wd.start()

        stderr_chunks = []
        def drain_stderr():
            for line in proc.stderr:
                _touch()
                stderr_chunks.append(line.decode("utf-8", errors="replace"))

        stderr_thread = threading.Thread(target=drain_stderr, daemon=True)
        stderr_thread.start()

        proc.wait()

        try:
            proc.stdout.close()
        except Exception:
            pass
        try:
            proc.stderr.close()
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
            footer = f"\n[{ts}] --- 超时终止 (killed, 5min no output) ---\n"
            log_file.write(footer)
            agent_log.write(footer)
            err_file = os.path.join(path, "memory", "errors.json")
            errs = read_json(err_file, [])
            errs.append({"time": ts, "agent": name, "error": "timeout", "detail": "5分钟无输出，进程被看门狗终止"})
            write_json(err_file, errs)
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

    state_file = os.path.join(path, "memory", "state.json")
    state = _load_agent_state(path) or {}
    state["status"] = "idle"
    state["last_run"] = ts
    state["run_count"] = state.get("run_count", 0) + 1
    write_json(state_file, state)

    rc = proc.returncode if proc else -1
    status = "完成" if rc == 0 else f"异常(exit={rc})"
    color = C.GREEN if "完成" in status else C.RED
    sym = "✔" if "完成" in status else "✘"
    out(f"  {color}{sym} {name} {status}{C.RST}")

    current = query_model_usage(out)
    pricing = load_pricing()
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
                out(f"    {C.DIM}{model}: +{tokens:,} tokens → ${cost:.4f}{C.RST}")
            out(f"  {C.GREEN}{C.BOLD}💰 本轮花费: ${total_cost:.4f}{C.RST}")
        else:
            out(f"  {C.DIM}💰 本轮无新增消耗{C.RST}")
        save_last_usage(current)
    elif current is None:
        out(f"  {C.YELLOW}⚠ 花费查询失败，运行: python D:/loopcli/scripts/usage.py{C.RST}")


def _load_agent_state(agent_path):
    state_file = os.path.join(agent_path, "memory", "state.json")
    if os.path.isfile(state_file):
        return read_json(state_file)
    return None
