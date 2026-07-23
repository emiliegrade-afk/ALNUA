# Arrete la stack locale ALNUA (supervisor + bots Telegram).
# Usage: .\scripts\stop-all.ps1

param([int]$HubPort = 8003)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Supervisor = Join-Path $Root "scripts\hub_supervisor.py"

Write-Host "Arret ALNUA Hub..." -ForegroundColor Cyan

try {
    if (Test-Path $Python) {
        & $Python -c @"
from config.settings import get_settings
from services.telegram_presence import (
    COFFEE_MESSAGE_ARIA, COFFEE_MESSAGE_NADIA, send_telegram_text,
)
s = get_settings()
cid = (s.telegram_chat_id or '').strip()
if cid and s.telegram_bot_token.strip():
    send_telegram_text(s.telegram_bot_token, int(cid), COFFEE_MESSAGE_ARIA)
scid = (s.telegram_secretary_chat_id_effective or '').strip()
if scid and s.telegram_secretary_bot_token.strip():
    send_telegram_text(s.telegram_secretary_bot_token, int(scid), COFFEE_MESSAGE_NADIA)
"@ 2>$null
    }
} catch { }

if (Test-Path $Supervisor) {
    & $Python $Supervisor stop 2>$null
}

# Legacy watchdogs (migration)
& (Join-Path $Root "scripts\stop_hub_daemon.ps1") -Port $HubPort 2>$null
& (Join-Path $Root "scripts\stop_hub_web_daemon.ps1") -Port 3000 2>$null

Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match 'bots\.telegram' } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Host "Bot Telegram arrete (PID $($_.ProcessId))" -ForegroundColor DarkGray
    }

Remove-Item (Join-Path $Root ".telegram_bot.lock") -Force -ErrorAction SilentlyContinue
Remove-Item (Join-Path $Root ".telegram_secretary_bot.lock") -Force -ErrorAction SilentlyContinue

Write-Host "Stack arretee." -ForegroundColor Green
