# ALNUA Hub - demarre le frontend Next.js (un seul serveur)
param([switch]$Clean)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$webRoot = (Join-Path (Join-Path $PSScriptRoot "..") "web") | Resolve-Path

$pids = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
foreach ($procId in $pids) {
  Write-Host "Arret du processus $procId sur le port 3000..."
  Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}

$nextCache = Join-Path $webRoot ".next"
if ($Clean -and (Test-Path $nextCache)) {
  Write-Host "Suppression du cache .next..."
  Remove-Item -Recurse -Force $nextCache
}

Set-Location $webRoot
Write-Host "Demarrage sur http://localhost:3000"
npm run dev
