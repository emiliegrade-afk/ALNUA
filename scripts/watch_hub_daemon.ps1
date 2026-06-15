# Surveille le Hub API : logs + redemarrage auto si crash.
# Usage: .\scripts\watch_hub_daemon.ps1 [-Port 8000]

param([int]$Port = 8000)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$LogDir = Join-Path $Root "data"
$LogFile = Join-Path $LogDir "hub_api.log"
$WatchPidFile = Join-Path $LogDir "hub_watch.pid"

if (-not (Test-Path $Python)) {
    Write-Host "venv introuvable: $Python" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$WatchPid = $PID
$WatchPid | Out-File -FilePath $WatchPidFile -Encoding utf8 -NoNewline

function Write-Log([string]$Msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

Write-Log "=== Hub watchdog demarre (PID $PID, port $Port) ==="
Set-Location $Root

while ($true) {
    $onPort = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($onPort) {
        Write-Log "Port $Port occupe - attente 10s"
        Start-Sleep -Seconds 10
        continue
    }

    Write-Log "Demarrage uvicorn sur :$Port"
    try {
        & $Python -m uvicorn api.main:app --host 127.0.0.1 --port $Port --log-level info 2>&1 |
            ForEach-Object { Add-Content -Path $LogFile -Value $_ -Encoding utf8 }
        $exit = $LASTEXITCODE
    } catch {
        Write-Log "ERREUR lancement: $_"
        $exit = 1
    }

    Write-Log "uvicorn termine (exit=$exit) - redemarrage dans 5s"
    Start-Sleep -Seconds 5
}
