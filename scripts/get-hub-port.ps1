# Returns the active Hub API port (data/hub_active_port.txt or 8003).
$Root = Split-Path -Parent $PSScriptRoot
$portFile = Join-Path $Root "data\hub_active_port.txt"
if (Test-Path $portFile) {
    $raw = (Get-Content $portFile -Raw).Trim()
    if ($raw -match '^\d+$') {
        Write-Output ([int]$raw)
        exit 0
    }
}
Write-Output 8003
