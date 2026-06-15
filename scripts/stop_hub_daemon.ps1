# Arrete le Hub API + watchdog
param([int]$Port = 8000)

$Root = Split-Path -Parent $PSScriptRoot
$PidFile = Join-Path $Root "data\hub_api.pid"
$WatchPidFile = Join-Path $Root "data\hub_watch.pid"

if (Test-Path $WatchPidFile) {
    $wpid = (Get-Content $WatchPidFile -Raw).Trim()
    if ($wpid -match '^\d+$') {
        Stop-Process -Id ([int]$wpid) -Force -ErrorAction SilentlyContinue
        Write-Host "Watchdog arrete (PID $wpid)" -ForegroundColor Cyan
    }
    Remove-Item $WatchPidFile -Force -ErrorAction SilentlyContinue
}

if (Test-Path $PidFile) {
    $savedPid = (Get-Content $PidFile -Raw).Trim()
    if ($savedPid -match '^\d+$') {
        Stop-Process -Id ([int]$savedPid) -Force -ErrorAction SilentlyContinue
        Write-Host "Hub API arrete (PID $savedPid)" -ForegroundColor Cyan
    }
    Remove-Item $PidFile -Force -ErrorAction SilentlyContinue
}

Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "Port $Port libere (PID $($_.OwningProcess))" -ForegroundColor Cyan
    }
