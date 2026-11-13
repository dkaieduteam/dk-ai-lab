@echo off
rem Go back to the previous program version and make HTML again.
rem This file has no Korean on purpose (cmd.exe can misread Korean lines). Messages come from the 02_ folder.
setlocal
set "P="
set "T="
for /d %%D in ("%~dp009_*") do set "P=%%~fD"
for /d %%D in ("%P%\02_*") do set "T=%%~fD"
set "PY=%P%\python\python.exe"
if not exist "%PY%" goto nopy
"%PY%" -I -B -X utf8 "%T%" rollback
if errorlevel 1 goto wait
exit /b 0

:nopy
chcp 65001 >nul
if exist "%T%\no_python.txt" type "%T%\no_python.txt"

:wait
echo.
pause
exit /b 1
