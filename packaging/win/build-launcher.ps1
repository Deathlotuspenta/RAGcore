# 编译 Windows 桌面启动器 RAGcore.exe（WinForms 状态面板）
param(
    [Parameter(Mandatory = $true)]
    [string]$OutExe
)

$ErrorActionPreference = "Stop"
$Source = Join-Path $PSScriptRoot "RagcoreApp.cs"

$cscCandidates = @(
    "${env:WINDIR}\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
    "${env:WINDIR}\Microsoft.NET\Framework\v4.0.30319\csc.exe"
)

$csc = $cscCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $csc) {
    throw "未找到 csc.exe，请安装 .NET Framework 4.x 开发组件"
}

$outDir = Split-Path $OutExe -Parent
if (-not (Test-Path $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}

& $csc `
    /nologo `
    /target:winexe `
    /platform:anycpu `
    /optimize+ `
    /out:"$OutExe" `
    /reference:System.dll,System.Drawing.dll,System.Windows.Forms.dll `
    "$Source"

if (-not (Test-Path $OutExe)) {
    throw "RAGcore.exe 编译失败"
}

Write-Host "    已生成: $OutExe"
