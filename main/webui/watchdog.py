"""WebUI Process Watchdog — auto-restart on crash, designed for Windows Task Scheduler."""
import subprocess
import sys
import time
import os

SERVER_SCRIPT = os.path.join(os.path.dirname(__file__), "server.py")
PYTHON = sys.executable
RESTART_DELAY = 5  # seconds between restart attempts


def main():
    print(f"[watchdog] Starting WebUI watchdog (python={PYTHON})")
    while True:
        print(f"[watchdog] Launching server.py ...")
        try:
            proc = subprocess.run(
                [PYTHON, SERVER_SCRIPT],
                cwd=os.path.dirname(__file__),
            )
            print(f"[watchdog] server.py exited with code {proc.returncode}")
        except Exception as e:
            print(f"[watchdog] Exception: {e}")

        print(f"[watchdog] Restarting in {RESTART_DELAY}s ...")
        time.sleep(RESTART_DELAY)


if __name__ == "__main__":
    main()
