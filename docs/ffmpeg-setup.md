# FFmpeg 安装与配置指南

Chestnut Studio 依赖 FFmpeg 进行视频信息解析和音轨提取。本文档将指导你完成 FFmpeg 的安装和配置。

---

## 下载 FFmpeg

### 方法一：官方版本（推荐）

1. 访问 [FFmpeg 官网](https://ffmpeg.org/download.html)
2. 选择适合你操作系统的版本
3. 下载 **release full** 版本（包含所有功能）

### 方法二：第三方构建（Windows 推荐）

Windows 用户可以从以下网站下载预编译版本，更加方便：

- [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) - 下载 `ffmpeg-release-full.zip`
- [BtbN GitHub](https://github.com/BtbN/FFmpeg-Builds/releases) - 下载 `ffmpeg-master-latest-win64-gpl.zip`

---

## 安装步骤

### Windows

1. **解压文件**
   - 将下载的 ZIP 文件解压到一个固定位置
   - 建议路径：`C:\ffmpeg` 或 `D:\tools\ffmpeg`
   - 避免路径中包含中文或空格

2. **配置系统 PATH**
   - 按 `Win + S` 搜索 "环境变量"
   - 点击 "编辑系统环境变量"
   - 点击 "环境变量" 按钮
   - 在 "系统变量" 中找到 `Path`，点击 "编辑"
   - 点击 "新建"，添加 FFmpeg 的 bin 目录路径
     - 例如：`C:\ffmpeg\bin`
   - 点击 "确定" 保存所有更改

3. **重启终端**
   - 关闭所有已打开的命令行窗口
   - 重新打开新的命令行窗口（PATH 更改需要重启终端生效）

### macOS

使用 Homebrew 安装：

```bash
brew install ffmpeg
```

### Linux

Ubuntu/Debian：
```bash
sudo apt update
sudo apt install ffmpeg
```

Fedora：
```bash
sudo dnf install ffmpeg
```

Arch Linux：
```bash
sudo pacman -S ffmpeg
```

---

## 验证安装

打开命令行（CMD / PowerShell / 终端），执行：

```bash
ffmpeg -version
```

如果安装成功，会显示 FFmpeg 的版本信息，类似：

```
ffmpeg version 7.0.2-full_build-www.gyan.dev
...
```

### 常见问题

**问题：提示 "ffmpeg 不是内部或外部命令"**

原因：PATH 未正确配置

解决方法：
1. 确认 FFmpeg 的 bin 目录已添加到 PATH
2. 重启命令行窗口
3. 使用完整路径测试：`C:\ffmpeg\bin\ffmpeg -version`

**问题：PATH 配置后仍不生效**

解决方法：
1. 注销并重新登录 Windows
2. 或者重启电脑

---

## 在 Chestnut Studio 中使用

配置好 FFmpeg 后，Chestnut Studio 会自动从系统 PATH 中查找 FFmpeg。

如果不想配置 PATH，也可以将 `ffmpeg.exe` 放在 Chestnut Studio 的项目根目录下，程序会优先查找当前目录。

---

## 相关文档

- [FFmpeg 封装模块文档](core/ffmpeg.md)
- [FFmpeg 官方文档](https://ffmpeg.org/documentation.html)