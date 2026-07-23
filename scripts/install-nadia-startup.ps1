# Installe Nadia au demarrage Windows (Hub auto + accueil)
# Usage: .\scripts\install-nadia-startup.ps1
# Desinstaller: schtasks /Delete /TN "ALNUA Nadia Logon" /F

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Script = Join-Path $Root "scripts\nadia-at-logon.ps1"
$TaskName = "ALNUA Nadia Logon"

if (-not (Test-Path $Script)) {
    Write-Host "Script introuvable: $Script" -ForegroundColor Red
    exit 1
}

$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$Script`"" `
    -WorkingDirectory $Root

$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Demarre ALNUA Hub et accueil Nadia au logon Windows" `
    -Force | Out-Null

Write-Host ""
Write-Host "Nadia installee au demarrage Windows." -ForegroundColor Green
Write-Host "  Tache : $TaskName"
Write-Host "  Script: $Script"
Write-Host ""
Write-Host "Test manuel : powershell -File `"$Script`""
Write-Host "Desinstaller : schtasks /Delete /TN `"$TaskName`" /F"
Write-Host ""
