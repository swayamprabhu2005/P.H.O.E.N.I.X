Set fso = CreateObject("Scripting.FileSystemObject")
currentDir = fso.GetParentFolderName(WScript.ScriptFullName)

Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = currentDir

' Launch P.H.O.E.N.I.X. silently in the background with windowless pythonw
WshShell.Run "pythonw app\main.py", 0, False
