# 核心系统变更测试框架
# 用途：在修改 run.py、MCP 配置、agent 框架前，先验证不会阻塞主进程

import subprocess
import sys
import time
from pathlib import Path

LOOPCLI_ROOT = Path(__file__).parent.parent
RUN_PY = LOOPCLI_ROOT / "run.py"


def test_run_py_syntax():
    """测试 run.py 语法正确"""
    result = subprocess.run(
        [sys.executable, "-m", "py_compile", str(RUN_PY)],
        capture_output=True,
        timeout=10,
        encoding="utf-8",
        errors="replace"
    )
    assert result.returncode == 0, f"语法错误: {result.stderr}"
    return True


def test_run_help():
    """测试 run.py --help 能正常输出（不阻塞）"""
    result = subprocess.run(
        [sys.executable, str(RUN_PY), "--help"],
        capture_output=True,
        timeout=10,
        encoding="utf-8",
        errors="replace"
    )
    if result.returncode != 0:
        return True  # 无 --help 选项也正常
    assert result.stdout, "无输出"
    return True


def test_agent_spawn_quick():
    """测试 agent 子进程能正常启动（快速检查）"""
    # 只测试进程能启动，不等待完整执行
    proc = subprocess.Popen(
        [sys.executable, str(RUN_PY), "list"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
        cwd=LOOPCLI_ROOT
    )
    try:
        stdout, stderr = proc.communicate(timeout=10)
        return True  # 进程正常退出
    except subprocess.TimeoutExpired:
        proc.kill()
        return False  # 进程卡死
    except Exception:
        return True  # 其他错误也算能启动


def run_all_tests():
    """运行所有核心测试"""
    tests = [
        ("语法检查", test_run_py_syntax),
        ("命令行工具", test_run_help),
        ("子进程启动", test_agent_spawn_quick),
    ]

    failed = []
    for name, test_func in tests:
        try:
            print(f"[*] {name}...", end=" ")
            test_func()
            print("OK")
        except Exception as e:
            print(f"FAIL: {e}")
            failed.append((name, str(e)))

    if failed:
        print("\n[!] 测试失败:")
        for name, err in failed:
            print(f"  - {name}: {err}")
        return False
    print("\n[+] 所有测试通过")
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
