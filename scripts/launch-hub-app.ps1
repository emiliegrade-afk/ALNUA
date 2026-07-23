# Ouvre ALNUA Hub en fenetre application (sans barre navigateur).
param(
    [string]$Url = "http://localhost:3000",
    [int]$WaitSeconds = 0,
    [int]$MaxWait = 45
)

$ErrorActionPreference = "SilentlyContinue"

function Test-HubWeb {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 4
        return $r.StatusCode -eq 200
    } catch {
        return $false
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
    Write-Host "Hub web pas pret sur $Url" -ForegroundColor Yellow
    Write-Host "Lance ALNUA Hub.bat pour tout demarrer." -ForegroundColor Yellow
    exit 1
}

$candidates = @(
    @{ Name = "Edge"; Path = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe" },
    @{ Name = "Edge"; Path = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe" },
    @{ Name = "Chrome"; Path = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe" },
    @{ Name = "Chrome"; Path = "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe" }
)

foreach ($browser in $candidates) {
    if (Test-Path $browser.Path) {
        # Fenêtre navigateur normale (le mode --app casse souvent le layout Hub).
        Start-Process $browser.Path -ArgumentList @(
            $Url,
            "--new-window"
        )
        Write-Host "ALNUA Hub ouvert via $($browser.Name)" -ForegroundColor Green
        exit 0
    }
}

Start-Process $Url
Write-Host "ALNUA Hub ouvert dans le navigateur" -ForegroundColor Green
