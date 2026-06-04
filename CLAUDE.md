# Chestnut Studio — AI 开发指南

> 供 AI Agent 在本项目中协作时参考

---

## 项目概述

Chestnut Studio 是一款视频笔记工具——边看视频边添加带时间戳的笔记。
基于 PySide6 开发，当前版本 v2.2.3。

**核心特性**:
- 视频播放 + 10 条彩色轨道
- 时间戳笔记（输入时自动记录当前视频位置）
- 笔记按轨道分组显示，双击跳转
- 术语库管理（笔记右键 → 术语）
- 导出/导入（TXT + JSON）
- 拖放打开视频

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
| `ui/cards/player_card.py` | QMediaPlayer 视频播放封装 |
| `core/note_manager.py` | 笔记 + 术语数据模型（Note/Term/NoteManager） |
| `core/ffmpeg.py` | FFmpeg 封装（视频信息解析） |
| `core/track_config.py` | 轨道数量、颜色、NOTE_TYPES 唯一来源 |
| `utils/log_manager.py` | 线程安全日志管理器（handler 模式） |
| `utils/time_utils.py` | 时间格式转换（ms → SRT/ASS/VTT/LRC 等） |
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
# 全部构建（PyInstaller + Nuitka）
uv run python scripts/build_release.py

# 仅构建 PyInstaller 版
uv run python scripts/build_release.py pyinstaller

# 仅构建 Nuitka 版
uv run python scripts/build_release.py nuitka
```

输出到 `dist/ChestnutStudio-{version}-{Backend}.exe`。

---

## 注意事项

1. **核心层不引入 PySide6** — `core/` 下的代码必须在纯 Python 环境中可测试
2. **版本号唯一来源是 `pyproject.toml`** — 改版本只改那里，然后 `uv lock`
3. **全局快捷键在 `MainWindow.keyPressEvent`** — 保证任何焦点下都生效
4. **术语编辑在 `term_dialog.py`** — 不要在新的地方另写一套术语 UI
5. **`NOTE_TYPES` 从 `track_config.py` 导入** — 不要在其他文件硬编码轨道列表
