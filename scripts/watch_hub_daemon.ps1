# Surveille le Hub API : process en arriere-plan + health checks (detecte les zombies).
# Usage: .\scripts\watch_hub_daemon.ps1 [-Port 8003]

param([int]$Port = 8003)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$LogDir = Join-Path $Root "data"
$LogFile = Join-Path $LogDir "hub_api.log"
$WatchPidFile = Join-Path $LogDir "hub_watch.pid"
$ApiPidFile = Join-Path $LogDir "hub_api.pid"
$ActivePortFile = Join-Path $LogDir "hub_active_port.txt"

if (-not (Test-Path $Python)) {
    Write-Host "venv introuvable: $Python" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$PID | Out-File -FilePath $WatchPidFile -Encoding ascii -NoNewline

function Write-Log([string]$Msg) {
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Msg
    Add-Content -Path $LogFile -Value $line -Encoding utf8
}

function Write-ActivePort([int]$P) {
    [System.IO.File]::WriteAllText($ActivePortFile, "$P")
}

function Get-HubApiKey() {
    $envFile = Join-Path $Root ".env"
    if (-not (Test-Path $envFile)) { return "" }
    $line = Get-Content $envFile | Where-Object { $_ -match '^HUB_API_KEY=' } | Select-Object -First 1
    if ($line) { return $line.Split('=', 2)[1].Trim() }
    return ""
}

function Test-HubAlive([int]$P) {
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$P/health" -TimeoutSec 15
        return $r.service -eq "alnua-hub"
    } catch {
        return $false
    }
}

function Clear-PortListeners([int]$P) {
    Get-NetTCPConnection -LocalPort $P -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            $procId = $_.OwningProcess
            if ($procId -gt 0) {
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                Write-Log "Port $P libere (PID $procId)"
            }
        }
}

function Stop-UvicornChild([System.Diagnostics.Process]$Proc) {
    if ($null -eq $Proc) { return }
    if (-not $Proc.HasExited) {
        try {
            Stop-Process -Id $Proc.Id -Force -ErrorAction SilentlyContinue
            Write-Log "uvicorn arrete (PID $($Proc.Id))"
        } catch {
            Write-Log "Echec arret uvicorn PID $($Proc.Id): $_"
        }
    }
}

function Start-UvicornChild([int]$P) {
    $args = @(
        "-m", "uvicorn", "api.main:app",
        "--host", "127.0.0.1", "--port", "$P",
        "--log-level", "info", "--limit-concurrency", "80"
    )
    return Start-Process `
        -FilePath $Python `
        -ArgumentList $args `
        -WorkingDirectory $Root `
        -PassThru `
        -WindowStyle Hidden
}

Write-Log "=== Hub watchdog demarre (PID $PID, port $Port) ==="
Set-Location $Root

$pathExtras = @(
    "$env:ProgramFiles\Git\cmd",
    "$env:ProgramFiles\GitHub CLI",
    "$env:ProgramFiles\nodejs",
    "$env:APPDATA\npm"
) | Where-Object { Test-Path $_ }
if ($pathExtras.Count -gt 0) {
    $env:Path = ($pathExtras -join ';') + ';' + $env:Path
}

$activePort = $Port
$uvicornProc = $null
$healthFailTicks = 0
$lastSlowLogAt = [datetime]::MinValue

while ($true) {
    if ($null -ne $uvicornProc -and $uvicornProc.HasExited) {
        Write-Log "uvicorn termine (exit=$($uvicornProc.ExitCode)) - redemarrage"
        $uvicornProc = $null
        Remove-Item $ApiPidFile -Force -ErrorAction SilentlyContinue
        $healthFailTicks = 0
    }

    if (Test-HubAlive $activePort) {
        Write-ActivePort $activePort
        $healthFailTicks = 0
        if ($null -eq $uvicornProc) {
            Start-Sleep -Seconds 25
            continue
        }
        Start-Sleep -Seconds 20
        continue
    }

    $onPort = Get-NetTCPConnection -LocalPort $activePort -State Listen -ErrorAction SilentlyContinue
    $procAlive = $null -ne $uvicornProc -and -not $uvicornProc.HasExited

    # Orphelin : port occupe mais pas notre process - liberer apres 3 echecs health
    if ($onPort -and -not $procAlive -and $healthFailTicks -ge 3) {
        Write-Log "Port $activePort occupe sans process supervise - nettoyage"
        Clear-PortListeners $activePort
        $healthFailTicks = 0
        Start-Sleep -Seconds 2
        continue
    }

    # API occupee ou bloquee : attendre, puis recycler si trop long
    if ($onPort -or $procAlive) {
        $healthFailTicks++
        $now = Get-Date
        if (($now - $lastSlowLogAt).TotalSeconds -ge 120) {
            Write-Log "Hub lent sur :$activePort (tick $healthFailTicks) - attente sans kill"
            $lastSlowLogAt = $now
        }
        if ($healthFailTicks -ge 12) {
            Write-Log "Hub bloque >4min sur :$activePort - recycle force"
            Stop-UvicornChild $uvicornProc
            $uvicornProc = $null
            Clear-PortListeners $activePort
            Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -match 'uvicorn api\.main' } |
                ForEach-Object {
                    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                }
            Remove-Item $ApiPidFile -Force -ErrorAction SilentlyContinue
            $healthFailTicks = 0
            Start-Sleep -Seconds 3
        } else {
            Start-Sleep -Seconds 20
        }
        continue
    }

    # Port libre : demarrer ou redemarrer uvicorn
    $healthFailTicks = 0
    Write-Log "Demarrage uvicorn sur :$activePort"
    try {
        $uvicornProc = Start-UvicornChild $activePort
        $uvicornProc.Id | Out-File -FilePath $ApiPidFile -Encoding ascii -NoNewline
        Write-ActivePort $activePort
    } catch {
        Write-Log "ERREUR lancement: $_"
        $uvicornProc = $null
        foreach ($alt in @(8003, 8002, 8001)) {
            if ($alt -eq $activePort) { continue }
            Write-Log "Essai port alternatif $alt"
            $activePort = $alt
            break
        }
        Start-Sleep -Seconds 5
        continue
    }

    $ready = $false
    for ($i = 0; $i -lt 50; $i++) {
        if ($null -ne $uvicornProc -and $uvicornProc.HasExited) { break }
        if (Test-HubAlive $activePort) {
            $ready = $true
            Write-Log "Hub pret sur :$activePort (apres $($i * 2)s)"
            break
        }
        Start-Sleep -Seconds 2
    }

    if (-not $ready) {
        Write-Log "Hub pas pret apres demarrage - recycle"
        Stop-UvicornChild $uvicornProc
        $uvicornProc = $null
        Clear-PortListeners $activePort
        Start-Sleep -Seconds 5
    }
}
