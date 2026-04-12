@echo off
rem Build the klodtalk-agent Docker image.
@echo off
rem Build the klodtalk-agent Docker image.
set "SCRIPT_DIR=%~dp0"
pushd "%SCRIPT_DIR%\..\.."
set "PROJECT_ROOT=%CD%"
popd
docker build -f server\Dockerfile.agent -t klodtalk-agent "%PROJECT_ROOT%"
