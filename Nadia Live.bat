@echo off
title Nadia Live
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-all.ps1" -OpenBrowser -OpenUrl "http://localhost:3000/live"
if errorlevel 1 (
    echo.
    echo  ERREUR au demarrage — lance "ALNUA Hub.bat" puis ouvre http://localhost:3000/live
    pause
    exit /b 1
)
exit /b 0
