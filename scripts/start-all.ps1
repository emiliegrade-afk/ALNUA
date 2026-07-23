# ALNUA Hub - demarre toute la stack locale en une commande.
# Usage: .\scripts\start-all.ps1
# Arret: .\scripts\stop-all.ps1

param(
    [int]$HubPort = 8003,
    [switch]$SkipWeb,
    [switch]$SkipBots,
    [switch]$SkipWake,
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Supervisor = Join-Path $Root "scripts\hub_supervisor.py"

function Write-Step([string]$Msg) {
    Write-Host ""
    Write-Host "==> $Msg" -ForegroundColor Cyan
}

function Test-HubHealth([int]$Port) {
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 10
        return $h.service -eq "alnua-hub"
    } catch {
        return $false
    }
}

function Start-BotIfNeeded([string]$Module, [string]$LockName) {
    $lock = Join-Path $Root $LockName
    if (Test-Path $lock) {
        try {
            $oldPid = [int](Get-Content $lock -Raw).Trim()
            if (Get-Process -Id $oldPid -ErrorAction SilentlyContinue) {
                Write-Host "  deja actif (PID $oldPid)" -ForegroundColor Green
                return
            }
        } catch { }
        Remove-Item $lock -Force -ErrorAction SilentlyContinue
    }
    $running = Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match $Module }
    if ($running) {
        Write-Host "  deja actif" -ForegroundColor Green
        return
    }
    $scriptMap = @{
        "bots.telegram_secretary_bot" = "start_secretary_bot.ps1"
        "bots.telegram_bot"           = "start_coo_bot.ps1"
    }
    $scriptName = $scriptMap[$Module]
    if (-not $scriptName) { return }
    $scriptPath = Join-Path $Root "scripts\$scriptName"
    Start-Process powershell.exe -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-WindowStyle", "Hidden", "-File", $scriptPath
    ) -WorkingDirectory $Root
    Write-Host "  demarre" -ForegroundColor Green
}

Write-Host "ALNUA Hub - demarrage (supervisor v2)" -ForegroundColor Yellow

if (-not (Test-Path $Python)) {
    Write-Host "venv introuvable: $Python" -ForegroundColor Red
    exit 1
}

Write-Step "Supervisor Hub (API :$HubPort + Web :3000)"

if (Test-HubHealth $HubPort) {
    Write-Host "  deja actif -> http://127.0.0.1:$HubPort" -ForegroundColor Green
} else {
    & $Python $Supervisor stop 2>$null
    Start-Sleep -Seconds 2
    $runArgs = @(
        $Supervisor, "run",
        "--api-port", "$HubPort",
        "--web-port", "3000"
    )
    if ($SkipWeb) { $runArgs += "--skip-web" }
    Start-Process -FilePath $Python -ArgumentList $runArgs -WorkingDirectory $Root -WindowStyle Hidden
    Write-Host "  Supervisor lance en arriere-plan" -ForegroundColor Green
}

$hubOk = $false
for ($i = 0; $i -lt 45; $i++) {
    Start-Sleep -Seconds 2
    if (Test-HubHealth $HubPort) {
        $hubOk = $true
        break
    }
}
if ($hubOk) {
    Write-Host "  API OK -> http://127.0.0.1:$HubPort" -ForegroundColor Green
} else {
    Write-Host "  API en cours - le supervisor continue (data\hub_supervisor.log)" -ForegroundColor Yellow
}

if (-not $SkipWeb) {
    $webOk = $false
    for ($i = 0; $i -lt 25; $i++) {
        Start-Sleep -Seconds 2
        try {
            $null = Invoke-WebRequest -Uri "http://localhost:3000" -UseBasicParsing -TimeoutSec 12
            $webOk = $true
            break
        } catch { }
    }
    if ($webOk) {
        Write-Host "  Web OK -> http://localhost:3000" -ForegroundColor Green
    } else {
        Write-Host "  Web en cours (~30s) -> http://localhost:3000" -ForegroundColor Yellow
    }
}

if (-not $SkipBots) {
    Write-Step "Nadia (Telegram)"
    Start-BotIfNeeded "bots.telegram_secretary_bot" ".telegram_secretary_bot.lock"
    Write-Step "Aria (Telegram COO)"
    Start-BotIfNeeded "bots.telegram_bot" ".telegram_bot.lock"
}

if (-not $SkipWake) {
    Write-Step "Pipeline Academy"
    & (Join-Path $Root "scripts\wake-agents.ps1") 2>&1 | Select-Object -Last 3
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host " Hub UI   : http://localhost:3000" -ForegroundColor White
Write-Host " Hub API  : http://127.0.0.1:$HubPort" -ForegroundColor White
Write-Host " Logs     : data\hub_supervisor.log" -ForegroundColor DarkGray
Write-Host " Arret    : Arreter-Hub.bat" -ForegroundColor DarkGray
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

if ($OpenBrowser) {
    $launchScript = Join-Path $Root "scripts\launch-hub-app.ps1"
    & $launchScript -WaitSeconds 25 -MaxWait 90
}
