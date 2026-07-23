@echo off
title ALNUA Hub
cd /d "%~dp0"

echo.
echo  ========================================
echo   ALNUA Hub - demarrage complet
echo  ========================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-all.ps1" -OpenBrowser
if errorlevel 1 (
    echo.
    echo  ERREUR - voir le message ci-dessus.
    echo.
    pause
    exit /b 1
)

echo.
echo  OK - tu peux fermer cette fenetre.
echo.
pause
