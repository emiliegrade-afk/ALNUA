@echo off
title ALNUA Hub - arret
cd /d "%~dp0"

echo Arret ALNUA Hub...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop-all.ps1"
echo.
pause
