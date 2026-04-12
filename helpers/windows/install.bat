@echo off
setlocal enabledelayedexpansion

rem ── KlodTalk Installer — Windows ──────────────────────────────────────────

rem Resolve project root (two levels up from this script)
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\..\.."
set "PROJECT_ROOT=%CD%"
popd
cd /d "%PROJECT_ROOT%"

echo.
echo ========================================
echo   KlodTalk Installer — Windows
echo ========================================
echo.

rem ── 1. Docker ─────────────────────────────────────────────────────────────

echo -- Checking Docker --
docker info >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [OK]    Docker is installed and running
    goto :check_python
)

rem Docker daemon not responding — check if Docker CLI is present (installed but not running)
docker --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo [WARN]  Docker is installed but not running.
    echo         Attempting to start Docker Desktop...
    powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1" -Action start-docker
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Could not start Docker Desktop automatically.
        echo         Please open Docker Desktop manually, wait for it to finish starting, then re-run this script.
        exit /b 1
    )
    goto :check_python
)

echo [WARN]  Docker not found — attempting to install Docker Desktop via PowerShell helper...

powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1" -Action install-docker
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker Desktop installation failed.
    exit /b 1
)

echo.
echo [WARN]  Docker Desktop has been installed.
echo         Please RESTART your computer, then re-run this script.
echo.
exit /b 0

rem ── 2. Python ─────────────────────────────────────────────────────────────

:check_python
echo.
echo -- Checking Python --

set "PYTHON="
python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON=python"
    goto :found_python
)
python3 --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON=python3"
    goto :found_python
)

echo [WARN]  Python not found — attempting install via PowerShell helper...

powershell -ExecutionPolicy Bypass -File "%SCRIPT_DIR%install.ps1" -Action install-python
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python installation failed.
    exit /b 1
)
echo [WARN]  Python installed. You may need to restart your terminal.
echo         Re-run this script after restarting.
exit /b 0

:found_python
for /f "tokens=*" %%V in ('%PYTHON% -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"') do set "PY_VERSION=%%V"
echo [OK]    Python %PY_VERSION% (%PYTHON%)

rem Check version >= 3.9
for /f %%M in ('%PYTHON% -c "import sys; print(sys.version_info.major)"') do set "PY_MAJOR=%%M"
for /f %%N in ('%PYTHON% -c "import sys; print(sys.version_info.minor)"') do set "PY_MINOR=%%N"

if %PY_MAJOR% lss 3 (
    echo [ERROR] Python 3.9+ required ^(found %PY_VERSION%^)
    exit /b 1
)
if %PY_MAJOR% equ 3 if %PY_MINOR% lss 9 (
    echo [ERROR] Python 3.9+ required ^(found %PY_VERSION%^)
    exit /b 1
)

rem ── 3. Python venv ────────────────────────────────────────────────────────

echo.
echo -- Setting up Python virtual environment --

if exist .venv\ (
    echo [OK]    .venv already exists — skipping creation
) else (
    %PYTHON% -m venv .venv
    echo [OK]    Created .venv
)

.venv\Scripts\pip install -q -r server\requirements.txt
echo [OK]    Dependencies installed

rem ── 4. Example configs ────────────────────────────────────────────────────

echo.
echo -- Copying example configs --

if exist config\users.json (
    echo [OK]    config\users.json already exists — skipping
) else (
    copy config\users.json.example config\users.json >nul
    echo [OK]    Created config\users.json from example
)

if exist config\projects.json (
    echo [OK]    config\projects.json already exists — skipping
) else (
    copy config\projects.json.example config\projects.json >nul
    echo [OK]    Created config\projects.json from example
)

rem ── 5. Build Docker image ─────────────────────────────────────────────────

echo.
echo -- Building Docker image --

call helpers\windows\docker_build.bat
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Docker image build failed
    exit /b 1
)
echo [OK]    Docker image 'klodtalk-agent' built successfully

rem ── 6. Next steps ─────────────────────────────────────────────────────────

echo.
echo ========================================
echo   Installation complete!
echo ========================================
echo.
echo   Next steps:
echo.
echo   1. Add a user:
echo      python helpers\add_user.py add ^<name^>
echo.
echo   2. Add a project:
echo      python helpers\add_project.py add ^<name^> --users ^<user^> --description "..." --folder ^<path^>
echo.
echo   3. Generate TLS certificate:
echo      helpers\windows\generate_cert.bat
echo.
echo   4. Run the server:
echo      helpers\windows\run_server.bat
echo.

endlocal
