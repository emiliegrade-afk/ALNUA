# Simule une alerte Sentry via l'API Hub (PowerShell-friendly)
# Usage: .\scripts\simulate_sentry.ps1 [-Port 8000] [-Title "Test crash"]

param(
    [int]$Port = 8000,
    [string]$Title = "Test crash HomeScreen"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $Root ".env"
$keyLine = Get-Content $envFile | Where-Object { $_ -match '^HUB_API_KEY=' } | Select-Object -First 1
if (-not $keyLine) {
    Write-Host "HUB_API_KEY manquant dans .env" -ForegroundColor Red
    exit 1
}
$key = $keyLine -replace '^HUB_API_KEY=', ''

$body = @{ title = $Title } | ConvertTo-Json -Compress
$uri = "http://127.0.0.1:$Port/ops/production/simulate"

$result = Invoke-RestMethod -Uri $uri -Method POST `
    -Headers @{ "X-Hub-Key" = $key; "Content-Type" = "application/json" } `
    -Body $body

$result | ConvertTo-Json -Depth 6
