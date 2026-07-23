# Watchdog Next.js - relance uniquement si le port 3000 ne repond plus.
# Usage: .\scripts\watch_hub_web.ps1 [-Port 3000]

param([int]$Port = 3000)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$LogDir = Join-Path $Root "data"
$LogFile = Join-Path $LogDir "hub_web.log"
$WatchPidFile = Join-Path $LogDir "hub_web_watch.pid"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$PID | Out-File -FilePath $WatchPidFile -Encoding ascii -NoNewline

function Write-Log([string]$Msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

function Test-WebAlive([int]$P) {
    foreach ($host in @("127.0.0.1", "localhost")) {
        try {
            $r = Invoke-WebRequest -Uri "http://${host}:$P" -UseBasicParsing -TimeoutSec 20
            if ($r.StatusCode -eq 200) { return $true }
        } catch { }
    }
    return $false
}

function Start-WebServer([int]$P) {
    $script = Join-Path $Root "scripts\restart_hub_web.ps1"
    Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $script, "-Port", "$P") `
        -WorkingDirectory $Root `
        -WindowStyle Minimized | Out-Null
}

Write-Log "=== Web watchdog demarre (PID $PID, port $Port) ==="

$failTicks = 0
$lastStartAt = [datetime]::MinValue

while ($true) {
    if (Test-WebAlive $Port) {
        $failTicks = 0
        Start-Sleep -Seconds 30
        continue
    }

    $inGrace = ((Get-Date) - $lastStartAt).TotalSeconds -lt 240
    if ($inGrace) {
        Write-Log "Port $Port en demarrage (grace) - attente"
        Start-Sleep -Seconds 15
        continue
    }

    $failTicks++
    Write-Log "Port $Port KO (tentative $failTicks/3)"
    if ($failTicks -lt 3) {
        Start-Sleep -Seconds 15
        continue
    }

    $failTicks = 0
    Write-Log "Demarrage Next.js sur :$Port"
    try {
        & (Join-Path $Root "scripts\sync-hub-env.ps1") | Out-Null
        Start-WebServer $Port
        $lastStartAt = Get-Date
    } catch {
        Write-Log "ERREUR lancement Next: $_"
    }

    Start-Sleep -Seconds 30
}
