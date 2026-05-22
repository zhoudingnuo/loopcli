"""Run.py Watchdog — auto-restart on crash or timeout, designed for Windows Task Scheduler."""
import subprocess
import sys
import time
import os

RUN_SCRIPT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "run.py")
PYTHON = sys.executable
RESTART_DELAY = 10  # seconds between restart attempts
MAX_RESTARTS = 1000  # safety limit


def main():
    print(f"[run-watchdog] Starting run.py watchdog (python={PYTHON})")
    restart_count = 0

    while restart_count < MAX_RESTARTS:
        print(f"[run-watchdog] Launching run.py (restart #{restart_count}) ...")
        try:
            proc = subprocess.run(
                [PYTHON, RUN_SCRIPT, "run"],
                cwd=os.path.dirname(os.path.dirname(__file__)),
            )
            print(f"[run-watchdog] run.py exited with code {proc.returncode}")
        except Exception as e:
            print(f"[run-watchdog] Exception: {e}")

        restart_count += 1
        print(f"[run-watchdog] Restarting in {RESTART_DELAY}s ... (attempt {restart_count}/{MAX_RESTARTS})")
        time.sleep(RESTART_DELAY)

    print(f"[run-watchdog] Reached max restarts ({MAX_RESTARTS}), stopping.")


if __name__ == "__main__":
    main()
