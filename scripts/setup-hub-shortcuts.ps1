# Cree les raccourcis ALNUA Hub avec le logo (Windows ne peut pas iconiser un .bat directement).
param(
    [switch]$DesktopOnly,
    [switch]$ProjectOnly
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$IconPath = Join-Path $Root "assets\alnua-hub.ico"
$Desktop = [Environment]::GetFolderPath("Desktop")

$launchers = @(
    @{
        Name = "ALNUA Hub"
        Target = Join-Path $Root "Ouvrir-Hub.bat"
        Description = "Ouvrir le cockpit ALNUA"
    },
    @{
        Name = "ALNUA Hub (demarrage complet)"
        Target = Join-Path $Root "Demarrer-Hub.bat"
        Description = "Demarrer API, web, bots Telegram"
    },
    @{
        Name = "Arreter ALNUA Hub"
        Target = Join-Path $Root "Arreter-Hub.bat"
        Description = "Arreter toute la stack ALNUA"
    },
    @{
        Name = "Reparer Hub Web"
        Target = Join-Path $Root "Reparer Hub Web.bat"
        Description = "Reparer l interface web (cache Next.js)"
    },
    @{
        Name = "Relancer agents"
        Target = Join-Path $Root "Relancer agents.bat"
        Description = "Remettre Théo et le pipeline Academy au travail"
    }
)

function New-HubShortcut {
    param(
        [string]$ShortcutPath,
        [string]$TargetPath,
        [string]$Description
    )

    if (-not (Test-Path $TargetPath)) {
        Write-Host "Ignore: cible introuvable $TargetPath" -ForegroundColor DarkGray
        return
    }

    $dir = Split-Path $ShortcutPath -Parent
    if ($dir -and -not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }

    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $TargetPath
    $shortcut.WorkingDirectory = $Root
    $shortcut.Description = $Description
    if (Test-Path $IconPath) {
        $shortcut.IconLocation = "$IconPath,0"
    }
    $shortcut.Save()
}

if (-not (Test-Path $IconPath)) {
    Write-Host "Icone introuvable: $IconPath" -ForegroundColor Red
    Write-Host "Lance: .venv\Scripts\python.exe scripts\build_hub_icon.py" -ForegroundColor Yellow
    exit 1
}

$created = @()

if (-not $ProjectOnly) {
    foreach ($item in $launchers) {
        $path = Join-Path $Desktop "$($item.Name).lnk"
        New-HubShortcut -ShortcutPath $path -TargetPath $item.Target -Description $item.Description
        $created += $path
    }
}

if (-not $DesktopOnly) {
    foreach ($item in $launchers) {
        $path = Join-Path $Root "$($item.Name).lnk"
        New-HubShortcut -ShortcutPath $path -TargetPath $item.Target -Description $item.Description
        $created += $path
    }
}

Write-Host ""
Write-Host "Raccourcis ALNUA crees avec le logo:" -ForegroundColor Green
foreach ($path in $created) {
    Write-Host "  $path" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "Astuce: utilise les fichiers .lnk (logo ALNUA), pas les .bat." -ForegroundColor Yellow
