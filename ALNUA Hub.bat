@echo off
title ALNUA Hub
cd /d "%~dp0"

echo.
echo  ========================================
echo   ALNUA Hub — demarrage
echo  ========================================
echo.
echo  Lance l'API (port 8003), l'interface web
echo  (port 3000) et ouvre ton navigateur.
echo.
echo  Premier lancement ? Execute d'abord
echo  "Installer ALNUA Hub.bat" une seule fois.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-all.ps1" -OpenBrowser
if errorlevel 1 (
    echo.
    echo  ERREUR au demarrage — voir le message ci-dessus.
    echo  Astuce : .\scripts\hub-status.ps1 pour diagnostiquer.
    pause
    exit /b 1
)

echo.
echo  OK — le Hub tourne en arriere-plan.
echo  Tu peux fermer cette fenetre.
echo.
echo  Pour arreter : double-clic sur "Arreter ALNUA Hub.bat"
echo.
timeout /t 12 >nul
