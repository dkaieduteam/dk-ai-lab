@echo off
rem Remove the print-design skill from this PC's Codex skills folder. The copy in this folder stays.
rem This file has no Korean on purpose (cmd.exe can misread Korean lines). Messages come from the 09_ folder.
setlocal
set "M="
for /d %%D in ("%~dp009_*") do set "M=%%~fD"
set "HOME_DIR=%USERPROFILE%\.codex"
if defined CODEX_HOME set "HOME_DIR=%CODEX_HOME%"
set "DST=%HOME_DIR%\skills\print-design"
chcp 65001 >nul
if not exist "%DST%" goto none
rmdir /s /q "%DST%"
if exist "%DST%" goto fail
type "%M%\removed.txt"
echo.
pause
exit /b 0

:none
type "%M%\notfound.txt"
echo.
pause
exit /b 0

:fail
type "%M%\failed.txt"
echo.
pause
exit /b 1
