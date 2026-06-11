# Lie le depot local ALUNA_HUB a GitHub et remplit .env
# Usage (PowerShell) :
#   1. gh auth login
#   2. .\scripts\link_github.ps1
#   3. Redemarrer l'API / le bot Telegram

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

Write-Host "`n[1/4] Verification gh CLI..." -ForegroundColor Cyan
gh auth status 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) {
    Write-Host "Lance d'abord : gh auth login" -ForegroundColor Yellow
    exit 1
}

$owner = gh api user -q .login
$repoName = "ALNUA"
$fullName = "$owner/$repoName"

Write-Host "`n[2/4] Depot GitHub cible : $fullName" -ForegroundColor Cyan

$repoExists = $false
try {
    gh repo view $fullName 2>$null | Out-Null
    $repoExists = $LASTEXITCODE -eq 0
} catch {
    $repoExists = $false
}

if (-not $repoExists) {
    Write-Host "Creation du repo GitHub $fullName ..." -ForegroundColor Yellow
    gh repo create $repoName --private --source=. --remote=origin --description "ALNUA Hub — agents IA, bots, API"
} else {
    Write-Host "Repo existant — liaison remote origin" -ForegroundColor Green
    $remote = git remote get-url origin 2>$null
    if (-not $remote) {
        git remote add origin "https://github.com/$fullName.git"
    }
}

$token = gh auth token

Write-Host "`n[3/4] Mise a jour .env ..." -ForegroundColor Cyan
$envFile = Join-Path $Root ".env"
$lines = Get-Content $envFile

function Update-EnvLine([string[]]$arr, [string]$name, [string]$value) {
    $pattern = "^$name="
    $line = "$name=$value"
    $idx = -1
    for ($i = 0; $i -lt $arr.Length; $i++) {
        if ($arr[$i] -match $pattern) { $idx = $i; break }
    }
    if ($idx -ge 0) { $arr[$idx] = $line } else { $arr += $line }
    return $arr
}

$lines = Update-EnvLine $lines "GITHUB_TOKEN" $token
$lines = Update-EnvLine $lines "GITHUB_REPO" $fullName
$lines = Update-EnvLine $lines "HUB_REPO_PATH" $Root
$lines | Set-Content $envFile -Encoding utf8

Write-Host "`n[4/4] Verification API GitHub..." -ForegroundColor Cyan
.venv\Scripts\python.exe scripts\check_pipeline_connections.py

Write-Host "`n[Labels] Creation des labels pipeline..." -ForegroundColor Cyan
$labels = @(
    @{ name = "agent-ready"; color = "0E8A16"; desc = "Pret pour le Dev App Agent" },
    @{ name = "in-pipeline"; color = "FBCA04"; desc = "En cours de traitement" },
    @{ name = "agent-done"; color = "1D76DB"; desc = "PR creee" },
    @{ name = "agent-failed"; color = "D93F0B"; desc = "Pipeline echoue" },
    @{ name = "auto-generated"; color = "5319E7"; desc = "PR generee automatiquement" }
)
foreach ($lbl in $labels) {
    gh label create $lbl.name --repo $fullName --color $lbl.color --description $lbl.desc 2>$null
}

Write-Host "`nTermine. GITHUB_REPO=$fullName" -ForegroundColor Green
Write-Host "Redemarre le bot Telegram et l'API, puis teste /pipeline" -ForegroundColor Yellow
