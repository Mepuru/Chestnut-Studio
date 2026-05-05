# setup-mpv.ps1 - 自动下载并配置 libmpv
# 用法: .\scripts\setup-mpv.ps1

$ErrorActionPreference = "Stop"

$LIBS_DIR = "$PSScriptRoot\..\libs\mpv"
$LIB_DIR = "$LIBS_DIR\lib"
$BIN_DIR = "$LIBS_DIR\bin"

# 创建目录
New-Item -ItemType Directory -Path $LIB_DIR -Force | Out-Null
New-Item -ItemType Directory -Path $BIN_DIR -Force | Out-Null

Write-Host "=== libmpv 自动配置脚本 ===" -ForegroundColor Cyan
Write-Host ""

# 检查是否已存在
if ((Test-Path "$BIN_DIR\mpv-2.dll") -and (Test-Path "$LIB_DIR\mpv.lib")) {
    Write-Host "[OK] libmpv 已配置，跳过下载" -ForegroundColor Green
    exit 0
}

# 从 GitHub API 获取最新 release
Write-Host "正在获取最新版本信息..." -ForegroundColor Yellow

try {
    $release = Invoke-RestMethod -Uri "https://api.github.com/repos/shinchiro/mpv-winbuild-cmake/releases/latest" -Headers @{
        "Accept" = "application/vnd.github.v3+json"
    }
    
    $version = $release.tag_name
    Write-Host "最新版本: $version" -ForegroundColor Green
    
    # 找到 x86_64-v3 的 7z 文件
    $asset = $release.assets | Where-Object { $_.name -match "mpv-dev-x86_64-v3.*\.7z$" } | Select-Object -First 1
    
    if (-not $asset) {
        Write-Host "[ERROR] 找不到合适的下载文件" -ForegroundColor Red
        exit 1
    }
    
    $downloadUrl = $asset.browser_download_url
    $fileName = $asset.name
    $tempFile = "$env:TEMP\$fileName"
    
    Write-Host "下载: $fileName" -ForegroundColor Yellow
    Write-Host "URL: $downloadUrl" -ForegroundColor Gray
    
    # 下载文件
    Invoke-WebRequest -Uri $downloadUrl -OutFile $tempFile -UseBasicParsing
    
    Write-Host "下载完成，正在解压..." -ForegroundColor Yellow
    
    # 解压（需要 7z 或使用 Expand-Archive）
    $extractDir = "$env:TEMP\mpv-extract"
    if (Test-Path $extractDir) {
        Remove-Item -Recurse -Force $extractDir
    }
    
    # 尝试使用 7z
    $7zPath = Get-Command 7z -ErrorAction SilentlyContinue
    if ($7zPath) {
        & 7z x $tempFile -o"$extractDir" -y | Out-Null
    } else {
        # 使用 tar（Windows 10+）
        Write-Host "[WARN] 未找到 7z，尝试使用 tar..." -ForegroundColor Yellow
        tar -xf $tempFile -C $env:TEMP
        $extractDir = "$env:TEMP\mpv-dev-x86_64-v3-*"
        $extractDir = (Get-Item $extractDir | Select-Object -First 1).FullName
    }
    
    # 复制文件
    $dllFile = Get-ChildItem -Path $extractDir -Filter "mpv-2.dll" -Recurse | Select-Object -First 1
    $libFile = Get-ChildItem -Path $extractDir -Filter "mpv.lib" -Recurse | Select-Object -First 1
    
    if ($dllFile) {
        Copy-Item $dllFile.FullName "$BIN_DIR\mpv-2.dll" -Force
        Write-Host "[OK] 已复制 mpv-2.dll" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] 找不到 mpv-2.dll" -ForegroundColor Red
    }
    
    if ($libFile) {
        Copy-Item $libFile.FullName "$LIB_DIR\mpv.lib" -Force
        Write-Host "[OK] 已复制 mpv.lib" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] 找不到 mpv.lib" -ForegroundColor Red
    }
    
    # 清理
    Remove-Item -Recurse -Force $extractDir -ErrorAction SilentlyContinue
    Remove-Item -Force $tempFile -ErrorAction SilentlyContinue
    
    Write-Host ""
    Write-Host "=== 配置完成 ===" -ForegroundColor Green
    Write-Host "现在可以使用以下命令编译:" -ForegroundColor Cyan
    Write-Host "  cargo build --features mpv" -ForegroundColor White
    
} catch {
    Write-Host "[ERROR] 下载失败: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "请手动下载 libmpv:" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://github.com/shinchiro/mpv-winbuild-cmake/releases" -ForegroundColor White
    Write-Host "  2. 下载 mpv-dev-x86_64-v3-*.7z" -ForegroundColor White
    Write-Host "  3. 解压后将 mpv-2.dll 和 mpv.lib 复制到 libs/mpv/bin 和 libs/mpv/lib" -ForegroundColor White
    exit 1
}
