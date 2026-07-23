# Demarre le bot Telegram Nadia (secrétaire) en polling local.
# Prerequis .env : TELEGRAM_SECRETARY_BOT_TOKEN + TELEGRAM_SECRETARY_POLLING=1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "venv introuvable: $Python" -ForegroundColor Red
    exit 1
}

Set-Location $Root
$env:PYTHONPATH = $Root
& $Python -m bots.telegram_secretary_bot
