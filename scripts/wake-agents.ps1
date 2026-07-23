# Reveille les agents quand ils glandent - alimente la file Academy + retry echecs.
param(
    [switch]$Status,
    [switch]$NoRetry,
    [int]$Count = 0,
    [string]$HubUrl = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Py = Join-Path $Root ".venv\Scripts\python.exe"
$EnvFile = Join-Path $Root ".env"

function Resolve-HubUrl {
    if ($HubUrl) { return $HubUrl.TrimEnd("/") }
    $portFile = Join-Path $Root "data\hub_active_port.txt"
    $ports = @()
    if (Test-Path $portFile) {
        $p = (Get-Content $portFile -Raw).Trim()
        if ($p -match '^\d+$') { $ports += [int]$p }
    }
    $ports += @(8003, 8002, 8000, 8001) | Where-Object { $ports -notcontains $_ }
    foreach ($port in $ports) {
        $url = "http://127.0.0.1:$port"
        try {
            Invoke-RestMethod -Uri "$url/orchestration/pipeline-status" -TimeoutSec 3 | Out-Null
            return $url
        } catch { }
    }
    return "http://127.0.0.1:8000"
}

$HubUrl = Resolve-HubUrl
$key = ""
if (Test-Path $EnvFile) {
    $line = Get-Content $EnvFile | Where-Object { $_ -match '^HUB_API_KEY=' } | Select-Object -First 1
    if ($line) { $key = $line.Split('=', 2)[1].Trim() }
}

function Show-Status($s) {
    $ac = $s.academy
    Write-Host ""
    Write-Host "=== Agents ALNUA ===" -ForegroundColor Cyan
    Write-Host "Etat    : $($s.verdict) - $($s.message)"
    if ($ac) {
        Write-Host "Niveau  : L$($ac.current_level) - $($ac.completed) sur $($ac.total) exercices"
        Write-Host "En cours: $($ac.in_pipeline) | En file: $($ac.agent_ready) | Echecs: $($ac.agent_failed)"
        Write-Host "Slots   : $($ac.slots_free) sur $($ac.max_parallel) libres"
    }
    Write-Host ""
    if ($s.verdict -eq "idle" -or $s.verdict -eq "stuck") {
        Write-Host "Relance sans -Status pour les remettre au travail." -ForegroundColor Yellow
    }
}

function Invoke-PythonWake {
    param([bool]$StatusOnly, [bool]$RetryFailed, [int]$ReadyCount)
    if (-not (Test-Path $Py)) { throw "venv introuvable: $Py" }
    $retryPy = if ($RetryFailed) { "True" } else { "False" }
    if ($StatusOnly) {
        $json = & $Py -c "from dotenv import load_dotenv; load_dotenv(); from services.agent_wake import get_pipeline_status; import json; print(json.dumps(get_pipeline_status()))"
        return $json | ConvertFrom-Json
    }
    if ($ReadyCount -gt 0) {
        $json = & $Py -c "from dotenv import load_dotenv; load_dotenv(); from services.agent_wake import wake_agents; import json; print(json.dumps(wake_agents(retry_failed=$retryPy, mark_ready_count=$ReadyCount), default=str))"
    } else {
        $json = & $Py -c "from dotenv import load_dotenv; load_dotenv(); from services.agent_wake import wake_agents; import json; print(json.dumps(wake_agents(retry_failed=$retryPy), default=str))"
    }
    return $json | ConvertFrom-Json
}

function Invoke-ApiWake {
    param([bool]$StatusOnly, [bool]$RetryFailed, [int]$ReadyCount)
    $headers = @{ "Content-Type" = "application/json" }
    if ($key) { $headers["X-Hub-Key"] = $key }
    if ($StatusOnly) {
        return Invoke-RestMethod -Uri "$HubUrl/orchestration/pipeline-status" -Headers $headers
    }
    $body = @{ retry_failed = $RetryFailed; sync = $true; notify = $false }
    if ($ReadyCount -gt 0) { $body["mark_ready_count"] = $ReadyCount }
    $json = $body | ConvertTo-Json -Compress
    return Invoke-RestMethod -Uri "$HubUrl/orchestration/wake" -Method POST -Headers $headers -Body $json
}

try {
    $useApi = $true
    try {
        if ($Status) {
            $result = Invoke-ApiWake -StatusOnly $true -RetryFailed $true -ReadyCount 0
        } else {
            $result = Invoke-ApiWake -StatusOnly $false -RetryFailed (-not $NoRetry) -ReadyCount $Count
        }
    } catch {
        $useApi = $false
        if ($Status) {
            $result = Invoke-PythonWake -StatusOnly $true -RetryFailed $true -ReadyCount 0
        } else {
            $result = Invoke-PythonWake -StatusOnly $false -RetryFailed (-not $NoRetry) -ReadyCount $Count
        }
    }

    if ($Status) {
        Show-Status $result
        exit 0
    }

    Write-Host ""
    if ($result.summary) {
        Write-Host $result.summary -ForegroundColor Green
    } else {
        Show-Status $result.status
    }
    Write-Host ""
    if ($result.status.verdict -eq "working") {
        Write-Host "Les agents travaillent." -ForegroundColor Green
    }
    if (-not $useApi) {
        Write-Host "(mode direct Python - redemarre le Hub pour l'API: .\scripts\stop_hub_daemon.ps1 puis start)" -ForegroundColor DarkGray
    }
}
catch {
    Write-Host "ERREUR: $_" -ForegroundColor Red
    exit 1
}
