@echo off
title ALNUA Hub - raccourcis
cd /d "%~dp0\..\.."

echo Creation des raccourcis Bureau (ALNUA Hub / Arreter / Nadia)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\setup-hub-shortcuts.ps1" -DesktopOnly -CleanOld
echo.
pause
