# Enregistre une lecon apres un fix manuel Emilie → agents dev_app apprennent.
param(
    [string]$Cause = "",
    [string]$Fix = "",
    [string]$Files = "",
    [int]$Issue = 0,
    [string]$HubUrl = "http://127.0.0.1:8000"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $Root ".env"
$key = ""
if (Test-Path $EnvFile) {
    $line = Get-Content $EnvFile | Where-Object { $_ -match '^HUB_API_KEY=' } | Select-Object -First 1
    if ($line) { $key = $line.Split('=', 2)[1].Trim() }
}

if (-not $Cause) {
    $Cause = Read-Host "Cause du bug (1 phrase)"
}
if (-not $Fix) {
    $Fix = Read-Host "Ce que tu as corrige (1 phrase)"
}
if (-not $Files) {
    $Files = Read-Host "Fichiers touches (optionnel, virgules)"
}

$body = @{
    cause    = $Cause
    fix      = $Fix
    repo_slug = "academy"
    agent_id = "dev_app"
}
if ($Files) { $body.files = @($Files -split ',\s*') }
if ($Issue -gt 0) { $body.issue_number = $Issue }

$headers = @{ "Content-Type" = "application/json" }
if ($key) { $headers["X-Hub-Key"] = $key }

$json = $body | ConvertTo-Json -Compress
try {
    $resp = Invoke-RestMethod -Uri "$HubUrl/academy/lesson" -Method POST -Headers $headers -Body $json
    Write-Host "Lecon enregistree pour dev_app (task: $($resp.task_id))" -ForegroundColor Green
} catch {
    Write-Host "ERREUR Hub API: $_" -ForegroundColor Red
    Write-Host "Verifiez que le daemon tourne: .\scripts\start_hub_daemon.ps1"
    exit 1
}
