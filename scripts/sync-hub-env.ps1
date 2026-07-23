# Sync web/.env.local with root .env + data/hub_active_port.txt
# Usage: .\scripts\sync-hub-env.ps1 [-Port 0]

param([int]$Port = 0)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$WebEnv = Join-Path $Root "web\.env.local"
$RootEnv = Join-Path $Root ".env"

if ($Port -le 0) {
    $Port = [int](& (Join-Path $Root "scripts\get-hub-port.ps1"))
}

function Read-EnvValue([string]$File, [string]$Name) {
    if (-not (Test-Path $File)) { return "" }
    $line = Get-Content $File | Where-Object { $_ -match "^$Name=" } | Select-Object -First 1
    if ($line) { return $line.Split('=', 2)[1].Trim() }
    return ""
}

function Set-EnvLine([string[]]$Lines, [string]$Name, [string]$Value) {
    $pattern = "^$Name="
    $line = "$Name=$Value"
    $idx = -1
    for ($i = 0; $i -lt $Lines.Length; $i++) {
        if ($Lines[$i] -match $pattern) { $idx = $i; break }
    }
    if ($idx -ge 0) { $Lines[$idx] = $line } else { $Lines += $line }
    return $Lines
}

$hubKey = Read-EnvValue $RootEnv "HUB_API_KEY"
$backendUrl = "http://127.0.0.1:$Port"

if (Test-Path $WebEnv) {
    $lines = Get-Content $WebEnv
} else {
    $example = Join-Path $Root "web\.env.example"
    $lines = if (Test-Path $example) { Get-Content $example } else { @() }
}

$lines = Set-EnvLine $lines "HUB_API_BACKEND_URL" $backendUrl
if ($hubKey) {
    $lines = Set-EnvLine $lines "HUB_API_KEY" $hubKey
}

$lines | Set-Content $WebEnv -Encoding utf8
Set-Content -Path (Join-Path $Root "data\hub_active_port.txt") -Value $Port -Encoding ascii -NoNewline

Write-Host "Sync OK: HUB_API_BACKEND_URL=$backendUrl" -ForegroundColor Green
