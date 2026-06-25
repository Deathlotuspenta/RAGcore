Set shell = CreateObject("WScript.Shell")
installDir = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
shell.CurrentDirectory = installDir
shell.Environment("PROCESS")("RAGCORE_BUNDLE") = "1"
shell.Environment("PROCESS")("RAGCORE_BUNDLE_DIR") = installDir
cmd = """" & installDir & "python\python.exe"" """ & installDir & "launcher.py"""
shell.Run cmd, 1, False
