@echo off
title ALNUA Hub
cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\launch-hub-app.ps1"
if errorlevel 1 (
    echo.
    echo  Hub pas demarre - lancement complet...
    echo.
    powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-all.ps1" -OpenBrowser
    if errorlevel 1 (
        echo.
        echo  ERREUR - voir le message ci-dessus.
        pause
        exit /b 1
    )
)
