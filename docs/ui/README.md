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

所有主要功能组件采用 `BaseCard`（继承 `QDockWidget`）实现：
- 支持拖拽、停靠、浮动
- 支持调整大小
- 支持布局保存和恢复
- 统一的生命周期钩子

### 2. 声明式信号

卡片间通过声明式信号通信：
- **SignalManager** 集中管理所有信号连接
- 卡片通过 `@subscribe` 装饰器或 `listens_to()` 声明订阅的信号
- MainWindow 通过 `@relay` 装饰器声明中转处理
- 新增组件无需修改 MainWindow

### 3. 职责分离

- **MainWindow**：初始化和协调（不包含具体业务逻辑）
- **SignalManager**：信号连接管理
- **ToolBar**：播放控制（统一控制所有播放相关操作）
- **PlayerCard**：视频渲染（不包含播放按钮）
- **WaveformCard**：波形显示和打轴操作
- **TimelineCard**：字幕列表显示和管理
- **TranslateCard**：字幕文本编辑

---

## 信号通信图

```
┌─────────────────────────────────────────────────────────────────┐
│                        SignalManager                            │
│                                                                 │
│  卡片声明 @subscribe / listens_to():                            │
│    WaveformCard ← player.position_changed/duration_changed     │
│    TimelineCard ← player.duration_changed                      │
│    TranslateCard ← timeline.subtitle_selected                  │
│    PlayerCard ← waveform.position_clicked                      │
│                ← timeline.jump_to_position                     │
│                ← toolbar.play_clicked/rate_changed/ab_loop_*   │
│                                                                 │
│    ToolBar ← player.position_changed/duration_changed          │
│            ← player.playback_state_changed/ab_loop_changed     │
│                                                                 │
│  中转处理 (@relay 装饰器):                                       │
│    player.video_opened → MainWindow._on_video_opened           │
│    player.ab_loop_changed → MainWindow._on_ab_loop_changed     │
│    waveform.subtitle_created → MainWindow._on_subtitle_created │
│    timeline.subtitle_selected → MainWindow._on_subtitle_selected│
│    translate.jump_to_next/prev → MainWindow._on_jump_to_*      │
│                                                                 │
│  动态订阅 (状态栏等):                                            │
│    player.position_changed → StatusBar.set_time                │
│    player.duration_changed → StatusBar.set_status              │
└─────────────────────────────────────────────────────────────────┘
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
