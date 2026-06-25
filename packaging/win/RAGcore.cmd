@echo off
setlocal
cd /d "%~dp0"
set "RAGCORE_BUNDLE=1"
set "RAGCORE_BUNDLE_DIR=%~dp0"
"%~dp0python\python.exe" "%~dp0launcher.py"
endlocal
