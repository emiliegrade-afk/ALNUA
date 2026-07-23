# Cree un raccourci Bureau "ALNUA Hub" (double-clic = ouvrir l'app).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$BatPath = Join-Path $Root "Ouvrir ALNUA Hub.bat"
$IconPath = Join-Path $Root "web\public\icon-512.png"
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "ALNUA Hub.lnk"

if (-not (Test-Path $BatPath)) {
    Write-Host "Fichier introuvable: $BatPath" -ForegroundColor Red
    exit 1
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $BatPath
$shortcut.WorkingDirectory = $Root
$shortcut.Description = "Cockpit ALNUA - entreprise virtuelle"
if (Test-Path $IconPath) {
    $shortcut.IconLocation = "$IconPath,0"
}
$shortcut.Save()

Write-Host "Raccourci cree : $ShortcutPath" -ForegroundColor Green
Write-Host "Double-clic sur le Bureau pour ouvrir ALNUA Hub." -ForegroundColor Cyan
