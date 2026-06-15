# Cree le repo GitHub alnua-academy + labels + variables .env
# Usage: .\scripts\setup_academy.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$AcademyPath = "C:\Dev\alnua-academy"
$RepoName = "alnua-academy"

Write-Host "`n[1/5] gh auth..." -ForegroundColor Cyan
gh auth status 2>&1 | Out-Host
if ($LASTEXITCODE -ne 0) { exit 1 }

$owner = gh api user -q .login
$fullName = "$owner/$RepoName"

Write-Host "`n[2/5] Repo GitHub $fullName" -ForegroundColor Cyan
$exists = $false
try {
    gh repo view $fullName 2>$null | Out-Null
    $exists = $LASTEXITCODE -eq 0
} catch {
    $exists = $false
}

if (-not $exists) {
    $desc = "ALNUA Academy - entrainement dev_app (jamais publie)"
    gh repo create $RepoName --private --description $desc
    Write-Host "Repo cree." -ForegroundColor Green
} else {
    Write-Host "Repo existe deja." -ForegroundColor Green
}

Write-Host "`n[3/5] Clone local $AcademyPath" -ForegroundColor Cyan
if (-not (Test-Path $AcademyPath)) {
    git clone "https://github.com/$fullName.git" $AcademyPath
} else {
    Write-Host "Dossier deja present." -ForegroundColor Yellow
}

Write-Host "`n[4/5] Labels academy" -ForegroundColor Cyan
$labels = @(
    @{ name = "academy"; color = "7057FF"; desc = "Exercice ALNUA Academy" },
    @{ name = "level-1"; color = "C5DEF5"; desc = "Niveau 1 Fondations" },
    @{ name = "level-2"; color = "BFD4F2"; desc = "Niveau 2 Geoloc" },
    @{ name = "level-3"; color = "F9D0C4"; desc = "Niveau 3 Social" },
    @{ name = "level-4"; color = "FEF2C0"; desc = "Niveau 4 Integration" },
    @{ name = "agent-ready"; color = "0E8A16"; desc = "Pret pour Dev App Agent" },
    @{ name = "in-pipeline"; color = "FBCA04"; desc = "En cours" },
    @{ name = "agent-done"; color = "1D76DB"; desc = "PR creee" },
    @{ name = "agent-failed"; color = "D93F0B"; desc = "Echec pipeline" }
)
foreach ($lbl in $labels) {
    gh label create $lbl.name --repo $fullName --color $lbl.color --description $lbl.desc 2>$null
}

Write-Host "`n[5/5] .env Hub" -ForegroundColor Cyan
$envFile = Join-Path $Root ".env"
if (-not (Test-Path $envFile)) {
    Write-Host "Fichier .env absent - copier depuis .env.example" -ForegroundColor Red
    exit 1
}

function Set-EnvLine {
    param([string[]]$Arr, [string]$Name, [string]$Value)
    $pattern = "^$Name="
    $line = "$Name=$Value"
    $idx = -1
    for ($i = 0; $i -lt $Arr.Length; $i++) {
        if ($arr[$i] -match $pattern) { $idx = $i; break }
    }
    if ($idx -ge 0) {
        $Arr[$idx] = $line
    } else {
        $Arr += $line
    }
    return $Arr
}

$envRaw = [System.IO.File]::ReadAllText($envFile)
if ($envRaw.StartsWith([char]0xFEFF)) {
    $envRaw = $envRaw.Substring(1)
}
$lines = $envRaw -split "`r?`n"
$lines = Set-EnvLine $lines "GITHUB_REPO_ACADEMY" $fullName
$lines = Set-EnvLine $lines "REPO_PATH_ACADEMY" $AcademyPath
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllLines($envFile, $lines, $utf8NoBom)

Write-Host "`nTermine." -ForegroundColor Green
Write-Host "  GITHUB_REPO_ACADEMY=$fullName"
Write-Host "  REPO_PATH_ACADEMY=$AcademyPath"
Write-Host ""
Write-Host "Ensuite:"
Write-Host '  python scripts/seed_academy_issues.py --level 1 --mark-ready'
Write-Host '  Redemarrer uvicorn puis ouvrir http://localhost:3000/hub'
