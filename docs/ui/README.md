# UI 层模块

> `chestnut_studio/ui/` 下各模块的接口、信号和设计说明。
> UI 层依赖 PySide6，负责显示和用户交互。

---

## 模块概览

### 主要组件

| 模块 | 文件 | 职责 |
|------|------|------|
| [主窗口](main_window.md) | `main_window.py` | 布局管理、信号连接、全局快捷键 |
| [工具栏](toolbar.md) | `toolbar.py` | 播放控制、AB 循环、倍速选择 |
| [菜单栏](menubar.md) | `menubar.py` | 文件/视图/帮助菜单 |
| [状态栏](statusbar.md) | `statusbar.py` | 三段式状态显示 |
| [拖放覆盖层](drag_overlay.md) | `drag_overlay.py` | 全局文件拖放、类型识别、视觉反馈 |

### 卡片组件

| 模块 | 文件 | 职责 |
|------|------|------|
| [视频播放卡片](cards/player_card.md) | `cards/player_card.py` | 视频渲染、播放控制、AB 循环 |
| [音频波形卡片](cards/waveform_card.md) | `cards/waveform_card.py` | 波形显示、打轴操作、缩放平移 |
| [时间轴列表卡片](cards/timeline_card.md) | `cards/timeline_card.py` | 字幕列表显示、编辑、锁定 |
| [翻译面板卡片](cards/translate_card.md) | `cards/translate_card.py` | 字幕文本编辑、快速跳转 |

### 弹窗组件

| 模块 | 文件 | 职责 |
|------|------|------|
| [字幕编辑对话框](dialogs/edit_subtitle_dialog.md) | `dialogs/edit_subtitle_dialog.py` | 字幕区间编辑 |

---

## 依赖关系

```
UI 层 (ui/)  ← 本模块
  ↓ 调用
核心层 (core/)
  ↓ 调用
工具层 (utils/)
```

- **UI 层**依赖核心层和工具层
- **UI 层**依赖 PySide6
- **核心层**不依赖 PySide6（可独立测试）

---

## 设计原则

### 1. 卡片化设计

所有主要功能组件采用 `QDockWidget` 实现：
- 支持拖拽、停靠、浮动
- 支持调整大小
- 支持布局保存和恢复

### 2. 信号通信

卡片间通过信号通信，不直接引用：
- `MainWindow` 负责连接各卡片的信号
- 卡片只发射信号，不直接调用其他卡片方法
- 信号命名：小写 + 下划线，描述事件

### 3. 职责分离

- **MainWindow**：布局管理、信号连接、全局快捷键
- **ToolBar**：播放控制（统一控制所有播放相关操作）
- **PlayerCard**：视频渲染（不包含播放按钮）
- **WaveformCard**：波形显示和打轴操作
- **TimelineCard**：字幕列表显示和管理
- **TranslateCard**：字幕文本编辑

---

## 信号通信图

```
ToolBar                          MainWindow                         PlayerCard
  │ play_clicked ──────────────→ play_pause ───────────────────→ QMediaPlayer
  │ skip_forward ──────────────→ _on_skip_forward ──────────────→ set_position
  │ skip_backward ─────────────→ _on_skip_backward ─────────────→ set_position
  │ rate_changed ──────────────→ set_playback_rate ─────────────→ QMediaPlayer
  │ ab_loop_a_clicked ─────────→ _on_ab_loop_set_a ────────────→ set_ab_loop_a
  │ ab_loop_b_clicked ─────────→ _on_ab_loop_set_b ────────────→ set_ab_loop_b
  │ ab_loop_clear_clicked ─────→ _on_ab_loop_clear ────────────→ clear_ab_loop
  │ ←───────────────────────── update_position ←──────────────── position_changed
  │ ←───────────────────────── set_duration ←─────────────────── duration_changed
  │ ←───────────────────────── set_playing ←──────────────────── playback_state_changed
  │ ←───────────────────── update_ab_loop_state ←─────────────── ab_loop_changed
                              │
                              ├──→ WaveformCard.update_position
                              ├──→ WaveformCard.set_duration
                              ├──→ WaveformCard.set_ab_loop_region
                              ├──→ TimelineCard.set_duration
                              ├──→ StatusBar.set_time (位置变化)
                              ├──→ StatusBar.set_status (时长变化)
                              └──→ StatusBar.set_video_info (FFmpeg 解析)

WaveformCard
  │ position_clicked ──────────→ PlayerCard.set_position
  │ subtitle_created ──────────→ MainWindow._on_subtitle_created → TimelineCard.add_subtitle
  │ subtitle_edited ───────────→ TimelineCard.apply_subtitle_edit

TimelineCard
  │ subtitle_selected ─────────→ TranslateCard.show_subtitle
  │ subtitle_changed ───────────→ MainWindow._sync_subtitle_overlay → WaveformCard.update_subtitle_overlay_from_data
  │ jump_to_position ──────────→ PlayerCard.set_position
  │ edit_subtitle_requested ───→ WaveformCard.enter_edit_mode
```

---

## 全局快捷键

在 `MainWindow.keyPressEvent` 中处理：

| 快捷键 | 功能 | 调用方法 |
|--------|------|----------|
| `Space` | 播放/暂停 | `player_card.play_pause()` |
| `[` | 设置 AB 循环 A 点 | `_on_ab_loop_set_a()` |
| `]` | 设置 AB 循环 B 点 | `_on_ab_loop_set_b()` |
| `\` | 清除 AB 循环 | `_on_ab_loop_clear()` |
| `Ctrl+O` | 打开视频文件 | `_on_open_video()` |
| `1`-`4` | 切换轨道 | `_on_switch_track()` |

---

## 布局系统

### 默认布局

比例：左 39% 右 61%，上 56% 下 44%，窗口缩放时保持比例不变。

```
┌──────────────────┬───────────────────────────────┐
│                  │                               │
│  Player          │  Timeline (打轴)              │
│                  │                               │
├──────────────────┼───────────────────────────────┤
│  Waveform        │  Translation (翻译)           │
│                  │                               │
└──────────────────┴───────────────────────────────┘
```

### 布局持久化

使用 `QSettings` 保存和恢复布局：
- 保存时机：`closeEvent`
- 恢复时机：`__init__`

---

## 主题系统

### 配色方案 (Tokyo Night)

| 用途 | 颜色 |
|------|------|
| 深色背景 | `#0f0f14` |
| 卡片标题 | `#18181b` |
| 边框 | `#27272a` |
| 强调色 | `#2563eb` |
| 主文字 | `#fafafa` |
| 次要文字 | `#a1a1aa` |

### 字体

使用 HarmonyOS Sans 字体，位于 `chestnut_studio/resources/fonts/`

---

## 测试要求

| 模块 | 测试要求 |
|------|---------|
| `main_window.py` | 可选，优先测试核心逻辑 |
| `toolbar.py` | 可选 |
| `cards/*.py` | 可选 |

UI 层测试需要 PySide6 环境，建议优先测试核心层。
