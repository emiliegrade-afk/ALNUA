# Renomme le dossier racine ALUNA_HUB → ALNUA_HUB
# Fermer Cursor/VS Code avant d'exécuter ce script.
$ErrorActionPreference = "Stop"
$src = "c:\Dev\ALUNA_HUB"
$dst = "c:\Dev\ALNUA_HUB"
if (-not (Test-Path $src)) {
  if (Test-Path $dst) {
    Write-Host "Déjà renommé : $dst"
    exit 0
  }
  Write-Error "Dossier source introuvable : $src"
}
if (Test-Path $dst) {
  Write-Error "La destination existe déjà : $dst"
}
Get-NetTCPConnection -LocalPort 3000,3001,8000 -State Listen -ErrorAction SilentlyContinue |
  ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
Start-Sleep -Seconds 2
Rename-Item -Path $src -NewName "ALNUA_HUB"
Write-Host "OK — projet déplacé vers $dst"
Write-Host "Rouvrir Cursor sur c:\Dev\ALNUA_HUB"
