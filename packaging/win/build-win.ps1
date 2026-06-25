# 维护者：构建 RAGcore Windows 目录（内置 Python embed + 模型 + 前端）
# 用法: powershell -ExecutionPolicy Bypass -File packaging\win\build-win.ps1
$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"
$Dist = Join-Path $Root "dist"
$Packaging = Join-Path $Root "packaging"
$OutDir = Join-Path $Dist "RAGcore-win-x64"
$PythonVersion = "3.11.9"
$EmbedZip = "python-$PythonVersion-embed-amd64.zip"
$EmbedUrl = "https://www.python.org/ftp/python/$PythonVersion/$EmbedZip"

Write-Host "==> RAGcore Windows 桌面应用构建"
Write-Host "    项目目录: $Root"

Write-Host ""
Write-Host "==> 构建前端..."
Push-Location $Frontend
if (Test-Path "package-lock.json") { npm ci } else { npm install }
npm run build
Pop-Location
if (-not (Test-Path (Join-Path $Frontend "dist\index.html"))) {
    throw "frontend/dist 构建失败"
}

Write-Host ""
Write-Host "==> 校验模型..."
$Embed = Join-Path $Backend "models\bge-small-zh-v1.5\config.json"
$Rerank = Join-Path $Backend "models\bge-reranker-base\model.safetensors"
if (-not (Test-Path $Embed)) { throw "缺少 backend\models\bge-small-zh-v1.5" }
if (-not (Test-Path $Rerank)) {
    Write-Host "缺少 reranker，正在下载..."
    bash (Join-Path $Backend "scripts\download_reranker.sh")
}

$Stage = Join-Path ([IO.Path]::GetTempPath()) ("ragcore-win-" + [guid]::NewGuid().ToString())
New-Item -ItemType Directory -Path $Stage -Force | Out-Null
try {
    Write-Host ""
    Write-Host "==> 下载 Python embeddable $PythonVersion ..."
    $EmbedDir = Join-Path $Stage "embed"
    New-Item -ItemType Directory -Path $EmbedDir -Force | Out-Null
    $ZipPath = Join-Path $Stage $EmbedZip
    Invoke-WebRequest -Uri $EmbedUrl -OutFile $ZipPath -UseBasicParsing
    Expand-Archive -Path $ZipPath -DestinationPath $EmbedDir -Force

    $PthFile = Get-ChildItem -Path $EmbedDir -Filter "python*._pth" | Select-Object -First 1
    if (-not $PthFile) { throw "未找到 python*._pth" }
    $pth = Get-Content $PthFile.FullName
    $pth = $pth | ForEach-Object { if ($_ -eq "#import site") { "import site" } else { $_ } }
    if ($pth -notcontains "Lib\site-packages") { $pth += "Lib\site-packages" }
    Set-Content -Path $PthFile.FullName -Value $pth -Encoding ASCII

    Write-Host ""
    Write-Host "==> 安装 pip 与依赖（约 10–20 分钟）..."
    $getPip = Join-Path $Stage "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $getPip -UseBasicParsing
    $embedPython = Join-Path $EmbedDir "python.exe"
    & $embedPython $getPip --no-warn-script-location

    $SitePackages = Join-Path $EmbedDir "Lib\site-packages"
    New-Item -ItemType Directory -Path $SitePackages -Force | Out-Null
    & $embedPython -m pip install --upgrade pip
    & $embedPython -m pip install -r (Join-Path $Backend "requirements-lock.txt") --no-warn-script-location

    Write-Host ""
    Write-Host "==> 组装安装目录..."
    if (Test-Path $OutDir) { Remove-Item -Recurse -Force $OutDir }
    New-Item -ItemType Directory -Path $OutDir -Force | Out-Null

    $PyOut = Join-Path $OutDir "python"
    Copy-Item -Recurse -Force $EmbedDir $PyOut

    $BackendOut = Join-Path $OutDir "backend"
    New-Item -ItemType Directory -Path $BackendOut -Force | Out-Null
    Copy-Item -Recurse -Force (Join-Path $Backend "server") (Join-Path $BackendOut "server")
    Copy-Item -Recurse -Force (Join-Path $Backend "models") (Join-Path $BackendOut "models")
    Copy-Item (Join-Path $Backend ".env.example") $BackendOut
    Copy-Item (Join-Path $Backend "requirements-lock.txt") $BackendOut

    $FrontendOut = Join-Path $OutDir "frontend\dist"
    New-Item -ItemType Directory -Path (Split-Path $FrontendOut) -Force | Out-Null
    Copy-Item -Recurse -Force (Join-Path $Frontend "dist") $FrontendOut

    Copy-Item (Join-Path $Packaging "launcher.py") $OutDir
    Copy-Item (Join-Path $Packaging "win\RAGcore.cmd") $OutDir
    Copy-Item (Join-Path $Packaging "win\RAGcore.vbs") $OutDir
    Copy-Item (Join-Path $Packaging "用户安装说明.txt") (Join-Path $OutDir "安装说明.txt")

    Write-Host ""
    Write-Host "完成: $OutDir"
    $size = (Get-ChildItem $OutDir -Recurse | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host ("大小: {0:N2} GB" -f $size)
    Write-Host ""
    Write-Host "用户：双击 RAGcore.vbs 或运行 RAGcore.cmd"
    Write-Host "安装包（可选）：安装 Inno Setup 后执行"
    Write-Host "  iscc packaging\win\installer.iss"
}
finally {
    if (Test-Path $Stage) { Remove-Item -Recurse -Force $Stage }
}
