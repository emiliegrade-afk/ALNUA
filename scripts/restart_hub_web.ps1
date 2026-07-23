# Redemarre le frontend Next.js
# Usage: .\scripts\restart_hub_web.ps1 [-Port 3000] [-Clean]
# -Clean : supprime .next (seulement si erreur ChunkLoadError)

param(
    [int]$Port = 3000,
    [switch]$Clean
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$WebRoot = Join-Path $Root "web"

Write-Host "Arret des listeners sur le port $Port..." -ForegroundColor Cyan
Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object {
        $ownPid = $_.OwningProcess
        if (Get-Process -Id $ownPid -ErrorAction SilentlyContinue) {
            Write-Host "  kill PID $ownPid"
            Stop-Process -Id $ownPid -Force -ErrorAction SilentlyContinue
        }
    }

Start-Sleep -Seconds 2

$nextCache = Join-Path $WebRoot ".next"
if ($Clean -and (Test-Path $nextCache)) {
    Write-Host "Suppression du cache .next..." -ForegroundColor Cyan
    Remove-Item -Recurse -Force $nextCache
}

Write-Host "Demarrage Next.js sur http://localhost:$Port ..." -ForegroundColor Green
Set-Location $WebRoot
npm run dev -- -p $Port
