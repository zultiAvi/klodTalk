@echo off
rem Run the klodTalk WebSocket server using the project's venv.
rem Usage: helpers\windows\run_server.bat

setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%..\.."
set "VENV_PYTHON=%PROJECT_ROOT%\.venv\Scripts\python.exe"
set "SERVER=%PROJECT_ROOT%\server\server.py"

if not exist "%VENV_PYTHON%" (
    echo ERROR: Virtual environment not found at %PROJECT_ROOT%\.venv
    echo Create it with:  python -m venv .venv ^&^& .venv\Scripts\pip install -r server\requirements.txt
    exit /b 1
)

"%VENV_PYTHON%" "%SERVER%" %*
