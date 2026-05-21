@echo off
chcp 65001 >nul 2>&1
title LoopCLI - Multi-Agent System

echo ╔══════════════════════════════════════════════╗
echo ║         LoopCLI Multi-Agent System           ║
echo ╚══════════════════════════════════════════════╝
echo.

:: Check Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: Check Claude CLI
where claude >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARN] Claude CLI not found. Agent execution will not work.
    echo        Install from https://claude.ai/code
    echo.
)

:: Set working directory
set "LOOPCLI_ROOT=D:\loopcli"

echo [1/3] Starting WebUI Server on http://127.0.0.1:8080 ...
start "LoopCLI WebUI" /min cmd /c "python %LOOPCLI_ROOT%\main\webui\server.py"
timeout /t 2 /nobreak >nul

echo [2/3] Starting Watchdog Process ...
start "LoopCLI Watchdog" /min cmd /c "python %LOOPCLI_ROOT%\main\webui\watchdog.py"

echo [3/3] Opening WebUI in browser ...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:8080

echo.
echo ════════════════════════════════════════════════
echo  WebUI:        http://127.0.0.1:8080
echo  API Docs:     See README.md - API Endpoints
echo  Config:       See docs/CONFIGURATION.md
echo ════════════════════════════════════════════════
echo.
echo  Press any key to open CLI mode (run.py),
echo  or close this window to keep WebUI running.
echo.
pause

echo.
echo Starting Agent Loop (CLI mode) ...
python %LOOPCLI_ROOT%\run.py run
