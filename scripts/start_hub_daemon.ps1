# DEPRECATED — redirige vers hub_supervisor.py (remplace watch_hub_daemon.ps1).

# Usage: .\scripts\start_hub_daemon.ps1

# Prefer: .\scripts\start-all.ps1 ou Demarrer-Hub.bat



param([int]$Port = 8003)



$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot

$Python = Join-Path $Root ".venv\Scripts\python.exe"

$Supervisor = Join-Path $Root "scripts\hub_supervisor.py"



if (-not (Test-Path $Python)) {

    Write-Host "venv introuvable: $Python" -ForegroundColor Red

    exit 1

}



Write-Host "Hub supervisor (API :$Port + Web :3000)..." -ForegroundColor Cyan

& $Python $Supervisor start --api-port $Port --web-port 3000

exit $LASTEXITCODE

