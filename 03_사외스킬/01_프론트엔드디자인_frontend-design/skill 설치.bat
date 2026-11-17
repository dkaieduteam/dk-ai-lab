@echo off
rem Install the frontend-design skill from this folder into this PC's Codex skills folder.
rem This file has no Korean on purpose (cmd.exe can misread Korean lines). Messages come from the 09_ folder.
setlocal
set "M="
for /d %%D in ("%~dp009_*") do set "M=%%~fD"
set "SRC=%~dp0frontend-design"
set "HOME_DIR=%USERPROFILE%\.codex"
if defined CODEX_HOME set "HOME_DIR=%CODEX_HOME%"
set "DST=%HOME_DIR%\skills\frontend-design"
chcp 65001 >nul
if not exist "%SRC%\SKILL.md" goto fail
if exist "%DST%" rmdir /s /q "%DST%"
xcopy "%SRC%" "%DST%\" /E /I /Y /Q >nul
if not exist "%DST%\SKILL.md" goto fail
type "%M%\installed.txt"
echo.
pause
exit /b 0

:fail
type "%M%\failed.txt"
echo.
pause
exit /b 1
