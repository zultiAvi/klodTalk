# KlodTalk Installer — PowerShell Helper
# Called by install.bat for operations that work better in PowerShell.
# Usage: powershell -ExecutionPolicy Bypass -File install.ps1 -Action <install-docker|install-python>

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("install-docker", "install-python", "start-docker")]
    [string]$Action
)

$ErrorActionPreference = "Stop"

function Find-Winget {
    # Try plain name first (interactive sessions / PATH already set)
    try {
        $cmd = Get-Command winget -ErrorAction Stop
        return $cmd.Source
    } catch {}
    # App execution aliases are not in PATH for non-interactive PowerShell processes.
    # Fall back to the well-known WindowsApps location.
    $alias = "$env:LOCALAPPDATA\Microsoft\WindowsApps\winget.exe"
    if (Test-Path $alias) { return $alias }
    return $null
}

switch ($Action) {
    "install-docker" {
        $winget = Find-Winget
        if (-not $winget) {
            Write-Host "[ERROR] winget is not available." -ForegroundColor Red
            Write-Host "        Please install Docker Desktop manually:" -ForegroundColor Red
            Write-Host "        https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
            exit 1
        }
        Write-Host "Installing Docker Desktop via winget..." -ForegroundColor Yellow
        & $winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
        # winget exits non-zero for "no upgrade available" (already installed) — treat that as success.
        # Only fail on codes that indicate a genuine installation error.
        # 0x8A150101 (-1978335999) = APPINSTALLER_CLI_ERROR_UPDATE_NOT_APPLICABLE (already up to date)
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335999) {
            # Check if docker is now reachable regardless (install may have succeeded despite odd exit code)
            $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
            if (-not $dockerCmd) {
                Write-Host "[ERROR] Docker Desktop installation failed." -ForegroundColor Red
                Write-Host "        Please install it manually:" -ForegroundColor Red
                Write-Host "        https://www.docker.com/products/docker-desktop/" -ForegroundColor Red
                exit 1
            }
        }
        Write-Host "[OK]    Docker Desktop installed successfully." -ForegroundColor Green
        exit 0
    }
    "start-docker" {
        $dockerDesktopPaths = @(
            "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
            "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe"
        )
        $dockerExe = $dockerDesktopPaths | Where-Object { Test-Path $_ } | Select-Object -First 1
        if (-not $dockerExe) {
            Write-Host "[ERROR] Docker Desktop executable not found. Please start it manually." -ForegroundColor Red
            exit 1
        }
        Write-Host "Starting Docker Desktop..." -ForegroundColor Yellow
        Start-Process $dockerExe
        # Wait up to 90 seconds for the Docker daemon to become available
        $timeout = 90
        $elapsed = 0
        while ($elapsed -lt $timeout) {
            Start-Sleep -Seconds 3
            $elapsed += 3
            & docker info 2>$null | Out-Null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK]    Docker Desktop is running." -ForegroundColor Green
                exit 0
            }
            Write-Host "        Waiting for Docker Desktop... ($elapsed/$timeout s)" -ForegroundColor Yellow
        }
        Write-Host "[ERROR] Docker Desktop did not start within $timeout seconds." -ForegroundColor Red
        Write-Host "        Please open Docker Desktop manually, wait for it to finish starting, then re-run this script." -ForegroundColor Red
        exit 1
    }
    "install-python" {
        $winget = Find-Winget
        if (-not $winget) {
            Write-Host "[ERROR] winget is not available." -ForegroundColor Red
            Write-Host "        Please install Python 3.9+ manually:" -ForegroundColor Red
            Write-Host "        https://www.python.org/downloads/" -ForegroundColor Red
            exit 1
        }
        Write-Host "Installing Python 3.12 via winget..." -ForegroundColor Yellow
        & $winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
        # winget exits non-zero for "no upgrade available" — treat that as success.
        if ($LASTEXITCODE -ne 0 -and $LASTEXITCODE -ne -1978335999) {
            $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
            if (-not $pythonCmd) {
                Write-Host "[ERROR] Python installation failed." -ForegroundColor Red
                Write-Host "        Please install Python 3.9+ manually:" -ForegroundColor Red
                Write-Host "        https://www.python.org/downloads/" -ForegroundColor Red
                exit 1
            }
        }
        Write-Host "[OK]    Python 3.12 installed successfully." -ForegroundColor Green
        exit 0
    }
}
