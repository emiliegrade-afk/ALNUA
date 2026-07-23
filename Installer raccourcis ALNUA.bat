@echo off
title ALNUA Hub - raccourcis
cd /d "%~dp0"

echo Creation des raccourcis avec le logo ALNUA...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\setup-hub-shortcuts.ps1"
echo.
pause
