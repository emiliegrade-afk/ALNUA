$ErrorActionPreference = "SilentlyContinue"
$Root = "c:\Dev\ALUNA_HUB"
$WebRoot = Join-Path $Root "web"

Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Start-Sleep -Seconds 2

$nextCache = Join-Path $WebRoot ".next"
if (Test-Path $nextCache) {
    Remove-Item -Recurse -Force $nextCache
    Write-Host "Cache .next supprime"
}

Set-Location $WebRoot
Write-Host "Demarrage Next.js..."
npm run dev
