# Etat du Hub ALNUA (API, web, supervisor, bots). Exit 0 si API saine.
param(
    [int]$ApiPort = 8003,
    [int]$WebPort = 3000
)

$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $PSScriptRoot
$apiOk = $false
$webOk = $false

function Write-Line([string]$Label, [string]$Value, [string]$Color = "White") {
    Write-Host ("  {0,-18} " -f $Label) -NoNewline
    Write-Host $Value -ForegroundColor $Color
}

Write-Host ""
Write-Host 'ALNUA Hub - etat' -ForegroundColor Yellow
Write-Host ""

# API health
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/health" -TimeoutSec 8
    if ($health.service -eq "alnua-hub") {
        $apiOk = $true
        Write-Line "API ($ApiPort)" 'OK - alnua-hub' "Green"
    } else {
        Write-Line "API ($ApiPort)" "Reponse inattendue" "Yellow"
    }
} catch {
    Write-Line "API ($ApiPort)" "Hors ligne ou injoignable" "Red"
}

# Web
try {
    $web = Invoke-WebRequest -Uri "http://127.0.0.1:$WebPort" -UseBasicParsing -TimeoutSec 8
    if ($web.StatusCode -eq 200) {
        $webOk = $true
        Write-Line "Web ($WebPort)" "OK" "Green"
    } else {
        Write-Line "Web ($WebPort)" "HTTP $($web.StatusCode)" "Yellow"
    }
} catch {
    Write-Line "Web ($WebPort)" "Hors ligne ou injoignable" "Red"
}

# Supervisor lock / state
$lockPath = Join-Path $Root "data\hub.supervisor.lock"
$statePath = Join-Path $Root "data\hub.supervisor.json"

if (Test-Path $lockPath) {
    $lockPid = (Get-Content $lockPath -Raw).Trim()
    $alive = $false
    if ($lockPid -match '^\d+$') {
        $alive = $null -ne (Get-Process -Id ([int]$lockPid) -ErrorAction SilentlyContinue)
    }
    $color = if ($alive) { "Green" } else { "Yellow" }
    $suffix = if ($alive) { " (actif)" } else { " (PID mort ?)" }
    Write-Line "Supervisor lock" "PID $lockPid$suffix" $color
} else {
    Write-Line "Supervisor lock" "absent" "DarkGray"
}

if (Test-Path $statePath) {
    try {
        $state = Get-Content $statePath -Raw | ConvertFrom-Json
        $parts = @()
        if ($state.api_pid) { $parts += "api PID $($state.api_pid)" }
        if ($state.web_pid) { $parts += "web PID $($state.web_pid)" }
        if ($state.updated_at) { $parts += "maj $($state.updated_at)" }
        $summary = if ($parts.Count -gt 0) { ($parts -join ", ") } else { "fichier present" }
        Write-Line "Supervisor etat" $summary "Cyan"
    } catch {
        Write-Line "Supervisor etat" "fichier illisible" "Yellow"
    }
} else {
    Write-Line "Supervisor etat" 'pas de hub.supervisor.json' "DarkGray"
}

# Bot locks
$botLocks = @(
    @{ Label = "Nadia (Telegram)"; Path = ".telegram_secretary_bot.lock" },
    @{ Label = "Aria (Telegram)"; Path = ".telegram_bot.lock" }
)
foreach ($bot in $botLocks) {
    $path = Join-Path $Root $bot.Path
    if (Test-Path $path) {
        $botPid = (Get-Content $path -Raw).Trim()
        $alive = $false
        if ($botPid -match '^\d+$') {
            $alive = $null -ne (Get-Process -Id ([int]$botPid) -ErrorAction SilentlyContinue)
        }
        $color = if ($alive) { "Green" } else { "Yellow" }
        Write-Line $bot.Label "PID $botPid" $color
    } else {
        Write-Line $bot.Label "arrete" "DarkGray"
    }
}

Write-Host ""
if ($apiOk) {
    Write-Host "Resultat : Hub API operationnelle." -ForegroundColor Green
    exit 0
}
Write-Host 'Resultat : Hub API indisponible - lance ALNUA Hub.bat ou consulte data/hub_supervisor.log' -ForegroundColor Red
exit 1
