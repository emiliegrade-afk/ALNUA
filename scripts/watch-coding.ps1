# Suit l'activite coding en direct.
param([int]$Lines = 30)

$Root = Split-Path -Parent $PSScriptRoot
$CodingLog = Join-Path $Root "data\coding_pipeline.log"
$HubLog = Join-Path $Root "data\hub_api.log"

Write-Host ""
Write-Host "=== File Academy ===" -ForegroundColor Cyan
& "$Root\scripts\wake-agents.ps1" -Status

Write-Host "=== coding_pipeline.log (activite dev_app) ===" -ForegroundColor Cyan
if (Test-Path $CodingLog) {
    Get-Content $CodingLog -Tail $Lines
} else {
    Write-Host "Aucune activite encore — lance wake-agents puis attends une issue in-pipeline." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== hub_api.log (Hub + poll GitHub) ===" -ForegroundColor Cyan
if (Test-Path $HubLog) {
    Get-Content $HubLog -Tail $Lines | Select-String -Pattern "GHIssues|HubCoding|uvicorn|Demarrage|issue|Pipeline|WATCHDOG" -CaseSensitive:$false
} else {
    Write-Host "Hub jamais demarre — .\scripts\start_hub_daemon.ps1" -ForegroundColor Yellow
}
