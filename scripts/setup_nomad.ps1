# Clone le repo NUAWAY (nomad) + configure REPO_PATH_NOMAD dans .env
# Usage: .\scripts\setup_nomad.ps1 [-ClonePath C:\Dev\NUAWAY]

param(
    [string]$ClonePath = "C:\Dev\NUAWAY"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $Root ".env"

function Set-EnvLine {
    param([string]$Key, [string]$Value)
    $pattern = "^\s*$([regex]::Escape($Key))\s*="
    $line = "$Key=$Value"
    if (-not (Test-Path $EnvFile)) {
        Copy-Item (Join-Path $Root ".env.example") $EnvFile
    }
    $content = Get-Content $EnvFile -Raw -Encoding UTF8
    if ($content -match "(?m)^\s*$([regex]::Escape($Key))\s*=") {
        $content = [regex]::Replace($content, "(?m)^\s*$([regex]::Escape($Key))\s*=.*$", $line)
    } else {
        $content = $content.TrimEnd() + "`r`n$line`r`n"
    }
    [System.IO.File]::WriteAllText($EnvFile, $content, [System.Text.UTF8Encoding]::new($false))
}

Write-Host "`n[1/4] gh auth..." -ForegroundColor Cyan
gh auth status 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { exit 1 }

$owner = gh api user -q .login
$repoFromEnv = $null
if (Test-Path $EnvFile) {
    $match = Select-String -Path $EnvFile -Pattern '^\s*GITHUB_REPO_NOMAD\s*=\s*(.+)$' | Select-Object -First 1
    if ($match) { $repoFromEnv = $match.Matches[0].Groups[1].Value.Trim() }
}
$fullName = if ($repoFromEnv) { $repoFromEnv } else { "$owner/NUAWAY" }

Write-Host "`n[2/4] Clone $fullName -> $ClonePath" -ForegroundColor Cyan
if (Test-Path $ClonePath) {
    Write-Host "Dossier existe deja." -ForegroundColor Yellow
} else {
    New-Item -ItemType Directory -Path (Split-Path $ClonePath -Parent) -Force | Out-Null
    gh repo clone $fullName $ClonePath
}

Write-Host "`n[3/4] Mise a jour .env" -ForegroundColor Cyan
Set-EnvLine "GITHUB_REPO_NOMAD" $fullName
Set-EnvLine "REPO_PATH_NOMAD" $ClonePath

Write-Host "`n[4/4] Verification" -ForegroundColor Cyan
if (Test-Path $ClonePath) {
    Write-Host "OK — $ClonePath" -ForegroundColor Green
} else {
    Write-Host "ERREUR — clone introuvable" -ForegroundColor Red
    exit 1
}

Write-Host "`nRelance l'API : .\scripts\restart_hub_api.ps1" -ForegroundColor Cyan
Write-Host "Audit readiness : python scripts/nuaway_readiness_audit.py`n" -ForegroundColor Cyan
