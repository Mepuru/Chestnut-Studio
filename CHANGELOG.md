# Changelog

## v2.7.0 (2026-06-09)

### ✨ 新功能

- **项目文件管理** — 新增 `.chestnut` 项目文件格式，支持保存(Ctrl+S)、另存为(Ctrl+Shift+S)、打开(Ctrl+Shift+O)
  - 项目文件包含笔记、术语、视频路径、播放进度、音量和倍速
  - 打开项目时自动恢复笔记列表、排序方式、当前轨道
  - 视频路径不存在时记录 warning 日志，不弹窗不残留
- **PlayerCard 重建机制** — 打开项目时销毁旧播放器创建新实例，彻底解决 QVideoWidget 原生窗口状态残留

### 🔧 改进

- **播放器状态零泄漏** — 项目切换 = 新旧播放器全量替换，无需手动清除任何状态
- **NoteManager 序列化** — 新增 `to_dict()` / `from_dict()` 批量方法，支持 JSON 序列化
- **Term 数据类** — 新增 `to_dict()` / `from_dict()` 序列化方法
- **NotePanel** — 新增 `set_sort_mode()` 公有方法，支持外部恢复排序状态

### 🧪 测试

- 新增 22 个测试覆盖 SessionState 序列化往返、项目文件 I/O、NoteManager 序列化
- 总测试数 236

### 📦 构建

- Nuitka standalone + NSIS 打包

## v2.6.0 (2026-06-09)

### ✨ 新功能

- **日志系统升级** — 新增 `@log_operation` 装饰器，自动记录用户操作日志，消除手动 `logger.info()` 调用
  - 支持 `after=True` 后置模式，用 `{result}` 绑定返回值
  - 替换 UI 层 13 处手动日志调用，源码更简洁
  - 核心层技术日志保留原有 `self._logger.info()` 手动模式（两种入口、同一条管道）

### 🔧 改进

- **更新检查** — 成功时（已是最新版本）增加日志提示，覆盖全部出口
- **CLAUDE.md** — 新增「日志约定」章节，明确装饰器使用规范

### 🐛 修复

- **HTTP 200 显示 Unknown Error** — PySide6 中 `QNetworkReply.error()` 返回枚举成员，Python 中所有枚举成员均为 truthy（含值为 0 的 `NoError`），导致成功响应被误判为错误
- **点击进度条 seek 后进度卡死** —  `_is_dragging` 标志在 `sliderPressed` 中提早设置，`sliderMoved` 不触发时标志无法复位
- **笔记列表文字显示不全** — 高度计算使用硬编码 `18 + n*18` 与 QLabel 实际渲染存在偏差，改用 `QFontMetrics` 精确计算文本换行高度

### 🧪 测试

- 新增 17 个 `@log_operation` 装饰器单元测试（含 `after=True` 后置模式 6 个）
- 总测试数 241（+17）

## v2.5.0 (2026-06-06)

### 📦 构建

- **NSIS 安装器** — 从 Nuitka onefile 替换为 standalone + NSIS 打包，彻底消除 Windows Defender 误报
  - LZMA 压缩，28.6 MB（比 onefile 更小）
  - 自动检测旧版本并静默卸载升级，安装无残留
  - 安装时可选择创建桌面快捷方式
- **CPU 兼容性** — Zig 编译器强制 `-mcpu=baseline`，支持所有 x86-64 CPU（修复旧机 0xc000001d 崩溃）

### 🔧 改进

- **术语编辑** — 保存前验证必填字段（术语/译文），缺失时弹出警告

### 🧪 测试

- 总测试数 224（无变化）

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
