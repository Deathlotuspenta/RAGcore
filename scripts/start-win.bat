@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set "ROOT=%~dp0.."
set "BACKEND=%ROOT%\backend"
set "FRONTEND=%ROOT%\frontend"
set "VENV=%BACKEND%\.venv"
set "PORT=8765"
set "URL=http://127.0.0.1:%PORT%"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP%\RAGcore.lnk"

if "%~1"=="install-autostart" goto install_autostart
if "%~1"=="uninstall-autostart" goto uninstall_autostart
if "%~1"=="autostart" goto autostart
goto start

:start
if not exist "%VENV%\Scripts\uvicorn.exe" (
  echo 开发者环境未就绪。请在 backend 目录创建虚拟环境并安装依赖：
  echo   cd backend
  echo   python -m venv .venv
  echo   .venv\Scripts\activate
  echo   pip install -r requirements.txt
  pause
  exit /b 1
)
if not exist "%FRONTEND%\dist\index.html" (
  echo 缺少 frontend\dist
  pause & exit /b 1
)
cd /d "%BACKEND%"
set SERVE_STATIC=true
curl -sf "%URL%/health" >nul 2>&1 && (
  echo RAGcore 已在运行: %URL%
  start "" "%URL%"
  pause
  exit /b 0
)
echo ==^> 启动 RAGcore: %URL%
echo ==^> 关闭此窗口即停止服务
call "%VENV%\Scripts\activate.bat"
start /b "" cmd /c "for /l %%i in (1,1,40) do (curl -sf %URL%/health >nul 2>&1 && (start \"\" %URL% & exit /b 0) & timeout /t 1 /nobreak >nul)"
uvicorn server.main:app --host 127.0.0.1 --port %PORT%
goto end

:autostart
if not exist "%VENV%\Scripts\uvicorn.exe" exit /b 1
cd /d "%BACKEND%"
set SERVE_STATIC=true
curl -sf "%URL%/health" >nul 2>&1 && exit /b 0
start /min "" cmd /c "cd /d %BACKEND% && call %VENV%\Scripts\activate.bat && set SERVE_STATIC=true && uvicorn server.main:app --host 127.0.0.1 --port %PORT%"
timeout /t 2 /nobreak >nul
start "" "%URL%"
goto end

:install_autostart
if not exist "%VENV%\Scripts\uvicorn.exe" (
  echo 请先配置 backend\.venv（见 README 开发者说明）
  pause & exit /b 1
)
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%SHORTCUT%'); $s.TargetPath='%ROOT%\scripts\start-win.bat'; $s.Arguments='autostart'; $s.WorkingDirectory='%ROOT%'; $s.Save()"
echo 已开启开机自启
goto end

:uninstall_autostart
if exist "%SHORTCUT%" del "%SHORTCUT%" && echo 已关闭开机自启 || echo 未配置开机自启
goto end

:end
