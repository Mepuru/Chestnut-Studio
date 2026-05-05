# Chestnut Studio — UI 层模块

> `chestnut_studio/ui/` 下各模块的接口、信号和设计说明。
> UI 层依赖 PySide6，负责显示和用户交互。

---

## 一、主窗口 (`main_window.py`)

`MainWindow(QMainWindow)` — 应用主窗口，管理所有卡片布局和组件信号连接。

### 职责

- 管理四个 DockWidget 卡片的布局（左 39% 右 61%，上 56% 下 44%）
- 集成菜单栏、工具栏、状态栏
- 连接各卡片间的信号通信
- 处理菜单事件（打开视频、布局重置等）
- 窗口缩放时按固定比例维护卡片尺寸

### 公有属性

| 属性 | 类型 | 说明 |
|------|------|------|
| `player_card` | `PlayerCard` | 视频播放卡片 |
| `timeline_card` | `TimelineCard` | 打轴编辑卡片 |
| `waveform_card` | `WaveformCard` | 音频波形卡片 |
| `translate_card` | `TranslateCard` | 翻译面板卡片 |
| `toolbar` | `ToolBar` | 工具栏 |
| `menu_bar` | `MenuBar` | 菜单栏 |
| `status_bar` | `StatusBar` | 状态栏 |

### 信号连接图

```
ToolBar                     MainWindow                    PlayerCard
  │ play_clicked ──────────→ play_pause ──────────────→ QMediaPlayer
  │ skip_forward ──────────→ _on_skip_forward ─────────→ set_position
  │ skip_backward ─────────→ _on_skip_backward ────────→ set_position
  │ rate_changed ──────────→ set_playback_rate ────────→ QMediaPlayer
  │ ←──────────────────── update_position ←──────────── position_changed
  │ ←──────────────────── set_duration ←─────────────── duration_changed
  │ ←──────────────────── set_playing ←──────────────── playback_state_changed
                            │
                            ├──→ StatusBar.set_time (位置变化)
                            ├──→ StatusBar.set_status (时长变化)
                            └──→ StatusBar.set_video_info (FFmpeg 解析)
```

### 布局系统

- `_layout_initialized` 标志位：首次调用跳过 `removeDockWidget`
- `_apply_layout_size()`：按比例动态计算卡片尺寸
- `resizeEvent()`：窗口缩放时自动维护比例
- `_dump_layout_info()`：打印布局调试信息到控制台

---

## 二、工具栏 (`toolbar.py`)

`ToolBar(QToolBar)` — 播放控制工具栏。

### 布局

```
[帧号] | [后退5秒] [播放/暂停] [前进5秒] | [倍速]
```

- 左侧：当前帧号（`Frame: 123` 格式，等宽字体）
- 中央：播放控制按钮组（弹性空间居中）
- 右侧：倍速下拉选择

### 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `play_clicked` | 无 | 播放/暂停按钮点击 |
| `skip_forward(ms)` | `int` | 前进毫秒 |
| `skip_backward(ms)` | `int` | 后退毫秒 |
| `rate_changed(rate)` | `float` | 倍速变化 |

### 公有方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_fps(fps)` | `float` | 设置视频帧率（用于帧号计算） |
| `set_duration(ms)` | `int` | 设置视频总时长 |
| `update_position(ms)` | `int` | 更新当前播放位置，刷新帧号 |
| `set_playing(playing)` | `bool` | 切换播放/暂停按钮文字 |
| `set_playback_rate(rate)` | `float` | 设置倍速下拉框选中项 |

### 帧号计算

```python
frame = int(ms * fps / 1000)
```

---

## 三、菜单栏 (`menubar.py`)

`MenuBar(QMenuBar)` — 应用菜单栏。

### 菜单结构

```
文件(F)
  ├── 打开视频(O)...      Ctrl+O
  ├── 导入字幕(I)...      Ctrl+I    (Phase 4)
  ├── 导出字幕(S)...      Ctrl+S    (Phase 4)
  ├── ────────────
  └── 退出(Q)             Ctrl+Q

视图(V)
  ├── 卡片(C)
  │   ├── 视频预览        （勾选显示/隐藏）
  │   ├── 时间轴
  │   ├── 波形图
  │   └── 翻译
  ├── ────────────
  ├── 布局(L)
  │   ├── 默认布局
  │   ├── ────────────
  │   └── 打印当前布局    （调试用）
  ├── ────────────
  └── 全屏(F)             F11

帮助(H)
  └── 快捷键说明(K)...    (Phase 5)
```

### 信号

| 信号 | 说明 |
|------|------|
| `open_video` | 打开视频文件 |
| `open_subtitle` | 导入字幕文件 |
| `save_subtitle` | 导出字幕文件 |
| `quit_app` | 退出应用 |
| `toggle_fullscreen` | 切换全屏 |
| `reset_layout` | 重置为默认布局 |
| `dump_layout` | 打印布局调试信息 |

---

## 四、状态栏 (`statusbar.py`)

`StatusBar(QStatusBar)` — 三段式状态栏。

### 布局

```
[就绪]  [1920×1080 · 60fps · 2000kbps]  [01:32 / 05:30]
 左1            中2（拉伸）                  右1
```

### 公有方法

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_status(text)` | `str` | 设置左侧状态信息 |
| `set_video_info(resolution, fps, bitrate)` | `str, str, str` | 设置中间视频参数（空参数不显示） |
| `set_time(current, total)` | `str, str` | 设置右侧时间（`"MM:SS" / "MM:SS"`） |
| `clear_video_info()` | 无 | 清除视频参数 |

---

## 五、视频播放卡片 (`cards/player_card.py`)

`PlayerCard(QDockWidget)` — 视频渲染和播放控制。

### 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `position_changed(ms)` | `int` | 播放位置变化 (ms) |
| `duration_changed(ms)` | `int` | 视频时长变化 (ms) |
| `video_opened(path)` | `str` | 视频已打开 |
| `playback_state_changed(playing)` | `bool` | 播放状态变化 |
| `subtitle_dropped(path)` | `str` | 字幕文件拖入 |

### 公有方法

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `open_video(path)` | `str` | `bool` | 打开视频文件 |
| `play()` | 无 | 无 | 播放 |
| `pause()` | 无 | 无 | 暂停 |
| `stop()` | 无 | 无 | 停止并回到起点 |
| `play_pause()` | 无 | 无 | 切换播放/暂停 |
| `set_position(ms)` | `int` | 无 | 跳转到指定位置 |
| `set_volume(value)` | `int` | 无 | 设置音量 0-100 |
| `set_playback_rate(rate)` | `float` | 无 | 设置倍速 0.1-2.0 |
| `set_muted(muted)` | `bool` | 无 | 设置静音 |
| `update_subtitle_overlay(text)` | `str` | 无 | 更新字幕叠加（空字符串隐藏） |
| `get_position()` | 无 | `int` | 获取当前播放位置 (ms) |
| `get_duration()` | 无 | `int` | 获取视频总时长 (ms) |
| `is_playing()` | 无 | `bool` | 是否正在播放 |

### 内部组件

| 组件 | 类型 | 说明 |
|------|------|------|
| `_scene` | `QGraphicsScene` | 场景容器 |
| `_view` | `VideoView` | 自适应缩放的视图 |
| `_video_item` | `QGraphicsVideoItem` | 视频画面 |
| `_subtitle_item` | `QGraphicsTextItem` | 字幕叠加（z=1） |
| `_hint_label` | `QLabel` | 空状态提示 |
| `_player` | `QMediaPlayer` | 播放器实例 |
| `_audio_output` | `QAudioOutput` | 音频输出 |

### VideoView 子类

`VideoView(QGraphicsView)` — 自动 `fitInView` 保持宽高比居中显示，`resizeEvent` 时重新适配。

### 拖放支持

- 接受视频文件：`.mp4 .avi .flv .mkv .mov .wmv .mp3 .wav .aac .flac .ogg`
- 接受字幕文件：`.srt .ass .vtt .lrc`（发射 `subtitle_dropped` 信号）

### 空状态

未加载视频时显示居中提示 `拖入视频文件 或 Ctrl+O 打开`，加载后自动隐藏。

---

## 六、其他卡片（占位）

以下卡片在 Phase 0 创建了空壳，后续阶段实现：

| 卡片 | 文件 | 默认区域 | 实现阶段 |
|------|------|----------|----------|
| `TimelineCard` | `cards/timeline_card.py` | Right | Phase 3 |
| `WaveformCard` | `cards/waveform_card.py` | Left | Phase 2 |
| `TranslateCard` | `cards/translate_card.py` | Right | Phase 4 |

当前均显示占位提示文字，功能为空。
