# Changelog

## v2.4.0 (2026-06-04)

### ✨ 新功能

- **启动页面** — 双击 exe 后瞬间弹出背景图，后台加载主窗口，减少黑屏等待感
- **关于对话框 GitHub 链接** — 方便直达项目主页

### 🔧 改进

- **启动速度优化** — splash 图片从 118KB (PNG) 降至 35KB (JPEG)，日志初始化移至 splash 之后
- **精简 dev 依赖** — 移除未使用的 `pyinstaller`/`imageio`/`pillow`，清理 241 行锁定文件
- **移除未使用的图标文件** — `send.svg` 从未被引用
- **代码清理** — 移除 `_show_about` 中的冗余导入、测试文件中的未使用 import

### 🧪 测试

- **新增 49 个测试用例** — 补充 `track_config`/`theme`/`update_checker`/`resources` 模块的单元测试
- 总测试数从 175 → 224

## v2.3.1 (2026-06-04)

### 🔧 改进

- **移除 PyInstaller** — 仅保留 Nuitka 单后端构建，体积更小
- **简化帮助菜单** — 移除不常用的键盘加速键（Alt+H/L/B/A）
- **移除 Space 误导提示** — 播放按钮不再标注 (Space)，避免误导用户
- **资源模块精简** — 移除 PyInstaller 残留代码和死函数 `get_fonts_dir()`

### 🧹 清理

- 移除 `PlayerControls` 未使用的 `seeking_started`/`seeking_finished` 信号
- 移除 `build_release.py` 中的 PyInstaller 构建函数
- 移除 `release_notes.md` 历史文件
- 移除 `version.py` 中过时的 "PyInstaller 后备" 注释

### 📦 构建

- 仅 Nuitka --onefile 构建
- 输出：`dist/ChestnutStudio-2.3.1-Nuitka.exe`（≈33 MB）

---

## v2.3.0 (2026-06-04)

### ✨ 新功能

- **全项目日志系统** — `LogManager` 单例落地，所有模块统一日志
  - 自动写入 `%LOCALAPPDATA%/ChestnutStudio/logs/app.log`
  - 崩溃时自动快照为 `crash_时间戳.log`
  - 超过 1MB 自动轮转，保留最近 10 个归档
  - 会话分隔线 + 每条日志即时落盘，崩溃不丢
- **开发者百宝箱** — 菜单「帮助 → 百宝箱」
  - 崩溃测试：`1÷0` / `assert False` / `IndexError`
  - 日志测试：DEBUG / INFO / WARNING / ERROR
  - 性能测试：批量添加 100/500/1000 条笔记
- **操作审计追踪** — 所有用户操作（打开视频、添加/删除笔记、导出导入、倍速切换等）忠实写入日志
- **状态栏改进**
  - 右下角常驻版本号
  - 消息持久显示，直到下一条操作覆盖
- **全局崩溃兜底** — `sys.excepthook` 捕获未处理异常，弹窗提示 + 日志快照

### 🔧 改进

- 笔记增删日志集中到 `NoteManager`，所有入口统一
- 统一日志调用风格：`logger.info(...)` 替代冗长的 `LogManager.instance().emit(LogRecord(...))`
- 统一日志存储路径，开发/发布均使用 `%LOCALAPPDATA%`
- 构建全面切换至 Nuitka（移除 PyInstaller 默认）

### 🧪 测试

- 测试总数从 **68** 增长至 **175**（+157%）
- 新增测试覆盖：时间工具、ASS 合并、版本号、术语 API、文件 I/O 异常路径

### 🧹 清理

- 移除 4 处死代码（`MergePlan.get_ass_content`、冗余 import、过时日志等）
- 移除 `logs/` 目录（日志统一走 `%LOCALAPPDATA%`）

### 📦 构建

- 仅 Nuitka `--onefile` 构建
- 输出：`dist/ChestnutStudio-2.3.0-Nuitka.exe` (≈33 MB)
