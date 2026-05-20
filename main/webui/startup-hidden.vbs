Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c cd /d D:\loopcli\main\webui && python watchdog.py >> D:\loopcli\logs\webui-watchdog.log 2>&1", 0, False
