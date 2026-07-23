# Redemarre UNE seule instance uvicorn ALNUA Hub (evite les zombies sur le port)
# Usage: .\scripts\restart_hub_api.ps1 [-Port 8000] [-NoReload]
#
# IMPORTANT: --reload coupe l'API a chaque sauvegarde de fichier (deconnexion UI).
# Pour un Hub stable 24/7: .\scripts\start_hub_daemon.ps1 (watchdog + auto-restart)

param(
    [int]$Port = 8003,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "venv introuvable: $Python" -ForegroundColor Red
    exit 1
}

Write-Host "Arret des listeners sur le port $Port..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
        $ownPid = $_.OwningProcess
        Write-Host "  kill port holder PID $ownPid"
        Stop-Process -Id $ownPid -Force -ErrorAction SilentlyContinue
    }

Write-Host "Arret des processus uvicorn ALNUA..." -ForegroundColor Cyan
Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object {
        $_.CommandLine -match 'uvicorn\s+api\.main:app' -or
        $_.CommandLine -match 'multiprocessing\.spawn'
    } |
    ForEach-Object {
        Write-Host "  kill PID $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Start-Sleep -Seconds 3

$still = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($still) {
    Write-Host "ATTENTION: le port $Port est encore occupe." -ForegroundColor Red
    exit 1
}

Write-Host "Demarrage Hub API sur http://127.0.0.1:$Port ..." -ForegroundColor Green
Set-Location $Root

$uvicornArgs = @("-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$Port")
# Default NoReload — reload provoque des deconnexions constantes pendant le dev.
if ($Reload) {
    $uvicornArgs += "--reload"
}

& $Python @uvicornArgs
