# Identite Windows d'une fenetre ALNUA (AUMID + icone barre des taches).
# Windows ne lit l'icone d'une app --app que si un .lnk du Menu Demarrer
# porte le meme AppUserModelID — sinon icone "raccourci Internet" (IE).

function Set-AlnuaShortcutIdentity {
    param(
        [Parameter(Mandatory = $true)][string]$ShortcutPath,
        [Parameter(Mandatory = $true)][string]$AppId,
        [string]$IconPath,
        [string]$DisplayName = "ALNUA Hub",
        [string]$RelaunchCommand
    )
    if (-not (Test-Path -LiteralPath $ShortcutPath)) { return }

    $code = @"
using System;
using System.Runtime.InteropServices;

public static class AlnuaShortcutIdentity {
  [ComImport, Guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
  interface IPropertyStore {
    uint GetCount(out uint cProps);
    uint GetAt(uint iProp, out PROPERTYKEY pkey);
    uint GetValue(ref PROPERTYKEY key, out PROPVARIANT pv);
    uint SetValue(ref PROPERTYKEY key, ref PROPVARIANT pv);
    uint Commit();
  }
  [StructLayout(LayoutKind.Sequential, Pack = 4)]
  struct PROPERTYKEY { public Guid fmtid; public uint pid; }
  [StructLayout(LayoutKind.Sequential)]
  struct PROPVARIANT {
    public ushort vt; public ushort wReserved1; public ushort wReserved2; public ushort wReserved3;
    public IntPtr pointerValue;
  }
  [DllImport("shell32.dll", CharSet = CharSet.Unicode, PreserveSig = false)]
  static extern void SHGetPropertyStoreFromParsingName(
    [MarshalAs(UnmanagedType.LPWStr)] string pszPath,
    IntPtr pbc, uint flags,
    [MarshalAs(UnmanagedType.LPStruct)] Guid riid,
    out IPropertyStore ppv);

  static readonly Guid PKEY = new Guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3");

  static void SetStr(IPropertyStore store, uint pid, string value) {
    if (string.IsNullOrEmpty(value)) return;
    var key = new PROPERTYKEY { fmtid = PKEY, pid = pid };
    var pv = new PROPVARIANT { vt = 31, pointerValue = Marshal.StringToCoTaskMemUni(value) };
    try { store.SetValue(ref key, ref pv); }
    finally { Marshal.FreeCoTaskMem(pv.pointerValue); }
  }

  public static void Set(string shortcutPath, string appId, string iconPath, string displayName, string relaunch) {
    IPropertyStore store;
    // GPS_READWRITE | GPS_HANDLERPROPERTIESONLY
    SHGetPropertyStoreFromParsingName(shortcutPath, IntPtr.Zero, 3, typeof(IPropertyStore).GUID, out store);
    try {
      SetStr(store, 5, appId);
      SetStr(store, 3, iconPath);
      SetStr(store, 4, displayName);
      SetStr(store, 2, relaunch);
      store.Commit();
    } finally {
      Marshal.ReleaseComObject(store);
    }
  }
}
"@
    try {
        if (-not ([System.Management.Automation.PSTypeName]"AlnuaShortcutIdentity").Type) {
            Add-Type -TypeDefinition $code -ErrorAction Stop
        }
        $iconRes = if ($IconPath) { "$IconPath,0" } else { $null }
        [AlnuaShortcutIdentity]::Set($ShortcutPath, $AppId, $iconRes, $DisplayName, $RelaunchCommand)
    } catch {
        # Best-effort : IconLocation du .lnk reste un repli.
    }
}

function Get-AlnuaHubIconPath {
    param([string]$Root)
    foreach ($rel in @("assets\alnua-x-round.ico", "assets\alnua-hub.ico")) {
        $p = Join-Path $Root $rel
        if (Test-Path -LiteralPath $p) { return $p }
    }
    return $null
}

function Install-AlnuaHubWindowShortcut {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$BrowserPath,
        [Parameter(Mandatory = $true)][string]$Arguments,
        [Parameter(Mandatory = $true)][string]$AppId,
        [string]$IconPath
    )

    $programs = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\ALNUA"
    if (-not (Test-Path -LiteralPath $programs)) {
        New-Item -ItemType Directory -Path $programs -Force | Out-Null
    }
    $lnkPath = Join-Path $programs "ALNUA Hub.lnk"

    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($lnkPath)
    $sc.TargetPath = $BrowserPath
    $sc.Arguments = $Arguments
    $sc.WorkingDirectory = $Root
    $sc.WindowStyle = 1
    $sc.Description = "ALNUA Hub"
    if ($IconPath) { $sc.IconLocation = "$IconPath,0" }
    $sc.Save()

    $relaunch = "`"$BrowserPath`" $Arguments"
    Set-AlnuaShortcutIdentity -ShortcutPath $lnkPath -AppId $AppId `
        -IconPath $IconPath -DisplayName "ALNUA Hub" -RelaunchCommand $relaunch

    return $lnkPath
}
