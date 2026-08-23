' Compat : redirige vers launch-spark-silent.vbs
Option Explicit
Dim sh, fso, root, vbs
Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
vbs = root & "\launch-spark-silent.vbs"
If fso.FileExists(vbs) Then
  sh.Run "wscript.exe //nologo """ & vbs & """", 0, False
Else
  MsgBox "Introuvable : launch-spark-silent.vbs", 16, "Spark"
End If
