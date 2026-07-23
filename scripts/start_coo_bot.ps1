# Demarre le bot Telegram Aria (COO) en polling local.
# Prerequis .env : TELEGRAM_BOT_TOKEN + TELEGRAM_POLLING=0 (ce script gere le polling)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "venv introuvable: $Python" -ForegroundColor Red
    exit 1
}

Set-Location $Root
$env:PYTHONPATH = $Root
& $Python -m bots.telegram_bot
