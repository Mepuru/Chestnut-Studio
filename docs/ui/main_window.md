# 主窗口

> `chestnut_studio/ui/main_window.py`
> `MainWindow(QMainWindow)` — 应用主窗口，管理所有卡片布局和组件信号连接。

---

## 职责

- 管理四个 DockWidget 卡片的布局（左 39% 右 61%，上 56% 下 44%）
- 集成菜单栏、工具栏、状态栏
- 连接各卡片间的信号通信
- 处理菜单事件（打开视频、布局重置等）
- 处理全局快捷键（Space、[、]、\）
- 窗口缩放时按固定比例维护卡片尺寸
- 拦截全局拖放事件，显示覆盖层并分发文件

---

## 公有属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `player_card` | `PlayerCard` | 视频播放卡片 |
| `timeline_card` | `TimelineCard` | 字幕列表卡片 |
| `waveform_card` | `WaveformCard` | 音频波形卡片 |
| `translate_card` | `TranslateCard` | 翻译面板卡片 |
| `toolbar` | `ToolBar` | 工具栏 |
| `menu_bar` | `MenuBar` | 菜单栏 |
| `status_bar` | `StatusBar` | 状态栏 |
| `_drag_overlay` | `DragOverlay` | 拖放覆盖层 |

---

## 信号连接图

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

在 `keyPressEvent` 中处理，确保任何卡片获得焦点都能响应：

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

### 布局实现

- `_layout_initialized` 标志位：首次调用跳过 `removeDockWidget`
- `_apply_layout_size()`：按比例动态计算卡片尺寸
- `resizeEvent()`：窗口缩放时自动维护比例
- `_dump_layout_info()`：打印布局调试信息到控制台

### 布局持久化

使用 `QSettings` 保存和恢复布局：
- 保存时机：`closeEvent`
- 恢复时机：`__init__`（开发阶段跳过）

---

## 内部方法

### 信号连接

- `_connect_signals()` - 连接所有卡片的信号
- `_connect_toolbar_signals()` - 连接工具栏信号
- `_connect_player_signals()` - 连接播放器信号
- `_connect_waveform_signals()` - 连接波形图信号
- `_connect_timeline_signals()` - 连接时间轴信号

### 事件处理

- `_on_open_video()` - 打开视频文件对话框
- `_on_subtitle_created(start_ms, end_ms)` - 处理打轴完成事件
- `_on_subtitle_selected(col, start_ms)` - 处理字幕选中事件
- `_on_jump_to_next(col, start_ms)` - 跳转到下一条字幕
- `_on_jump_to_prev(col, start_ms)` - 跳转到上一条字幕

---

## 使用示例

```python
from chestnut_studio.ui.main_window import MainWindow

# 创建主窗口
window = MainWindow()
window.show()

# 访问卡片
window.player_card.open_video("video.mp4")
window.waveform_card.load_waveform("video.mp4")
```

---

## 注意事项

### 焦点问题

- 全局快捷键在 `keyPressEvent` 中处理
- 确保任何卡片获得焦点都能响应快捷键
- 避免快捷键被子组件拦截

### 布局调试

- 菜单 **视图 > 布局 > 打印当前布局** 可输出各卡片的区域、尺寸、位置到控制台
- 使用 `_dump_layout_info()` 方法调试布局

---

## 依赖

- PySide6: `QMainWindow`, `QDockWidget`, `QSettings`
- chestnut_studio.ui.cards: `PlayerCard`, `WaveformCard`, `TimelineCard`, `TranslateCard`
- chestnut_studio.ui.toolbar: `ToolBar`
- chestnut_studio.ui.menubar: `MenuBar`
- chestnut_studio.ui.statusbar: `StatusBar`
