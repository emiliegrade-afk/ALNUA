# Install Grounding DINO into the project venv (Windows).
# Run from repo root: .\scripts\install-grounding-dino.ps1

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Pip = Join-Path $Root ".venv\Scripts\pip.exe"

if (-not (Test-Path $Python)) {
    Write-Error "Venv not found. Create it first: python -m venv .venv"
}

Write-Host "==> Using venv: $Python"

Write-Host "==> Installing PyTorch (CPU)..."
& $Pip install "torch>=2.0.0" "torchvision>=0.15.0"

Write-Host "==> Installing DINO runtime deps (no opencv-python — headless already in project)..."
& $Pip install timm transformers addict yapf pycocotools matplotlib defusedxml pydeprecate scipy
& $Pip install supervision --no-deps

Write-Host "==> Installing Grounding DINO (no build isolation, no deps)..."
& $Pip install --no-deps --no-build-isolation "git+https://github.com/IDEA-Research/GroundingDINO.git"

$ModelsDir = Join-Path $Root "models\groundingdino"
$ConfigPath = Join-Path $ModelsDir "GroundingDINO_SwinT_OGC.py"
$WeightsPath = Join-Path $ModelsDir "groundingdino_swint_ogc.pth"
New-Item -ItemType Directory -Force -Path $ModelsDir | Out-Null

if (-not (Test-Path $ConfigPath)) {
    Write-Host "==> Downloading config..."
    Invoke-WebRequest `
        -Uri "https://raw.githubusercontent.com/IDEA-Research/GroundingDINO/main/groundingdino/config/GroundingDINO_SwinT_OGC.py" `
        -OutFile $ConfigPath
}

if (-not (Test-Path $WeightsPath)) {
    Write-Host "==> Downloading weights (~700 MB, may take a few minutes)..."
    Invoke-WebRequest `
        -Uri "https://github.com/IDEA-Research/GroundingDINO/releases/download/v0.1.0-alpha/groundingdino_swint_ogc.pth" `
        -OutFile $WeightsPath
}

Write-Host "==> Verifying import..."
& $Python -c "from groundingdino.util.inference import load_model, load_image, predict; print('groundingdino OK')"

Write-Host ""
Write-Host "Done. Weights:" $WeightsPath
