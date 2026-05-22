import shutil
import sys
import threading

from .colors import C

_ob = [0]
_buf = [""]
_lock = threading.Lock()


def out(text=""):
    with _lock:
        sys.stdout.write("\033[s")
        sys.stdout.write(f"\033[{_ob[0]};1H")
        sys.stdout.write(text + "\n")
        sys.stdout.write("\033[u")
        sys.stdout.flush()


def draw_input():
    with _lock:
        cols = shutil.get_terminal_size().columns
        ob = _ob[0]
        buf = _buf[0][:cols - 25]
        sys.stdout.write(f"\033[{ob+1};1H\033[K{C.CYAN}{'─'*cols}{C.RST}")
        sys.stdout.write(f"\033[{ob+2};1H\033[K{C.CYAN} > {C.RST}{buf}{C.DIM}█{C.RST} {C.DIM}(Enter发送, exit退出){C.RST}")
        sys.stdout.write(f"\033[{ob+2};{4 + len(buf)}H")
        sys.stdout.flush()


def p_sub(text):
    out(f"  {C.DIM}{text}{C.RST}")


def p_agent_header(name, iteration):
    out(f"\n{C.CYAN}{C.BOLD} {name} {C.RST} {C.DIM}iter #{iteration}{C.RST}")


_AGENT_COLORS = [
    "\033[36m",
    "\033[33m",
    "\033[32m",
    "\033[35m",
    "\033[34m",
    "\033[31m",
]
_agent_color_map = {}


def _agent_tag(name):
    if name not in _agent_color_map:
        _agent_color_map[name] = _AGENT_COLORS[len(_agent_color_map) % len(_AGENT_COLORS)]
    c = _agent_color_map[name]
    short = name[:16]
    return f"{c}[{short}]{C.RST}"
