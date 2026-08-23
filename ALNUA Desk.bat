@echo off
REM Ancien nom — redirige vers Spark.
cd /d "%~dp0"
wscript.exe "%~dp0scripts\launch-spark-silent.vbs"
exit /b 0
