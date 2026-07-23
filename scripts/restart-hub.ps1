# Redemarrage Hub propre via supervisor v2.

param([int]$Port = 8003)



$ErrorActionPreference = "Continue"

$Root = Split-Path -Parent $PSScriptRoot

$Python = Join-Path $Root ".venv\Scripts\python.exe"

$Supervisor = Join-Path $Root "scripts\hub_supervisor.py"



Write-Host "Arret supervisor: supervisor..." -ForegroundColor Cyan

& $Python $Supervisor stop 2>$null

Start-Sleep -Seconds 2



Write-Host "Demarrage Hub: supervisor..." -ForegroundColor Cyan

& $Python $Supervisor start --api-port $Port --web-port 3000

if ($LASTEXITCODE -ne 0) {

    Write-Host "Erreur - voir data\hub_supervisor.log" -ForegroundColor Red

    exit 1

}



for ($i = 0; $i -lt 30; $i++) {

    Start-Sleep -Seconds 2

    try {

        $h = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 8

        if ($h.service -eq "alnua-hub") {

            Write-Host "Hub OK -> http://127.0.0.1:$Port" -ForegroundColor Green

            exit 0

        }

    } catch { }

}



Write-Host "Hub pas encore pret - voir data\hub_supervisor.log" -ForegroundColor Yellow

exit 1

