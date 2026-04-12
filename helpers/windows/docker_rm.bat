@echo off
rem Remove all klodtalk session containers.
for /f %%i in ('docker ps -aq --filter "name=klodtalk_"') do docker rm -f %%i
