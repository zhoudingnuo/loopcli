Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d D:\loopcli\main && python run_watchdog.py >> D:\loopcli\logs\run-watchdog.log 2>&1", 0, False
