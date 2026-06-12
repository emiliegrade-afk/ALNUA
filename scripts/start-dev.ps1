# ALNUA Hub — démarre le frontend Next.js (un seul serveur)
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$webRoot = (Join-Path (Join-Path $PSScriptRoot "..") "web") | Resolve-Path

# Libère le port 3000 si un ancien next dev traîne
$pids = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
  Select-Object -ExpandProperty OwningProcess -Unique
foreach ($procId in $pids) {
  Write-Host "Arrêt du processus $procId sur le port 3000..."
  Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
}

$nextCache = Join-Path $webRoot ".next"
if (Test-Path $nextCache) {
  Write-Host "Suppression du cache .next..."
  Remove-Item -Recurse -Force $nextCache
}

Set-Location $webRoot
Write-Host "Démarrage sur http://localhost:3000"
npm run dev
