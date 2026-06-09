# Chestnut Studio — AI 开发指南

> 供 AI Agent 在本项目中协作时参考

---

## 项目概述

Chestnut Studio 是一款视频笔记工具——边看视频边添加带时间戳的笔记。
基于 PySide6 开发，当前版本 v2.6.0。

**核心特性**:
- 视频播放 + 10 条彩色轨道（Ctrl+1~9/0 切换）
- 时间戳笔记（输入时自动记录当前视频位置）
- 笔记按轨道分组显示，双击跳转
- 术语库管理（笔记列表按 M 或右键 → 术语）
- 导出/导入（TXT + JSON）
- 拖放打开视频
- ASS+TXT 字幕合并
- 深色主题（token 化 QSS）

---

## 核心约定

### 分层架构

```
UI 层 (ui/)          → 依赖核心层和工具层，依赖 PySide6
核心层 (core/)        → 只依赖工具层，不依赖 PySide6（可独立测试）
工具层 (utils/)       → 无外部依赖
```

**红线**: 核心层绝不引入 PySide6 依赖。

### 核心层内部子层（core/）

```
model/     → 纯数据类（dataclass），可被任意层引用
compute/   → 纯计算函数，依赖 model/，零 I/O 零副作用（已落地）
io/        → 文件/网络 I/O，依赖 model/ + compute/（已落地）
manager/   → 编排器（轻量胶水），组合 model + compute + io（规划中）
```

**子层依赖规则**:
- `model/` 可被 `compute/`、`io/`、`manager/`、`ui/` 任意引用
- `compute/`、`io/`、`manager/` 不可反向依赖
- 当前过渡期：`MergePlan` 中的 `write()`/`generate_report()` 已委托到 `core/io/ass_writer.py`，保持方法存根以兼容现有调用点

### 导入路径规范

数据类统一从 `core.model` 导入，不从原始模块导入：

```python
# ✅ 正确
from chestnut_studio.core.model.note import Note, Term
from chestnut_studio.core.model.ass_merge import AssDialogue, MergePlan
from chestnut_studio.core.model.ffmpeg import VideoInfo, FFmpegError

# ❌ 错误 — 数据类已从原始模块移除
from chestnut_studio.core.note_manager import Note   # Note 已移到 model/note.py
from chestnut_studio.core.ass_merge import AssDialogue  # AssDialogue 已移到 model/ass_merge.py

# ✅ 编排器/服务类仍从原始模块导入
from chestnut_studio.core.note_manager import NoteManager
from chestnut_studio.core.ass_merge import build_merge_plan
from chestnut_studio.core.ffmpeg import FFmpeg
```

`core/__init__.py` 同时导出所有公开符号以保持 `from chestnut_studio.core import XXX` 兼容，但新代码应优先使用精确导入路径。

### 信号通信

信号在 `MainWindow._connect_signals()` 中集中声明连接：

```python
self.player_card.position_changed.connect(self.input_bar.set_timestamp)
self.player_card.video_opened.connect(self._on_video_opened)
self.input_bar.note_sent.connect(self._on_note_sent)
self.note_panel.jump_to_position.connect(self.player_card.set_position)
self.note_panel.edit_requested.connect(self.input_bar.load_for_edit)
self.note_panel.term_requested.connect(self._on_term_requested)
```

---

## 关键文件

| 文件 | 职责 |
|------|------|
| `main.py` | 应用入口（高 DPI + 字体 + 样式表） |
| `ui/main_window.py` | 主窗口：菜单栏、信号连接、快捷键、拖放 |
| `ui/input_bar.py` | 底部输入栏：轨道切换 + 时间戳显示 + 发送 |
| `ui/note_panel.py` | 右侧笔记列表：分组显示、双击跳转、右键删除/术语 |
| `ui/term_dialog.py` | 术语编辑/查看对话框 |
| `ui/player_controls.py` | 播放控制栏：进度条、音量、倍速 |
| `ui/merge_dialog.py` | ASS+TXT 字幕合并对话框 |
| `ui/debug_box.py` | 开发者百宝箱（崩溃/日志/性能测试） |
| `ui/cards/player_card.py` | QMediaPlayer 视频播放封装 |
| `core/model/note.py` | Note / Term 纯数据类 |
| `core/model/ass_merge.py` | AssDialogue / TxtNote / MergePlan 纯数据类（write/generate_report 薄委托） |
| `core/model/ffmpeg.py` | VideoInfo / FFmpegError 纯数据类 |
| `core/compute/note_processor.py` | 笔记纯计算函数（过滤/排序/ID分配） |
| `core/compute/ass_merge_engine.py` | ASS+TXT 合并纯匹配算法（可被 Moonbit 替换） |
| `core/io/note_repository.py` | 笔记文件 I/O（读/写 TXT + JSON） |
| `core/io/term_repository.py` | 术语文件 I/O（读/追加区块格式） |
| `core/io/ass_repository.py` | ASS/TXT 字幕文件解析（read_ass, read_txt_notes） |
| `core/io/ass_writer.py` | 合并结果输出（write_output, generate_merge_report） |
| `core/note_manager.py` | NoteManager 编排器（CRUD + 导入导出编排，委托 compute + io） |
| `core/ffmpeg.py` | FFmpeg 封装（视频信息解析） |
| `core/track_config.py` | 轨道数量、颜色、NOTE_TYPES 唯一来源 |
| `core/ass_merge.py` | ASS+TXT 文件解析 + build_merge_plan 编排（委托 compute） |
| `resources.py` | 资源路径管理（支持 Nuitka 打包） |
| `utils/theme.py` | 主题引擎：32 个 token + render_stylesheet() |
| `utils/log_manager.py` | 线程安全日志管理器（handler 模式） |
| `utils/time_utils.py` | 时间格式转换（ms → SRT/ASS/VTT/LRC 等） |
| `utils/update_checker.py` | GitHub 版本更新检查（纯数据层） |
| `utils/version.py` | 版本号从 pyproject.toml 单源读取 |

---

## 快捷键

| 快捷键 | 功能 | 位置 |
|--------|------|------|
| `F1` | 播放/暂停 | `main_window.py:keyPressEvent` |
| `F2` / `←` | 后退 5 秒 | 同上 |
| `F3` / `→` | 前进 5 秒 | 同上 |
| `Ctrl+1~9` / `Ctrl+0` | 切换轨道 1~10 | 同上 |
| `Ctrl+O` | 打开视频 | 菜单栏 |
| `Ctrl+E` | 导出笔记 | 菜单栏 |
| `Ctrl+I` | 导入笔记 | 菜单栏 |
| `Ctrl+Q` | 退出 | 菜单栏 |
| `Enter` (输入框) | 发送笔记 | `input_bar.py:_send` |
| `Delete` (笔记列表) | 删除选中笔记 | `note_panel.py:_NoteListWidget` |
| `M` (笔记列表) | 打开术语录入 | 同上 |

---

## 测试

```bash
# 代码检查 + 格式化
uv run ruff check chestnut_studio/
uv run ruff format chestnut_studio/

# 运行测试
uv run pytest tests/ -v
```

---

## 日志约定

> 统一使用 `@log_operation` 装饰器代替手动 `logger.info()` 记录用户操作审计日志。
> 装饰器底层和手动调用走的是同一个 `LogManager` 管道，不存在两套系统。

### 前置模式 `after=False`（默认）

用于日志内容仅依赖方法参数的场景——在方法调用前记录。

```python
from chestnut_studio.utils import log_operation

@log_operation("打开视频: {path}")
def _on_open_video(self, path: str):
    ...

@log_operation("查看术语")
def _show_terms(self):
    ...
```

### 后置模式 `after=True`

用于日志内容依赖函数内部运行时状态（如播放/暂停、静音切换）或内部计算结果（如跳转位置）的场景——在方法调用后记录，`{result}` 绑定返回值。

```python
@log_operation("{result}", after=True)
def _toggle_play_pause(self) -> str:
    was_playing = self._is_playing
    self.play_pause()
    return "暂停" if was_playing else "播放"

@log_operation("跳转 {ms:+d}ms → {result}ms", after=True)
def _skip(self, ms: int) -> int:
    new_pos = max(0, min(self._player.position() + ms, self._duration))
    self.set_position(new_pos)
    return new_pos
```

`{result}` 和 `{param_name}` 可以同时使用。

### 条件分支的处理

不要把日志写在分发函数（如 `keyPressEvent`）中。让每个分支调用的目标方法自身使用 `@log_operation`：

```python
# ❌ 不推荐：在分发层手动写日志
def keyPressEvent(self, event):
    if key == Qt.Key_F1:
        self.player_card.play_pause()
        logger.info("用户操作: 播放")   # ← 手动日志

# ✅ 推荐：日志下推到目标方法
def keyPressEvent(self, event):
    if key == Qt.Key_F1:
        self.player_card.play_pause()  # ← play_pause() 自身带 @log_operation
```

### 什么时候不用装饰器？

以下场景保留手动 `self._logger.info()` 或 `logger.info()`：

1. **属性/表达式型** — 日志内容包含属性访问（`{note.type}`）、方法调用（`{ms_to_time_str(x)}`）或切片（`{text[:50]}`）（`str.format()` 不支持这些）
2. **核心层技术调试** — `core/` 下的 debug/error 日志仍用 `self._logger.info()` 手动调用

### 导入路径

```python
from chestnut_studio.utils import log_operation  # 推荐
from chestnut_studio.utils.log_utils import log_operation  # 也可
```

---

## 构建

```bash
# 构建 (Nuitka --mode=standalone + NSIS installer)
uv run python scripts/build_release.py
```

输出到 `dist/ChestnutStudio-{version}-Setup-x86_64_v1.exe`。

构建流程:
1. `--mode=standalone` → 目录（exe + DLL + Python 运行时）
2. NSIS (makensis) 打包成 setup.exe（LZMA 压缩）
3. Zig 编译器以 `-mcpu=baseline` 模式运行（兼容所有 x86-64 CPU）
4. 安装时自动检测旧版本，先静默卸载再安装新版

---

## Release Notes 规范

每次发布新版本时，用 `gh release create` 创建 GitHub Release，Release Notes 按以下格式编写。

### 格式模板

```markdown
> {一句话版本亮点}

---

### ✨ 新功能

- **{功能名}** — {一句话概述}
  - {子要点}（可选，有则写）
  - {子要点}

### 🔧 改进

- {改动描述}

### 🐛 修复

- {问题描述}

### 🧪 测试

- {测试指标变化}

### 📦 构建

- {构建相关变更}
```

### 规则

1. **每条 Release Note 必须自包含** — 不引用 CHANGELOG.md、commit hash 或其他外部文档。用户看到的应该是一个可以直接理解的发布说明。
2. **功能按重要性降序排列** — 新功能在前，修复居中，构建/测试在后。同类变更合并成一条（如"修复 5 处内存泄漏"）。
3. **描述要具体** — 不说"优化了体验"，说"添加了确认对话框，防止误清空笔记"。

### 发布命令

```bash
gh release create v{version} "dist/ChestnutStudio-{version}-Setup-x86_64_v1.exe" --title "Chestnut Studio v{version}" --notes-file /dev/stdin << EOF
{按上面模板写 Release Notes}
EOF
```

---

## 注意事项

1. **核心层不引入 PySide6** — `core/` 下的代码必须在纯 Python 环境中可测试
2. **版本号唯一来源是 `pyproject.toml`** — 改版本只改那里，然后 `uv lock`
3. **全局快捷键在 `MainWindow.keyPressEvent`** — 保证任何焦点下都生效
4. **术语编辑在 `term_dialog.py`** — 不要在新的地方另写一套术语 UI
5. **`NOTE_TYPES` 从 `track_config.py` 导入** — 不要在其他文件硬编码轨道列表
6. **QSS 使用 `{{token}}` 占位符** — `utils/theme.py` 渲染，不要硬编码颜色值到 QSS 中
7. **内联 `setStyleSheet()` 仅用于动态值** — 轨道颜色（`get_track_color()`）、视频背景色（`get_theme()['bg_video']`）等无法通过 QSS 控制的场景才用
8. **`@log_operation` 优先于手写 `logger.info()`** — UI 层用户操作审计统一用装饰器，减少冗余；核心层技术日志保留手动调用
9. **数据类从 `core.model` 导入** — `Note`, `Term`, `AssDialogue`, `MergePlan`, `VideoInfo` 等纯数据类统一从 `core.model` 子包导入，不从原始模块（`note_manager.py` / `ass_merge.py` / `ffmpeg.py`）导入。编排器/服务类（`NoteManager` / `FFmpeg` / `build_merge_plan`）仍从原始模块导入。
