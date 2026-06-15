# Enregistre le Hub ALNUA au demarrage Windows (tache planifiee utilisateur).
# Usage (PowerShell admin NON requis): .\scripts\install_hub_daemon_startup.ps1
# Desinstaller: .\scripts\install_hub_daemon_startup.ps1 -Remove

param([switch]$Remove)

$Root = Split-Path -Parent $PSScriptRoot
$StartScript = Join-Path $Root "scripts\start_hub_daemon.ps1"
$TaskName = "ALNUA-Hub-API"

if ($Remove) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Tache $TaskName supprimee." -ForegroundColor Green
    exit 0
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$StartScript`""
$Trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 2)

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger `
    -Settings $Settings -Description "ALNUA Hub API daemon (port 8000)" -Force

Write-Host "Tache $TaskName enregistree - Hub demarre a chaque ouverture de session." -ForegroundColor Green
Write-Host 'Verifier: Invoke-WebRequest http://127.0.0.1:8000/health' -ForegroundColor Cyan
