@echo off

title ALNUA Hub - redemarrage

cd /d "%~dp0"



echo.

echo  ========================================

echo   ALNUA Hub - redemarrage complet

echo  ========================================

echo.



powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\restart-all.ps1"

if errorlevel 1 (

    echo.

    echo  ERREUR - voir data\hub_api.log

    pause

    exit /b 1

)



echo.

echo  OK - Hub redemarre (port dans data\hub_active_port.txt)

echo  UI : http://localhost:3000

echo.

pause

