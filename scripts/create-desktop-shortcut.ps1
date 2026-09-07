# Cree un raccourci Bureau "ALNUA Hub" — double-clic = ouvrir sans fenetre CMD.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$VbsPath = Join-Path $Root "scripts\launch-hub-silent.vbs"
$BatPath = Join-Path $Root "ALNUA Hub.bat"
$IconPath = Join-Path $Root "assets\alnua-x-round.ico"
if (-not (Test-Path $IconPath)) {
    $IconPath = Join-Path $Root "assets\alnua-hub.ico"
}
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "ALNUA Hub.lnk"

$Target = if (Test-Path $VbsPath) { $VbsPath } else { $BatPath }
if (-not (Test-Path $Target)) {
    Write-Host "Fichier introuvable: $Target" -ForegroundColor Red
    exit 1
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($ShortcutPath)
# Passer par wscript.exe pour que Windows honore IconLocation (X rond).
$ext = [System.IO.Path]::GetExtension($Target).ToLowerInvariant()
if ($ext -eq ".vbs") {
    $shortcut.TargetPath = Join-Path $env:SystemRoot "System32\wscript.exe"
    $shortcut.Arguments = "//nologo `"$Target`""
}
elseif ($ext -eq ".bat" -or $ext -eq ".cmd") {
    $shortcut.TargetPath = Join-Path $env:SystemRoot "System32\cmd.exe"
    $shortcut.Arguments = "/c `"$Target`""
}
else {
    $shortcut.TargetPath = $Target
}
$shortcut.WorkingDirectory = $Root
$shortcut.Description = "ALNUA Hub — demarrage silencieux (pas de fenetre CMD)"
if (Test-Path $IconPath) {
    $shortcut.IconLocation = "$IconPath,0"
}
$shortcut.Save()

Write-Host "Raccourci cree : $ShortcutPath" -ForegroundColor Green
Write-Host "Double-clic = Hub en arriere-plan + navigateur. Aucune CMD permanente." -ForegroundColor Cyan
