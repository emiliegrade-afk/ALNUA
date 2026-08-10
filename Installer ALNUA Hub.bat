@echo off
title ALNUA Hub — installation
cd /d "%~dp0"

echo.
echo  ========================================
echo   Installation ALNUA Hub
echo  ========================================
echo.
echo  Ce script verifie Python, npm et cree
echo  un raccourci Bureau pour demarrer le Hub.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install-hub.ps1"
if errorlevel 1 (
    echo.
    echo  Installation incomplete — voir les messages ci-dessus.
    pause
    exit /b 1
)

echo.
pause
