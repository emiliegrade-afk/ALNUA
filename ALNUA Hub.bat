@echo off
title ALNUA Hub
cd /d "%~dp0"

echo.
echo  ========================================
echo   ALNUA Hub - demarrage
echo  ========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-all.ps1" -OpenBrowser
if errorlevel 1 (
    echo.
    echo  ERREUR au demarrage - voir le message ci-dessus.
    pause
    exit /b 1
)

echo.
echo  OK - tu peux fermer cette fenetre.
echo  Arret : Arreter ALNUA Hub.bat
echo.
timeout /t 12 >nul
