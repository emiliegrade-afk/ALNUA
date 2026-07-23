@echo off
chcp 65001 > nul
title Nadia Desktop ? ALNUA
set HUB_ROOT=C:\Dev\ALUNA_HUB
set PYTHON=%HUB_ROOT%\.venv\Scripts\python.exe
set ALNUA_HUB_ROOT=%HUB_ROOT%
set PYTHONPATH=%HUB_ROOT%
set NADIA_LLM_BACKEND=glm_direct
set NADIA_TTS_BACKEND=edge
for /f "tokens=1,* delims==" %%a in ('findstr /i "GLM_API_KEY" "%HUB_ROOT%\.env"') do (
    if /i "%%a"=="GLM_API_KEY" set GLM_API_KEY=%%b
)
cd /d "%HUB_ROOT%\nadia_desktop"
"%PYTHON%" main.py
