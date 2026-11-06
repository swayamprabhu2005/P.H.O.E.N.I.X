Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = currentDir

setupDoneMarker = currentDir & "\config\.setup_done"

' If first time running, open console wizard to ask for Name & Groq Key
If Not fso.FileExists(setupDoneMarker) Then
    WshShell.Run "python app\first_run_setup.py", 1, True
End If

' Launch P.H.O.E.N.I.X. silently in the background with windowless pythonw
WshShell.Run "pythonw app\main.py", 0, False
