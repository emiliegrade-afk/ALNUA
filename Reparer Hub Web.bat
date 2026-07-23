@echo off
title ALNUA Hub - reparation web
cd /d "%~dp0"

echo.
echo  Reparation interface web (cache + redemarrage)
echo  Attendre ~30 secondes puis rafraichir avec Ctrl+Shift+R
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\repair_hub_web.ps1"
