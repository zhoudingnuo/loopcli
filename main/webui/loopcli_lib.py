"""
LoopCLI shared library — common functions used by server.py and run.py.
"""

import json
import os
import tempfile
import threading
from pathlib import Path


def _resolve_root():
    """Resolve LOOPCLI_ROOT: env var > auto-detect from file location."""
    env = os.environ.get("LOOPCLI_ROOT", "").strip()
    if env:
        return Path(env).resolve()
    # loopcli_lib.py lives at LOOPCLI_ROOT/main/webui/loopcli_lib.py
    return Path(__file__).resolve().parent.parent.parent


LOOPCLI_ROOT = _resolve_root()
AGENT_MARKER = "AGENT"

_json_lock = threading.Lock()


# ─── JSON I/O ───

def read_json(path, default=None):
    """Read and parse a JSON file, returning default on failure."""
    path = Path(path)
    if not path.exists():
        return default if default is not None else {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default if default is not None else {}


def write_json(path, data):
    """Atomically write data as JSON using tempfile + os.replace.

    Writes to a temporary file first, then atomically replaces the target.
    This ensures no partial/corrupt files if the process crashes mid-write.
    """
    import time as _time
    path = Path(path)
    with _json_lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(data, ensure_ascii=False, indent=2)
        fd, tmp_path = tempfile.mkstemp(
            suffix=".tmp",
            prefix=".loopcli_",
            dir=str(path.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())
            # On Windows, os.replace can fail if another thread is reading the file.
            # Retry a few times with a short delay.
            for attempt in range(5):
                try:
                    os.replace(tmp_path, str(path))
                    break
                except PermissionError:
                    if attempt == 4:
                        raise
                    _time.sleep(0.05)
        except BaseException:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise


# ─── Agent path safety ───

def safe_agent_path(agent_id: str) -> Path | None:
    """Validate and resolve an agent directory path, preventing traversal attacks."""
    if not agent_id or '/' in agent_id or '\\' in agent_id or '..' in agent_id or '\x00' in agent_id:
        return None
    agent_dir = LOOPCLI_ROOT / agent_id
    try:
        agent_dir.resolve().relative_to(LOOPCLI_ROOT.resolve())
    except ValueError:
        return None
    return agent_dir


# ─── Agent discovery ───

def get_agent_marker(agent_dir) -> str | None:
    """Read AGENT marker file content, or None if missing."""
    marker = Path(agent_dir) / AGENT_MARKER
    if marker.is_file():
        return marker.read_text(encoding="utf-8").strip()
    return None


def is_agent_enabled(agent_dir) -> bool:
    """Check if an agent directory has a valid, non-disabled AGENT marker."""
    content = get_agent_marker(agent_dir)
    if content is None:
        return False
    return "disabled" not in content


def discover_agents(include_disabled=False):
    """Discover agent directories under LOOPCLI_ROOT.

    Returns list of {"name": str, "path": str}.
    """
    agents = []
    for child in LOOPCLI_ROOT.iterdir():
        if not child.is_dir():
            continue
        if not (child / AGENT_MARKER).exists():
            continue
        if include_disabled or is_agent_enabled(child):
            agents.append({"name": child.name, "path": str(child)})
    return agents


def scan_agents():
    """Full agent scan with metadata (state, soul, task counts)."""
    agents = []
    for child in LOOPCLI_ROOT.iterdir():
        if not child.is_dir():
            continue
        if not (child / AGENT_MARKER).exists():
            continue
        state = read_json(child / "memory" / "state.json", {})
        soul_path = child / "SOUL.md"
        desc = ""
        if soul_path.exists():
            for line in soul_path.read_text(encoding="utf-8").strip().splitlines():
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    desc = stripped
                    break
        tasks = read_json(child / "memory" / "tasks.json", [])
        done_count = sum(1 for t in tasks if t.get("status") == "done")
        pending_count = sum(1 for t in tasks if t.get("status") == "pending")
        enabled = is_agent_enabled(child)
        agents.append({
            "id": child.name,
            "name": state.get("agent", child.name),
            "status": "disabled" if not enabled else state.get("status", "unknown"),
            "description": desc,
            "last_run": state.get("last_run"),
            "run_count": state.get("run_count", 0),
            "current_task": state.get("current_task"),
            "task_count": len(tasks),
            "task_done": done_count,
            "task_pending": pending_count,
        })
    return agents


# ─── Task management ───

def next_task_id(tasks):
    """Get the next auto-increment task ID from a task list."""
    return max((t.get("id", 0) for t in tasks), default=0) + 1


def create_task(agent_dir, title, description="", assignee=None, created=None):
    """Create a new task in an agent's tasks.json and return the task dict."""
    from datetime import datetime, timezone
    agent_dir = Path(agent_dir)
    tasks_file = agent_dir / "memory" / "tasks.json"
    tasks = read_json(tasks_file, [])
    new_id = next_task_id(tasks)
    task = {
        "id": new_id,
        "status": "pending",
        "title": title,
        "description": description,
        "created": created or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "assignee": assignee or agent_dir.name,
    }
    tasks.append(task)
    write_json(tasks_file, tasks)
    return task


def get_agent_tasks(agent_id):
    """Get tasks for a specific agent by ID. Returns None if agent_id is invalid."""
    agent_dir = safe_agent_path(agent_id)
    if not agent_dir:
        return None
    return read_json(agent_dir / "memory" / "tasks.json", [])


def get_all_agent_tasks():
    """Aggregate tasks from all agents, each tagged with _agent_id."""
    all_tasks = []
    for child in LOOPCLI_ROOT.iterdir():
        if not child.is_dir() or not (child / AGENT_MARKER).exists():
            continue
        tasks = read_json(child / "memory" / "tasks.json", [])
        for t in tasks:
            t["_agent_id"] = child.name
        all_tasks.extend(tasks)
    return all_tasks


# ─── Message / inbox ───

def write_inbox_message(agent_dir, sender, content, msg_type="指令"):
    """Write a message to an agent's inbox directory. Returns the message file path."""
    import uuid
    from datetime import datetime
    agent_dir = Path(agent_dir)
    inbox_dir = agent_dir / "inbox"
    inbox_dir.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    ts = now.strftime("%Y%m%d_%H%M")
    msg_file = inbox_dir / f"{sender}_{ts}_{uuid.uuid4().hex[:8]}.md"
    msg_file.write_text(
        f"# 来自 {sender} 的消息\n- 类型：{msg_type}\n- 时间：{now.strftime('%Y-%m-%d %H:%M')}\n\n## 内容\n{content}\n",
        encoding="utf-8",
    )
    return msg_file


# ─── Agent enable/disable ───

def set_agent_enabled(agent_dir, enabled=True):
    """Enable or disable an agent by writing its AGENT marker."""
    agent_dir = Path(agent_dir)
    marker = agent_dir / AGENT_MARKER
    if enabled:
        marker.write_text("type: main\n", encoding="utf-8")
    else:
        marker.write_text("type: main\ndisabled: true\n", encoding="utf-8")


# ─── File utilities ───

def get_recent_lines(filepath, n=100):
    """Read the last N lines from a text file."""
    filepath = Path(filepath)
    if not filepath.exists():
        return []
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return [l.rstrip("\n\r") for l in lines[-n:]]
    except OSError:
        return []


def read_file_tail_incremental(filepath, last_pos=0):
    """Read only new content appended since last_pos.

    Returns (new_lines, new_pos). Efficient for SSE/polling scenarios.
    """
    filepath = Path(filepath)
    if not filepath.exists():
        return [], 0
    try:
        size = filepath.stat().st_size
        if size < last_pos:
            # File was truncated/rotated — read from start
            last_pos = 0
        if size == last_pos:
            return [], last_pos
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            f.seek(last_pos)
            new_content = f.read()
            new_pos = f.tell()
        lines = [l.rstrip("\n\r") for l in new_content.splitlines()]
        return lines, new_pos
    except OSError:
        return [], last_pos
