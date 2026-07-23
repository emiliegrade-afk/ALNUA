# Arrete Next.js + watchdog web
param([int]$Port = 3000)

$Root = Split-Path -Parent $PSScriptRoot
$WatchPidFile = Join-Path $Root "data\hub_web_watch.pid"
$WebPidFile = Join-Path $Root "data\hub_web.pid"

if (Test-Path $WatchPidFile) {
    $wpid = (Get-Content $WatchPidFile -Raw).Trim()
    if ($wpid -match '^\d+$') {
        Stop-Process -Id ([int]$wpid) -Force -ErrorAction SilentlyContinue
        Write-Host "Web watchdog arrete (PID $wpid)" -ForegroundColor Cyan
    }
    Remove-Item $WatchPidFile -Force -ErrorAction SilentlyContinue
}

if (Test-Path $WebPidFile) {
    $pidWeb = (Get-Content $WebPidFile -Raw).Trim()
    if ($pidWeb -match '^\d+$') {
        Stop-Process -Id ([int]$pidWeb) -Force -ErrorAction SilentlyContinue
        Write-Host "Next.js arrete (PID $pidWeb)" -ForegroundColor Cyan
    }
    Remove-Item $WebPidFile -Force -ErrorAction SilentlyContinue
}

Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "Port $Port libere (PID $($_.OwningProcess))" -ForegroundColor Cyan
    }
