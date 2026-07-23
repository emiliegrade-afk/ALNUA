@echo off
title ALNUA - Relancer les agents
cd /d "%~dp0"

echo.
echo  Relance des agents (Academy + pipeline)...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\wake-agents.ps1"
if errorlevel 1 (
    echo.
    echo  ERREUR - le Hub API est peut-etre arrete.
    echo  Lance "ALNUA Hub (demarrage complet)" d abord.
    pause
    exit /b 1
)

echo.
timeout /t 8 >nul
