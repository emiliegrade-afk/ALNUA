# Ouvre ALNUA Hub dans ALNUAHub.exe (icone X dans la barre des taches).
# Plus Edge --app : Windows affiche toujours le logo Edge pour ce process.
param(
    [string]$Url = "http://localhost:3000/",
    [int]$WaitSeconds = 0,
    [int]$MaxWait = 90
)

$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $PSScriptRoot
$Exe = Join-Path $Root "bin\ALNUAHub.exe"
$Build = Join-Path $PSScriptRoot "build-hub-window.ps1"
. (Join-Path $PSScriptRoot "alnua-shortcut-identity.ps1")

function Test-HubWeb {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4
        return $r.StatusCode -eq 200
    } catch {
        return $false
    }
}

function Stop-HubEdgeApp {
    Get-CimInstance Win32_Process -Filter "Name='msedge.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*hub-app-profile*" } |
        ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        }
}

if ($WaitSeconds -gt 0) {
    Start-Sleep -Seconds $WaitSeconds
}

$elapsed = 0
while (-not (Test-HubWeb) -and $elapsed -lt $MaxWait) {
    Start-Sleep -Seconds 2
    $elapsed += 2
}

if (-not (Test-HubWeb)) {
    $log = Join-Path $Root "data\hub_web.log"
    Add-Content -Path $log -Value "$(Get-Date -Format o) launch-hub-app: web pas pret sur $Url"
    exit 1
}

if (-not (Test-Path $Exe)) {
    $ErrorActionPreference = "Stop"
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $Build
    if (-not (Test-Path $Exe)) { exit 1 }
}

Stop-HubEdgeApp

$IconPath = Get-AlnuaHubIconPath -Root $Root
$lnk = Install-AlnuaHubWindowShortcut -Root $Root -BrowserPath $Exe `
    -Arguments "`"$Url`"" -AppId "ALNUA.Hub" -IconPath $IconPath

Start-Process -FilePath $Exe -ArgumentList $Url -WorkingDirectory (Split-Path $Exe) | Out-Null
exit 0
