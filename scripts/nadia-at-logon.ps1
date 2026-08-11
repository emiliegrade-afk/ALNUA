# Nadia — demarrage Hub + accueil au logon Windows
# Usage: .\scripts\nadia-at-logon.ps1

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Supervisor = Join-Path $Root "scripts\hub_supervisor.py"
$PortFile = Join-Path $Root "data\hub_active_port.txt"
$LogFile = Join-Path $Root "data\nadia_desktop.log"

function Write-NadiaLog([string]$Msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

function Get-HubPort {
    if (Test-Path $PortFile) {
        try { return [int](Get-Content $PortFile -Raw).Trim() } catch { }
    }
    return 8003
}

function Test-HubOnline([int]$Port) {
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 8
        return $h.service -eq "alnua-hub"
    } catch {
        return $false
    }
}

function Test-SupervisorRunning {
    $lock = Join-Path $Root "data\hub.supervisor.lock"
    if (-not (Test-Path $lock)) { return $false }
    try {
        $pid = [int](Get-Content $lock -Raw).Trim()
        return $null -ne (Get-Process -Id $pid -ErrorAction SilentlyContinue)
    } catch {
        return $false
    }
}

Write-NadiaLog "=== Nadia logon demarre ==="

if (-not (Test-SupervisorRunning)) {
    Write-NadiaLog "Supervisor absent — demarrage Hub"
    if (Test-Path $Python) {
        Start-Process `
            -FilePath $Python `
            -ArgumentList @($Supervisor, "--api-port", "8003", "--web-port", "3000") `
            -WorkingDirectory $Root `
            -WindowStyle Hidden | Out-Null
    } else {
        Write-NadiaLog "ERREUR: venv python introuvable"
    }
} else {
    Write-NadiaLog "Supervisor deja actif"
}

$port = Get-HubPort
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    if (Test-HubOnline $port) {
        $ready = $true
        break
    }
    Start-Sleep -Seconds 3
}

if ($ready) {
    Write-NadiaLog "Hub OK sur :$port"
    try {
        $boot = Invoke-RestMethod -Uri "http://127.0.0.1:$port/nadia/desktop/boot?source=windows_logon" -Method POST -TimeoutSec 15
        $msg = ($boot.greeting -split "`n")[0]
        Write-NadiaLog "Boot enregistre: $msg"
        try {
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            $template = @"
<toast>
  <visual><binding template="ToastText02">
    <text id="1">Nadia — ALNUA Hub</text>
    <text id="2">$msg</text>
  </binding></visual>
</toast>
"@
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($template)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("ALNUA Hub").Show($toast)
        } catch {
            Write-NadiaLog "Toast non disponible (normal sur certaines configs)"
        }
    } catch {
        Write-NadiaLog "Boot API echoue: $_"
    }
} else {
    Write-NadiaLog "Hub pas pret apres attente — lance Demarrer-Hub.bat manuellement"
}

# Lance Nadia Desktop (chat + éditeur) si pas déjà ouvert
$desktopPy = Join-Path $Root "nadia_desktop\main.py"
$already = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*nadia_desktop*main.py*" }
if (-not $already -and (Test-Path $Python) -and (Test-Path $desktopPy)) {
    Write-NadiaLog "Lancement Nadia Desktop UI"
    Start-Process `
        -FilePath $Python `
        -ArgumentList @($desktopPy) `
        -WorkingDirectory (Join-Path $Root "nadia_desktop") `
        -WindowStyle Normal | Out-Null
} else {
    Write-NadiaLog "Nadia Desktop deja active ou script manquant"
}
