# start_nadia_desktop.ps1
# Lance Nadia Desktop depuis le venv du Hub.
# Place ce fichier à la racine du Hub ou dans nadia_desktop/.

$ErrorActionPreference = "Stop"

# ── Chemins ──────────────────────────────────────────────────────────────────
# Adapte HUB_ROOT si ton Hub n'est pas à cet endroit
$HUB_ROOT    = $env:ALNUA_HUB_ROOT
if (-not $HUB_ROOT) {
    # Tentative auto-détection : cherche à côté de ce script
    $HUB_ROOT  = "C:\Dev\ALUNA_HUB"
}

$Python      = Join-Path $HUB_ROOT ".venv\Scripts\python.exe"
$NadiaDir    = Join-Path $HUB_ROOT "nadia_desktop"

# ── Vérifie les prérequis ────────────────────────────────────────────────────
if (-not (Test-Path $Python)) {
    Write-Host "❌ venv introuvable : $Python" -ForegroundColor Red
    Write-Host "   Lance d'abord : python -m venv .venv && .venv\Scripts\pip install -r requirements.txt"
    exit 1
}

if (-not (Test-Path $NadiaDir)) {
    Write-Host "❌ Dossier nadia_desktop introuvable : $NadiaDir" -ForegroundColor Red
    exit 1
}

# ── Variables d'environnement ─────────────────────────────────────────────────
$env:ALNUA_HUB_ROOT      = $HUB_ROOT
$env:PYTHONPATH          = $HUB_ROOT
$env:NADIA_LLM_BACKEND   = "hub"       # "hub" | "glm" | "ollama"
$env:NADIA_TTS_BACKEND   = "edge"      # "edge" | "kokoro"
# $env:GLM_API_KEY        = "ta-clé"   # décommenter si NADIA_LLM_BACKEND=glm
# $env:NADIA_WAKE_WORD    = "1"         # décommenter pour activer le wake word

# ── Lancement ────────────────────────────────────────────────────────────────
Write-Host "🟡 Démarrage Nadia Desktop…" -ForegroundColor Yellow
Write-Host "   Hub     : $HUB_ROOT" -ForegroundColor Gray
Write-Host "   Python  : $Python"   -ForegroundColor Gray
Write-Host "   Mode    : $($env:NADIA_LLM_BACKEND)" -ForegroundColor Gray

Set-Location $NadiaDir
& $Python main.py
