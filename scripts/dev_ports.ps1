# dev_ports.ps1 — Check / stop ALNUA dev servers (Windows)
param(
    [ValidateSet("status", "stop")]
    [string]$Action = "status"
)

$Ports = @(3000, 3001, 8000, 8001, 8002)

function Get-ListenerInfo([int]$Port) {
    Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            [PSCustomObject]@{
                Port     = $Port
                PID      = $_.OwningProcess
                Process  = $proc.ProcessName
                Command  = (
                    Get-CimInstance Win32_Process -Filter "ProcessId=$($_.OwningProcess)" `
                        -ErrorAction SilentlyContinue
                ).CommandLine
            }
        }
}

function Test-AlnuaDevProcess([string]$CommandLine) {
    if (-not $CommandLine) { return $false }
    return (
        $CommandLine -match "uvicorn api\.main" -or
        $CommandLine -match "next dev" -or
        $CommandLine -match "playwright"
    )
}

switch ($Action) {
    "status" {
        Write-Host "ALNUA dev ports:"
        $found = $false
        foreach ($port in $Ports) {
            $rows = Get-ListenerInfo $port
            foreach ($row in $rows) {
                $found = $true
                $cmd = if ($row.Command) { $row.Command.Substring(0, [Math]::Min(90, $row.Command.Length)) } else { "(n/a)" }
                Write-Host ("  :{0}  PID {1}  {2}  {3}" -f $row.Port, $row.PID, $row.Process, $cmd)
            }
        }
        if (-not $found) {
            Write-Host "  (aucun listener sur 3000/3001/8000/8001/8002)"
        }
        Write-Host ""
        Write-Host "Si npm run dev:api / dev:web echoue, lance: npm run dev:stop"
    }
    "stop" {
        $stopped = 0
        Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -in @("python.exe", "node.exe") } |
            ForEach-Object {
                if (Test-AlnuaDevProcess $_.CommandLine) {
                    Write-Host "Stop PID $($_.ProcessId): $($_.CommandLine.Substring(0, [Math]::Min(80, $_.CommandLine.Length)))"
                    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
                    $stopped++
                }
            }
        # Fallback: kill anything listening on known dev ports (Playwright children, truncated cmdlines)
        foreach ($port in $Ports) {
            Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
                ForEach-Object {
                    $procId = $_.OwningProcess
                    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
                        Write-Host "Stop listener PID $procId on :$port"
                        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
                        $stopped++
                    }
                }
        }
        if ($stopped -eq 0) {
            Write-Host "Aucun serveur ALNUA trouve sur les ports dev."
        } else {
            Write-Host "Arrete $stopped processus. Relance npm run dev:api puis npm run dev:web."
        }
    }
}
