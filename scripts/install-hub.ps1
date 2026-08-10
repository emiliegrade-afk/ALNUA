# Installe ALNUA Hub sur ce PC (venv, npm, raccourci Bureau, demarrage optionnel).
# Usage: .\scripts\install-hub.ps1 [-InstallNpm] [-SkipNpm] [-Startup]

param(
    [switch]$InstallNpm,
    [switch]$SkipNpm,
    [switch]$Startup
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$WebDir = Join-Path $Root "web"
$NodeModules = Join-Path $WebDir "node_modules"
$EnvFile = Join-Path $Root ".env"
$EnvExample = Join-Path $Root ".env.example"
$BatPath = Join-Path $Root "ALNUA Hub.bat"

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host "  Installation ALNUA Hub" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# 1. Python venv
if (-not (Test-Path $Python)) {
    Write-Host "ERREUR : environnement Python introuvable." -ForegroundColor Red
    Write-Host ""
    Write-Host "Depuis le dossier du projet, execute :" -ForegroundColor Yellow
    Write-Host "  python -m venv .venv" -ForegroundColor White
    Write-Host "  .venv\Scripts\pip install -r requirements.txt" -ForegroundColor White
    Write-Host ""
    exit 1
}
Write-Host '(OK) Python venv :' $Python -ForegroundColor Green

# 2. npm / node_modules
if (-not (Test-Path $NodeModules)) {
    if ($SkipNpm) {
        Write-Host '[!] node_modules absent (npm ignore avec -SkipNpm)' -ForegroundColor Yellow
    } elseif ($InstallNpm) {
        Write-Host "Installation npm dans web\ ..." -ForegroundColor Cyan
        Push-Location $WebDir
        try {
            npm install
            if ($LASTEXITCODE -ne 0) { throw "npm install a echoue (code $LASTEXITCODE)" }
        } finally {
            Pop-Location
        }
        Write-Host '(OK) Dependances web installees' -ForegroundColor Green
    } else {
        $answer = Read-Host "node_modules absent. Lancer npm install dans web\ ? (O/n)"
        if ($answer -eq "" -or $answer -match "^[oOyY]") {
            Push-Location $WebDir
            try {
                npm install
                if ($LASTEXITCODE -ne 0) { throw "npm install a echoue (code $LASTEXITCODE)" }
            } finally {
                Pop-Location
            }
            Write-Host '(OK) Dependances web installees' -ForegroundColor Green
        } else {
            Write-Host '[!] npm non installe - le web ne demarrera pas sans node_modules' -ForegroundColor Yellow
        }
    }
} else {
    Write-Host '(OK) Dependances web (node_modules)' -ForegroundColor Green
}

# 3. .env
if (-not (Test-Path $EnvFile)) {
    Write-Host ""
    Write-Host "ATTENTION : fichier .env absent." -ForegroundColor Yellow
    if (Test-Path $EnvExample) {
        Write-Host "Copie .env.example vers .env et remplis au minimum :" -ForegroundColor Yellow
        Write-Host "  SUPABASE_URL, SUPABASE_KEY, OPENROUTER_API_KEY, HUB_API_KEY" -ForegroundColor White
        Write-Host "Modele : $EnvExample" -ForegroundColor DarkGray
    } else {
        Write-Host "Cree un fichier .env avec tes cles (voir la doc)." -ForegroundColor Yellow
    }
} else {
    Write-Host '(OK) Fichier .env present' -ForegroundColor Green
}

# 4. Raccourci Bureau -> ALNUA Hub.bat
if (-not (Test-Path $BatPath)) {
    Write-Host "ERREUR : $BatPath introuvable" -ForegroundColor Red
    exit 1
}

$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "ALNUA Hub.lnk"
$IconCandidates = @(
    (Join-Path $Root "assets\alnua-hub.ico"),
    (Join-Path $Root "web\public\icon-512.png")
)

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($ShortcutPath)
$shortcut.TargetPath = $BatPath
$shortcut.WorkingDirectory = $Root
$shortcut.Description = 'Cockpit ALNUA - entreprise virtuelle'
foreach ($icon in $IconCandidates) {
    if (Test-Path $icon) {
        $shortcut.IconLocation = "$icon,0"
        break
    }
}
$shortcut.Save()
Write-Host '(OK) Raccourci Bureau :' $ShortcutPath -ForegroundColor Green

# 5. Demarrage a la connexion (optionnel)
if ($Startup) {
    $startupScript = Join-Path $Root "scripts\install_hub_daemon_startup.ps1"
    & $startupScript
}

# 6. Instructions finales
Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Installation terminee" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Comment demarrer :" -ForegroundColor Cyan
Write-Host "  1. Double-clic sur le raccourci Bureau ""ALNUA Hub""" -ForegroundColor White
Write-Host "     ou lance ""ALNUA Hub.bat"" a la racine du projet" -ForegroundColor White
Write-Host "  2. Le navigateur s'ouvre sur http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Arreter le Hub :" -ForegroundColor Cyan
Write-Host "  Double-clic sur ""Arreter ALNUA Hub.bat""" -ForegroundColor White
Write-Host ""
Write-Host "Verifier l'etat :" -ForegroundColor Cyan
Write-Host "  .\scripts\hub-status.ps1" -ForegroundColor White
Write-Host ""
if (-not $Startup) {
    Write-Host "Demarrage automatique a la connexion (H24) :" -ForegroundColor Cyan
    Write-Host "  .\scripts\install-hub.ps1 -Startup" -ForegroundColor White
    Write-Host "  ou .\scripts\install_hub_daemon_startup.ps1" -ForegroundColor White
    Write-Host ""
}
