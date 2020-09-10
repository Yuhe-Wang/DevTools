@echo off
set PYTHON_VERSION=3.8.5
%~dp0..\app\python-%PYTHON_VERSION%\python %~dp0..\main.py %*
if %ERRORLEVEL% NEQ 0 exit /b 1