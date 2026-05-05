# libmpv 设置说明

## 项目已配置

libmpv 库已配置在 `libs/mpv/` 目录中：
- `libs/mpv/bin/libmpv-2.dll` - 运行时动态库
- `libs/mpv/lib/mpv.lib` - MSVC 导入库（从 DLL 生成）
- `libs/mpv/lib/mpv.def` - 符号定义文件

## 编译

### 启用 mpv 支持
```bash
cargo build --features mpv
```

### 不启用 mpv 支持（默认）
```bash
cargo build
```

## 发布打包

当使用 `cargo build --release --features mpv` 构建后，需要将 `mpv-2.dll` 
与可执行文件一起分发。

发布目录结构：
```
chestnut-studio/
├── chestnut-studio.exe
├── mpv-2.dll          ← 必须包含此文件
└── ... (其他资源文件)
```

## 验证安装

编译并运行程序后，点击"导入视频"按钮，如果能正常打开视频文件，说明 libmpv 配置成功。

## 更新 libmpv

如需更新 libmpv 版本：

1. 从 https://github.com/shinchiro/mpv-winbuild-cmake/releases 下载新版本
2. 解压并将 `libmpv-2.dll` 复制到 `libs/mpv/bin/`
3. 重新生成 MSVC 导入库（可选，如果 API 没变化可以复用）

### 重新生成 MSVC 导入库

```powershell
# 1. 导出符号
dumpbin /EXPORTS libs/mpv/bin/libmpv-2.dll /OUT:libs/mpv/exports.txt

# 2. 创建 .def 文件（只包含 mpv_ 开头的符号）

# 3. 生成 .lib
lib /DEF:libs/mpv/lib/mpv.def /OUT:libs/mpv/lib/mpv.lib /MACHINE:X64
```

## 故障排除

### 编译错误：找不到 mpv.lib
确保 `libs/mpv/lib/mpv.lib` 文件存在。

### 运行时错误：找不到 mpv-2.dll
确保 `mpv-2.dll` 与可执行文件在同一目录。

### 链接错误：未解析的符号
可能是 libmpv 版本与 crate 不兼容。尝试下载更新的 libmpv 版本。
