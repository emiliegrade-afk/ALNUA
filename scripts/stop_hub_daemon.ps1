# Arrete le Hub API + watchdog + zombies uvicorn sur tous les ports dev
param([int]$Port = 8003)

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

Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'uvicorn api\.main' } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "uvicorn arrete (PID $($_.ProcessId))" -ForegroundColor Cyan
    }

Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "Port $Port libere (PID $($_.OwningProcess))" -ForegroundColor Cyan
    }

# Dev uvicorn parfois sur d'autres ports — tout nettoyer
foreach ($extraPort in @(8000, 8001, 8002, 8003)) {
    if ($extraPort -eq $Port) { continue }
    Get-NetTCPConnection -LocalPort $extraPort -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)" -ErrorAction SilentlyContinue
            if ($proc -and $proc.CommandLine -match 'uvicorn api\.main') {
                Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
                Write-Host "Port $extraPort libere (uvicorn PID $($_.OwningProcess))" -ForegroundColor Cyan
            }
        }
}
