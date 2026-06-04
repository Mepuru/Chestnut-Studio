# Chestnut Studio — AI 开发指南

> 供 AI Agent 在本项目中协作时参考

---

## 项目概述

Chestnut Studio 是一款视频笔记工具——边看视频边添加带时间戳的笔记。
基于 PySide6 开发，当前版本 v2.3.0。

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
| `core/note_manager.py` | 笔记 + 术语数据模型（Note/Term/NoteManager） |
| `core/ffmpeg.py` | FFmpeg 封装（视频信息解析） |
| `core/track_config.py` | 轨道数量、颜色、NOTE_TYPES 唯一来源 |
| `core/ass_merge.py` | ASS+TXT 字幕合并引擎（无 UI 依赖） |
| `resources.py` | 资源路径管理（支持 Nuitka 打包） |
| `utils/theme.py` | 主题引擎：34 个 token + render_stylesheet() |
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

## 构建

```bash
uv run python scripts/build_release.py
```

输出到 `dist/ChestnutStudio-{version}-Nuitka.exe`。

---

## Release Notes 规范

每次发布新版本时，用 `gh release create` 创建 GitHub Release，Release Notes 按以下格式编写。

### 格式模板

```markdown
# Chestnut Studio v{version}

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
2. **只写用户能感知的变化** — 不上报纯粹的内部重构（改变量名、调整 import 顺序等），除非它有外部可观测的影响（性能提升、体积减小等）。
3. **功能按重要性降序排列** — 新功能在前，修复居中，构建/测试在后。同类变更合并成一条（如"修复 5 处内存泄漏"）。
4. **描述要具体** — 不说"优化了体验"，说"添加了确认对话框，防止误清空笔记"。
5. **篇幅控制** — 大版本 ≤ 30 行，小版本（hotfix）≤ 15 行。

### 发布命令

```bash
gh release create v{version} "dist/ChestnutStudio-{version}-Nuitka.exe" --title "Chestnut Studio v{version}" --notes-file /dev/stdin << EOF
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
