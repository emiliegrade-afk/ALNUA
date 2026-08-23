@echo off
REM Lance Spark en arriere-plan (aucune fenetre CMD).
cd /d "%~dp0"
wscript.exe "%~dp0scripts\launch-spark-silent.vbs"
exit /b 0
