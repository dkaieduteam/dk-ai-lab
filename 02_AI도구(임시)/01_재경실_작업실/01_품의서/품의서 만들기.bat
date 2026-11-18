@echo off
rem Make HTML from the 01_ folder and open the result page. If the AI changed the program, test it first.
rem This file has no Korean on purpose (cmd.exe can misread Korean lines). Messages come from the 02_ folder.
setlocal
set "P="
set "T="
for /d %%D in ("%~dp009_*") do set "P=%%~fD"
for /d %%D in ("%P%\02_*") do set "T=%%~fD"
set "PY=%P%\python\python.exe"
if not exist "%PY%" goto nopy
"%PY%" -I -B -X utf8 "%T%" make
if errorlevel 1 goto wait
exit /b 0

:nopy
chcp 65001 >nul
if exist "%T%\no_python.txt" type "%T%\no_python.txt"

:wait
echo.
pause
exit /b 1
