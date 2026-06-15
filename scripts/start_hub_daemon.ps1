# Lance le watchdog Hub (survit aux crash + log dans data/hub_api.log).
# Usage: .\scripts\start_hub_daemon.ps1
# Arret: .\scripts\stop_hub_daemon.ps1

param([int]$Port = 8000)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$WatchScript = Join-Path $Root "scripts\watch_hub_daemon.ps1"
$WatchPidFile = Join-Path $Root "data\hub_watch.pid"

if (-not (Test-Path $WatchScript)) {
    Write-Host "watch_hub_daemon.ps1 introuvable" -ForegroundColor Red
    exit 1
}

if (Test-Path $WatchPidFile) {
    $wpid = (Get-Content $WatchPidFile -Raw).Trim()
    if ($wpid -match '^\d+$') {
        $alive = Get-Process -Id ([int]$wpid) -ErrorAction SilentlyContinue
        if ($alive) {
            Write-Host "Watchdog Hub deja actif (PID $wpid) - voir data/hub_api.log" -ForegroundColor Yellow
            exit 0
        }
    }
}

$portListen = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if ($portListen) {
    $pidOnPort = ($portListen | Select-Object -First 1).OwningProcess
    Write-Host "Hub deja actif sur le port $Port (PID $pidOnPort)" -ForegroundColor Yellow
    exit 0
}

Start-Process `
    -FilePath "powershell.exe" `
    -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $WatchScript, "-Port", "$Port" `
    -WorkingDirectory $Root `
    -WindowStyle Hidden

Start-Sleep -Seconds 4

try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/health" -UseBasicParsing -TimeoutSec 15
    if ($r.StatusCode -eq 200) {
        Write-Host "Hub API demarre (watchdog) -> http://127.0.0.1:$Port" -ForegroundColor Green
        Write-Host "Logs: data\hub_api.log | Arret: .\scripts\stop_hub_daemon.ps1" -ForegroundColor Cyan
    }
} catch {
    Write-Host "Watchdog lance - /health pas encore pret (voir data\hub_api.log)" -ForegroundColor Yellow
}
