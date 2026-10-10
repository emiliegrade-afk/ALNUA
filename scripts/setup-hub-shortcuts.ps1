# Cree 2-3 raccourcis Bureau clairs (pas une douzaine de .bat).
param(
    [switch]$DesktopOnly,
    [switch]$ProjectOnly,
    [switch]$CleanOld
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
. (Join-Path $PSScriptRoot "alnua-shortcut-identity.ps1")
$IconPath = Get-AlnuaHubIconPath -Root $Root
$Desktop = [Environment]::GetFolderPath("Desktop")
$VbsPath = Join-Path $Root "scripts\launch-hub-silent.vbs"
$StartTarget = if (Test-Path $VbsPath) { $VbsPath } else { Join-Path $Root "ALNUA Hub.bat" }

$launchers = @(
    @{
        Name = "ALNUA Hub"
        Target = $StartTarget
        Description = "Demarrer ALNUA Hub (sans fenetre CMD)"
    },
    @{
        Name = "Arreter ALNUA Hub"
        Target = Join-Path $Root "Arreter ALNUA Hub.bat"
        Description = "Arreter toute la stack ALNUA"
    },
    @{
        Name = "Spark"
        Target = $(
            $sparkVbs = Join-Path $Root "scripts\launch-spark-silent.vbs"
            if (Test-Path $sparkVbs) { $sparkVbs }
            elseif (Test-Path (Join-Path $Root "scripts\launch-desk-silent.vbs")) {
                Join-Path $Root "scripts\launch-desk-silent.vbs"
            } else { Join-Path $Root "Spark.bat" }
        )
        Description = "Spark - assistante desktop ALNUA (Nadia)"
    },
    @{
        Name = "Nadia Live"
        Target = Join-Path $Root "Nadia Live.bat"
        Description = "Nadia Live - voix temps reel + taches (/live)"
    }
)

$oldNames = @(
    "ALNUA Hub (demarrage complet)",
    "Ouvrir ALNUA Hub",
    "Reparer Hub Web",
    "Relancer agents",
    "Relancer Hub",
    "Installer raccourcis ALNUA",
    "Nadia Desktop",
    "ALNUA Desk"
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

    # Windows ignore souvent IconLocation si Target = .bat/.vbs.
    # Passer par un .exe (wscript/cmd) force l'icone custom (X rond).
    $ext = [System.IO.Path]::GetExtension($TargetPath).ToLowerInvariant()
    $exeTarget = $TargetPath
    $arguments = ""
    if ($ext -eq ".vbs") {
        $exeTarget = Join-Path $env:SystemRoot "System32\wscript.exe"
        $arguments = "//nologo `"$TargetPath`""
    }
    elseif ($ext -eq ".bat" -or $ext -eq ".cmd") {
        $exeTarget = Join-Path $env:SystemRoot "System32\cmd.exe"
        $arguments = "/c `"$TargetPath`""
    }

    $wsh = New-Object -ComObject WScript.Shell
    $shortcut = $wsh.CreateShortcut($ShortcutPath)
    $shortcut.TargetPath = $exeTarget
    $shortcut.Arguments = $arguments
    $shortcut.WorkingDirectory = $Root
    $shortcut.Description = $Description
    if (Test-Path $IconPath) {
        $shortcut.IconLocation = "$IconPath,0"
    }
    $shortcut.Save()
}

if ($CleanOld -or -not $ProjectOnly) {
    foreach ($name in $oldNames) {
        $old = Join-Path $Desktop "$name.lnk"
        if (Test-Path $old) {
            Remove-Item $old -Force
            Write-Host "Supprime (ancien) : $old" -ForegroundColor DarkGray
        }
    }
}

if (-not (Test-Path $IconPath)) {
    Write-Host "Icone introuvable: $IconPath (raccourcis sans icone custom)" -ForegroundColor Yellow
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
Write-Host "Raccourcis ALNUA :" -ForegroundColor Green
foreach ($path in $created) {
    Write-Host "  $path" -ForegroundColor Cyan
}
Write-Host ""
Write-Host "Au quotidien : double-clic ""ALNUA Hub"" sur le Bureau." -ForegroundColor Yellow
