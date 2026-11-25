@echo off
rem Opens the pre-check window (09_* folder\Ready-Check.ps1). The practice folders are not changed.
rem This file has no Korean on purpose (cmd.exe can misread Korean lines). Messages come from the 09_ folder.
setlocal
set "G="
for /d %%D in ("%~dp009_*") do if exist "%%~fD\Ready-Check.ps1" set "G=%%~fD\Ready-Check.ps1"
if not defined G goto nogui
start "" powershell.exe -NoLogo -NoProfile -STA -ExecutionPolicy Bypass -WindowStyle Hidden -File "%G%"
exit /b 0

:nogui
echo.
echo   [FAIL] Check window not found. Unzip the original zip again (right click - Extract All).
echo.
pause
exit /b 1
