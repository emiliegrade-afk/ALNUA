# Redemarrage complet ALNUA (API + web + bots) sur le bon port.
# Usage: .\scripts\restart-all.ps1

param(
    [int]$HubPort = 0,
    [switch]$SkipWeb,
    [switch]$SkipBots
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot

if ($HubPort -le 0) {
    $HubPort = [int](& (Join-Path $Root "scripts\get-hub-port.ps1"))
}

Write-Host "Redemarrage ALNUA Hub (port $HubPort)..." -ForegroundColor Yellow

& (Join-Path $Root "scripts\sync-hub-env.ps1") -Port $HubPort | Out-Null

& (Join-Path $Root "scripts\stop-all.ps1") -HubPort $HubPort
Start-Sleep -Seconds 3

$startParams = @{ HubPort = $HubPort }
if ($SkipWeb) { $startParams.SkipWeb = $true }
if ($SkipBots) { $startParams.SkipBots = $true }

& (Join-Path $Root "scripts\start-all.ps1") @startParams

Start-Sleep -Seconds 12
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$HubPort/health" -TimeoutSec 20
    if ($health.service -eq "alnua-hub") {
        Write-Host "Hub API OK -> http://127.0.0.1:$HubPort" -ForegroundColor Green
    }
} catch {
    Write-Host "Hub API pas encore pret - voir data\hub_api.log" -ForegroundColor Yellow
}

if (-not $SkipWeb) {
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:3000/api/hub/health" -UseBasicParsing -TimeoutSec 15
        Write-Host "Interface web OK -> http://localhost:3000 (rafraichis la page)" -ForegroundColor Green
    } catch {
        Write-Host "Interface web en demarrage - attends 30s puis Ctrl+F5 sur localhost:3000" -ForegroundColor Yellow
    }
}
