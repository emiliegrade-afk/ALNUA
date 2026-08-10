@echo off
REM Lance le Hub en arriere-plan (aucune fenetre CMD qui reste ouverte).
cd /d "%~dp0"
wscript.exe "%~dp0scripts\launch-hub-silent.vbs"
exit /b 0
