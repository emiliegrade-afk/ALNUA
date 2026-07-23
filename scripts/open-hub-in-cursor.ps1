# Ouvre ALNUA Hub dans le Simple Browser integre de Cursor/VS Code.
param(
    [string]$Path = "/",
    [int]$WebPort = 3000
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$PortFile = Join-Path $Root "data\hub_active_port.txt"
$ApiPort = $WebPort

try {
    $webState = Get-Content (Join-Path $Root "data\hub.supervisor.json") -Raw | ConvertFrom-Json
    if ($webState.web_port) { $WebPort = [int]$webState.web_port }
} catch {
    # ignore
}

$hubUrl = "http://127.0.0.1:$WebPort$Path"
$simpleUrl = "vscode://vscode/simple-browser?url=$([uri]::EscapeDataString($hubUrl))"

try {
    $r = Invoke-WebRequest -Uri $hubUrl -UseBasicParsing -TimeoutSec 6
    if ($r.StatusCode -ne 200) {
        Write-Host "Hub web repond $($r.StatusCode) sur $hubUrl" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Hub web pas pret sur $hubUrl" -ForegroundColor Yellow
    Write-Host "Lance scripts\restart-hub.ps1 puis reessaie." -ForegroundColor Yellow
    exit 1
}

$cli = $null
foreach ($name in @("cursor", "code")) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) {
        $cli = $cmd.Source
        break
    }
}

if (-not $cli) {
    Write-Host "CLI Cursor/VS Code introuvable." -ForegroundColor Red
    Write-Host "Dans Cursor: Ctrl+Shift+P -> Simple Browser: Show -> $hubUrl" -ForegroundColor Cyan
    exit 1
}

Start-Process $cli -ArgumentList @("--open-url", $simpleUrl)
Write-Host "Hub ouvert dans Cursor: $hubUrl" -ForegroundColor Green
