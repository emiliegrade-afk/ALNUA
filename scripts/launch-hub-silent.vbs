' ALNUA Hub — demarrage silencieux (sans fenetre CMD).
' Appele par "ALNUA Hub.bat" / raccourci Bureau.

Option Explicit
Dim sh, fso, root, ps1, cmd
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
root = fso.GetParentFolderName(root)
ps1 = root & "\scripts\start-all.ps1"
If Not fso.FileExists(ps1) Then
  MsgBox "Introuvable : scripts\start-all.ps1" & vbCrLf & root, 16, "ALNUA Hub"
  WScript.Quit 1
End If
cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & ps1 & """ -OpenBrowser"
' 0 = fenetre cachee, False = ne pas attendre
sh.Run cmd, 0, False
