import os
import subprocess
from datetime import datetime

from .colors import C
from .terminal import out
from loopcli_lib import LOOPCLI_ROOT

LOOPCLI_DIR = str(LOOPCLI_ROOT)
GIT_TOKEN_FILE = os.path.join(LOOPCLI_DIR, ".gittoken")


def resolve_git():
    for p in os.environ.get("PATH", "").split(";"):
        candidate = os.path.join(p, "git.exe")
        if os.path.isfile(candidate):
            return candidate
    for d in [r"C:\Program Files\Git\cmd", r"C:\Program Files\Git\bin"]:
        candidate = os.path.join(d, "git.exe")
        if os.path.isfile(candidate):
            return candidate
    return "git"


def git_push():
    if not os.path.isfile(GIT_TOKEN_FILE):
        return
    with open(GIT_TOKEN_FILE, "r") as f:
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
