# Chestnut Studio — AI 开发指南

> 供 AI Agent 在本项目中协作开发时参考

---

## 项目概述

Chestnut Studio 是一款面向字幕组/烤肉组的现代化字幕工具，基于 PySide6 开发。

**当前进度**: Phase 3 进行中（打轴编辑）

**核心特性**: 
- 时间轴卡片负责打轴（设置字幕的开始/结束时间）
- 翻译面板分为源语言区和目标语言区
- 源语言和目标语言共享相同的时间点

---

## 核心约定

### 分层架构

```
UI 层 (ui/)          → 依赖核心层和工具层，依赖 PySide6
核心层 (core/)        → 只依赖工具层，不依赖 PySide6（可独立测试）
工具层 (utils/)       → 无外部依赖
```

**红线**: 核心层绝不引入 PySide6 依赖。

### 卡片间通信

- 卡片间通过 **Signal** 通信，不直接引用
- MainWindow 负责连接各卡片的信号
- 错误做法: `self.player_card._player.setPosition(1000)`
- 正确做法: `self.player_card.position_changed.connect(...)`

---

## 关键路径

| 文件 | 职责 |
|------|------|
| `chestnut_studio/ui/main_window.py` | 主窗口，信号连接中心 |
| `chestnut_studio/ui/cards/player_card.py` | 视频播放 + AB 循环 |
| `chestnut_studio/ui/cards/waveform_card.py` | 音频波形显示 |
| `chestnut_studio/ui/toolbar.py` | 工具栏按钮 |
| `chestnut_studio/core/audio.py` | 音频处理函数 |
| `chestnut_studio/core/ffmpeg.py` | FFmpeg 封装 |

---

## 快捷键清单

| 快捷键 | 功能 | 所在文件 |
|--------|------|----------|
| `Space` | 播放/暂停 | `main_window.py` |
| `[` | 设置 AB 循环 A 点 | `main_window.py` |
| `]` | 设置 AB 循环 B 点 | `main_window.py` |
| `\` | 清除 AB 循环 | `main_window.py` |
| `Ctrl+O` | 打开视频 | `menubar.py` |

---

## 信号连接图

```
ToolBar                          MainWindow                         PlayerCard
  │ play_clicked ──────────────→ play_pause ───────────────────→ QMediaPlayer
  │ skip_forward ──────────────→ _on_skip_forward ──────────────→ set_position
  │ ab_loop_a_clicked ─────────→ _on_ab_loop_set_a ────────────→ set_ab_loop_a
  │ ab_loop_b_clicked ─────────→ _on_ab_loop_set_b ────────────→ set_ab_loop_b
  │ ab_loop_clear_clicked ─────→ _on_ab_loop_clear ────────────→ clear_ab_loop
  │ ←───────────────────────── update_position ←──────────────── position_changed
  │ ←───────────────────────── set_duration ←─────────────────── duration_changed
  │ ←───────────────────── update_ab_loop_state ←─────────────── ab_loop_changed
                              │
                              ├──→ WaveformCard.update_position
                              ├──→ WaveformCard.set_ab_loop_region
                              └──→ StatusBar.set_time

WaveformCard
  │ position_clicked ──────────→ PlayerCard.set_position

TimelineCard
  │ subtitle_selected ─────────→ TranslateCard.show_subtitle
  │ subtitle_changed ──────────→ WaveformCard.refresh_overlay
```

---

## 测试命令

```bash
# 运行所有测试
uv run pytest tests/

# 运行特定测试文件
uv run pytest tests/test_phase2.py -v

# 代码检查
uv run ruff check chestnut_studio/

# 代码格式化
uv run ruff format chestnut_studio/
```

---

## 注意事项

1. **不要修改 prototypes/ 目录** - 这是历史设计文档
2. **docs/ 目录的文档要保持面向外部读者** - 不要写"我记得..."
3. **新增功能要同步更新文档** - 特别是 docs/ui.md 和 docs/core.md
4. **全局快捷键在 MainWindow.keyPressEvent 中处理** - 确保任何卡片获得焦点都能响应
