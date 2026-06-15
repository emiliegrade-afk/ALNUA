# dev.ps1 — Local dev helpers (Windows)
param(
    [ValidateSet("api", "web", "docker", "docker-down")]
    [string]$Target = "api"
)

$Root = Split-Path -Parent $PSScriptRoot

function Test-PortListening([int]$Port) {
    $conn = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if (-not $conn) { return $false }
    # Ignore stale Windows TCP rows where the PID no longer exists
    return $null -ne (Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue)
}

function Resolve-Port([int]$Preferred, [string]$Label) {
    if (-not (Test-PortListening $Preferred)) {
        return $Preferred
    }
    Write-Host "Port $Preferred deja utilise ($Label)."
    Write-Host "  npm run dev:status"
    Write-Host "  npm run dev:stop"
    Write-Host "  ou: `$env:DEV_API_PORT=8002; npm run dev:api"
    Write-Host "  ou: `$env:DEV_WEB_PORT=3001; npm run dev:web"
    exit 1
}

switch ($Target) {
    "api" {
        Set-Location $Root
        $port = if ($env:DEV_API_PORT) { [int]$env:DEV_API_PORT } else { 8000 }
        Resolve-Port $port "api" | Out-Null
        python -m uvicorn api.main:app --reload --host 127.0.0.1 --port $port
    }
    "web" {
        Set-Location (Join-Path $Root "web")
        $port = if ($env:DEV_WEB_PORT) { [int]$env:DEV_WEB_PORT } else { 3000 }
        Resolve-Port $port "web" | Out-Null
        npx next dev -p $port
    }
    "docker" {
        Set-Location $Root
        docker compose -f docker-compose.dev.yml up --build
    }
    "docker-down" {
        Set-Location $Root
        docker compose -f docker-compose.dev.yml down
    }
}
