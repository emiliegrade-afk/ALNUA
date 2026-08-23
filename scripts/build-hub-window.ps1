# Compile ALNUAHub.exe (icone X integree) pour la barre des taches Windows.
# Necessite .NET Framework 4.x (csc) — present sur Windows 10/11.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Src = Join-Path $Root "tools\alnua-hub-window\HubWindow.cs"
$OutDir = Join-Path $Root "bin"
$Exe = Join-Path $OutDir "ALNUAHub.exe"
$LibDir = Join-Path $Root "tools\webview2"
$WvVersion = "1.0.2903.40"
$Icon = Join-Path $Root "assets\alnua-x-round.ico"
if (-not (Test-Path $Icon)) { $Icon = Join-Path $Root "assets\alnua-hub.ico" }

$csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"
if (-not (Test-Path $csc)) {
    $csc = Join-Path $env:WINDIR "Microsoft.NET\Framework\v4.0.30319\csc.exe"
}
if (-not (Test-Path $csc)) {
    Write-Host "csc.exe introuvable - impossible de compiler la fenetre ALNUA." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $Src)) {
    Write-Host "Source introuvable: $Src" -ForegroundColor Red
    exit 1
}

New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
New-Item -ItemType Directory -Path $LibDir -Force | Out-Null

$coreDll = Join-Path $LibDir "Microsoft.Web.WebView2.Core.dll"
$formsDll = Join-Path $LibDir "Microsoft.Web.WebView2.WinForms.dll"
$loaderDll = Join-Path $LibDir "WebView2Loader.dll"

if (-not ((Test-Path $coreDll) -and (Test-Path $formsDll) -and (Test-Path $loaderDll))) {
    Write-Host "Telechargement WebView2 $WvVersion ..." -ForegroundColor Cyan
    $nupkg = Join-Path $LibDir "webview2.zip"
    Invoke-WebRequest -Uri "https://www.nuget.org/api/v2/package/Microsoft.Web.WebView2/$WvVersion" `
        -OutFile $nupkg -UseBasicParsing
    $extract = Join-Path $LibDir "_pkg"
    if (Test-Path $extract) { Remove-Item $extract -Recurse -Force }
    Expand-Archive -Path $nupkg -DestinationPath $extract -Force
    Copy-Item (Join-Path $extract "lib\net462\Microsoft.Web.WebView2.Core.dll") $coreDll -Force
    Copy-Item (Join-Path $extract "lib\net462\Microsoft.Web.WebView2.WinForms.dll") $formsDll -Force
    $native = Get-ChildItem -Path (Join-Path $extract "runtimes") -Recurse -Filter "WebView2Loader.dll" |
        Where-Object { $_.FullName -match "win-x64" } |
        Select-Object -First 1
    if (-not $native) {
        throw "WebView2Loader.dll absent du package NuGet"
    }
    Copy-Item $native.FullName $loaderDll -Force
}

$cscArgs = @(
    "/nologo",
    "/target:winexe",
    "/platform:x64",
    "/out:$Exe",
    "/r:System.Windows.Forms.dll",
    "/r:System.Drawing.dll",
    "/r:$coreDll",
    "/r:$formsDll",
    $Src
)
if (Test-Path $Icon) {
    $cscArgs = @("/win32icon:$Icon") + $cscArgs
}

& $csc @cscArgs
if ($LASTEXITCODE -ne 0) { throw "Compilation ALNUAHub.exe echouee" }

Copy-Item $coreDll (Join-Path $OutDir "Microsoft.Web.WebView2.Core.dll") -Force
Copy-Item $formsDll (Join-Path $OutDir "Microsoft.Web.WebView2.WinForms.dll") -Force
Copy-Item $loaderDll (Join-Path $OutDir "WebView2Loader.dll") -Force
if (Test-Path $Icon) {
    Copy-Item $Icon (Join-Path $OutDir "alnua-hub.ico") -Force
}

Write-Host "OK $Exe" -ForegroundColor Green
