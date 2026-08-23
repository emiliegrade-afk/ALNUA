' Spark — demarrage silencieux (aucune fenetre PowerShell/CMD).
' Appele par "Spark.bat" / raccourci Bureau.

Option Explicit
Dim sh, fso, root, deskDir, pyw, py, exe, envFile, line, parts, key, glmKey
Dim ts

Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(WScript.ScriptFullName)
root = fso.GetParentFolderName(root)
deskDir = root & "\nadia_desktop"
pyw = root & "\.venv\Scripts\pythonw.exe"
py = root & "\.venv\Scripts\python.exe"

If Not fso.FolderExists(deskDir) Then
  MsgBox "Introuvable : nadia_desktop\" & vbCrLf & root, 16, "Spark"
  WScript.Quit 1
End If

exe = pyw
If Not fso.FileExists(exe) Then exe = py
If Not fso.FileExists(exe) Then
  MsgBox "Python introuvable. Lance d'abord Installer ALNUA Hub.bat", 16, "Spark"
  WScript.Quit 1
End If

glmKey = ""
envFile = root & "\.env"
If fso.FileExists(envFile) Then
  Set ts = fso.OpenTextFile(envFile, 1)
  Do While Not ts.AtEndOfStream
    line = Trim(ts.ReadLine)
    If Left(line, 1) <> "#" And InStr(line, "=") > 0 Then
      parts = Split(line, "=", 2)
      key = Trim(parts(0))
      If LCase(key) = "glm_api_key" Then
        glmKey = Trim(parts(1))
        Exit Do
      End If
    End If
  Loop
  ts.Close
End If

sh.Environment("PROCESS")("ALNUA_HUB_ROOT") = root
sh.Environment("PROCESS")("PYTHONPATH") = root
sh.Environment("PROCESS")("NADIA_LLM_BACKEND") = "glm_direct"
sh.Environment("PROCESS")("NADIA_TTS_BACKEND") = "edge"
If glmKey <> "" Then sh.Environment("PROCESS")("GLM_API_KEY") = glmKey

sh.CurrentDirectory = deskDir
sh.Run """" & exe & """ main.py", 0, False
