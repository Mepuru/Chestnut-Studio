# Chestnut Studio v2.2.3

> 双后端构建 + 多项稳定性修复

---

## 双后端构建

从 v2.2.2 开始，Chestnut Studio 提供两种打包方式，均位于 GitHub Release 附件中：

### PyInstaller 版（`-PyInstaller.exe`）

| 项目 | 值 |
|------|-----|
| 大小 | ≈55 MB |
| 原理 | 捆绑 Python 解释器 + PySide6 DLL |
| 特点 | 构建快速（≈1 分钟）、兼容性好 |

### Nuitka 版（`-Nuitka.exe`）

| 项目 | 值 |
|------|-----|
| 大小 | ≈33 MB |
| 原理 | 将 Python 编译为 C → 原生 exe |
| 特点 | 体积小 40%、启动更快、不易反编译 |
| 注意 | 首次构建需下载 zig 编译器（自动）；Python 3.14 为实验性支持 |

**选择建议**：一般用户推荐 Nuitka 版（更小更快）；如遇到杀软误报或兼容问题，换用 PyInstaller 版。

---

## v2.2.1 → v2.2.3 变更

### Bug 修复

- `Note.from_line` 支持 3 位毫秒时间戳解析（之前只支持 2 位厘秒）
- `import_terms` 重复术语去重（同一文件导入两次不再重复）
- `_clear_all` 添加确认对话框，防止误清空笔记和术语
- `Note.__lt__` 与 `__hash__`/`__eq__` 对齐，排序行为可预测
- FFmpeg 缺失时状态栏提示安装，不再静默失败

### 代码质量

- `AssDialogue` dataclass 原生字段替代动态 `setattr`/`delattr`，消除异常泄露
- `_on_term_requested` 复用 `TermEditDialog`，消除 70 行内联对话框
- `NOTE_TYPES` / `TRACK_COLORS_HEX` 改为 `tuple` 防止意外变异
- `_build_track_colors_line` 模运算兜底颜色索引
- 移除死代码 `get_effective_track_count`、`InputBar._add_term`

### 构建系统

- 新增 Nuitka 构建后端（`--onefile --include-qt-plugins=multimedia`）
- PyInstaller 改为 `--onefile` 输出（单 exe）
- 构建脚本 `--jobs=N` 自动使用全部 CPU 核心
- Nuitka 版默认关闭控制台窗口（`--windows-console-mode=disable`）
- Nuitka 版使用归档格式（`--onefile-as-archive`）规避杀软误报
- 构建产物各自独立，互不删文件

### 其他

- `LogManager` 启动时注册 stderr handler，日志不再落入黑洞
- 移除三个版本绑定的陈旧 `.spec` 文件
