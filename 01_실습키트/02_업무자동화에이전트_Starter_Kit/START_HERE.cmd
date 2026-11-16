@echo off
setlocal
chcp 65001 > nul
title AI Automation Training - Start Here (v2 .env-driven)
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Start-TrainingConsole.ps1"
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
  echo.
  echo [INFO] 자동 흐름이 종료되었습니다. 이 창은 10초 뒤 닫힙니다.
  timeout /t 10 /nobreak >nul
)
exit /b %RESULT%