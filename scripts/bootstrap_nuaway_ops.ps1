# Bootstrap ops NUAWAY — audit + readiness + prochaines etapes
# Usage: .\scripts\bootstrap_nuaway_ops.ps1 [-Port 8003] [-SkipApi]

param(
    [int]$Port = 8003,
    [switch]$SkipApi
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    Write-Host "venv introuvable: $Python" -ForegroundColor Red
    exit 1
}

Set-Location $Root

Write-Host "`n=== ALNUA Bootstrap NUAWAY (Phase 7) ===" -ForegroundColor Cyan

if (-not $SkipApi) {
    $listening = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listening) {
        Write-Host "`n[API] Demarrage sur :$Port ..." -ForegroundColor Yellow
        Start-Process -FilePath $Python -ArgumentList @(
            "-m", "uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "$Port"
        ) -WorkingDirectory $Root -WindowStyle Hidden
        Start-Sleep -Seconds 12
    } else {
        Write-Host "`n[API] Deja active sur :$Port (PID $($listening.OwningProcess))" -ForegroundColor Green
    }
}

Write-Host "`n[1/3] Audit Phase 0..." -ForegroundColor Cyan
& $Python scripts/audit_autonomy_phase0.py
$phase0 = $LASTEXITCODE

Write-Host "`n[2/3] Readiness beta..." -ForegroundColor Cyan
& $Python scripts/nuaway_readiness_audit.py
$readiness = $LASTEXITCODE

Write-Host "`n[3/3] Bootstrap diagnostic..." -ForegroundColor Cyan
& $Python -c @"
from dotenv import load_dotenv
load_dotenv('.env')
import json
from services.nuaway_bootstrap import run_nuaway_bootstrap
print(json.dumps(run_nuaway_bootstrap(refresh=True), indent=2, ensure_ascii=False))
"@

Write-Host "`n=== Resume ===" -ForegroundColor Cyan
Write-Host "Phase 0 exit: $phase0 | Readiness exit: $readiness"
Write-Host "Hub API: http://127.0.0.1:$Port/health"
Write-Host "Cockpit: http://localhost:3000/hub"
Write-Host ""

if ($readiness -ne 0) {
    Write-Host "Actions suggerees:" -ForegroundColor Yellow
    Write-Host "  .\scripts\setup_nomad.ps1"
    Write-Host "  .\scripts\setup_academy.ps1"
    Write-Host "  .\scripts\simulate_sentry.ps1"
}

exit $readiness
