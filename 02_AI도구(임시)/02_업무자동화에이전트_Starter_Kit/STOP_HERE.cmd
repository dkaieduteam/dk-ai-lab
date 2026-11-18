@echo off
setlocal
chcp 65001 > nul
title AI Automation Training - Stop Here
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Stop-TrainingConsole.ps1"
set "RESULT=%ERRORLEVEL%"
echo.
echo 이 창은 10초 뒤 닫힙니다.
timeout /t 10 /nobreak >nul
exit /b %RESULT%