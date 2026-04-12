@echo off
rem Generates a self-signed TLS certificate for KlodTalk WSS
rem Usage: helpers\windows\generate_cert.bat [cert_dir]
setlocal enabledelayedexpansion

set "CERT_DIR=%USERPROFILE%\.klodtalk\certs"
if not "%~1"=="" set "CERT_DIR=%~1"

if not exist "%CERT_DIR%" mkdir "%CERT_DIR%"

rem Try to detect LAN IP from ipconfig
set "DEFAULT_IP="
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R "IPv4"') do (
    set "DEFAULT_IP=%%a"
    rem Trim leading space
    set "DEFAULT_IP=!DEFAULT_IP: =!"
    goto :gotip
)
:gotip

if not "!DEFAULT_IP!"=="" (
    set /p "SERVER_IP=Server LAN IP address (default: !DEFAULT_IP!): "
    if "!SERVER_IP!"=="" set "SERVER_IP=!DEFAULT_IP!"
) else (
    set /p "SERVER_IP=Server LAN IP address (e.g. 192.168.1.100): "
)

if "!SERVER_IP!"=="" (
    echo Error: A real LAN IP is required.
    exit /b 1
)
if "!SERVER_IP!"=="0.0.0.0" (
    echo Error: A real LAN IP is required ^(not 0.0.0.0^).
    exit /b 1
)

openssl req -x509 -nodes -days 3650 -newkey rsa:2048 ^
  -keyout "%CERT_DIR%\server.key" ^
  -out "%CERT_DIR%\server.crt" ^
  -subj "/CN=klodtalk" ^
  -addext "subjectAltName=IP:!SERVER_IP!,IP:127.0.0.1"

echo.
echo Certificate generated in %CERT_DIR%
echo   %CERT_DIR%\server.crt  (give this to clients that need to trust it)
echo   %CERT_DIR%\server.key  (keep private, server-only)
echo.
echo Next steps:
echo   1. Set ssl_cert and ssl_key in config\server_config.yaml
echo   2. Restart the server
echo   3. For web browser: navigate to https://!SERVER_IP!:9000 and accept the self-signed cert
echo   4. For Android: copy server.crt to your device and install as CA certificate
echo.
echo Note: if your server IP changes, you must regenerate the certificate.
