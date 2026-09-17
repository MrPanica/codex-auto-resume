Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
Set objWMIService = GetObject("winmgmts:\\.\root\cimv2")
Set colItems = objWMIService.ExecQuery("SELECT * FROM Win32_Process WHERE Name like 'python%' AND CommandLine like '%codex_tray_app.py%'")

is_running = False
For Each objItem in colItems
    is_running = True
    Exit For
Next

codexDir = "C:\Users\Artur\.codex"
triggerFile = codexDir & "\toggle.trigger"
appScript = "O:\GitHub\codex-auto-resume\codex_tray_app.py"
pythonwExe = "C:\Users\Artur\AppData\Local\Programs\Python\Python312\pythonw.exe"

If is_running Then
    Set tf = fso.CreateTextFile(triggerFile, True)
    tf.WriteLine("toggle")
    tf.Close
Else
    WshShell.Run """" & pythonwExe & """ """ & appScript & """", 0, False
End If
