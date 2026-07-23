# DEPRECATED — le Web est gere par hub_supervisor.py (Demarrer-Hub.bat).

# Usage legacy: .\scripts\start_hub_web_daemon.ps1

# Prefer: .\scripts\start-all.ps1



param([int]$Port = 3000)



$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot

$Python = Join-Path $Root ".venv\Scripts\python.exe"

$Supervisor = Join-Path $Root "scripts\hub_supervisor.py"



Write-Host "Web gere par hub_supervisor — demarrage stack complete..." -ForegroundColor Yellow

& $Python $Supervisor start --api-port 8003 --web-port $Port

exit $LASTEXITCODE

