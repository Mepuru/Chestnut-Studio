# 视频播放卡片

> `chestnut_studio/ui/cards/player_card.py`
> `PlayerCard(BaseCard)` — 视频渲染和播放控制，支持 AB 循环。

---

## 职责

- 视频渲染（QGraphicsVideoItem + 字幕叠加预览）
- 播放控制（播放/暂停/停止/跳转）
- AB 循环功能
- 空状态提示

---

## 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `position_changed(ms)` | `int` | 播放位置变化 (ms) |
| `duration_changed(ms)` | `int` | 视频时长变化 (ms) |
| `video_opened(path)` | `str` | 视频已打开 |
| `playback_state_changed(playing)` | `bool` | 播放状态变化 |
| `ab_loop_changed(a, b)` | `int, int` | AB 循环状态变化，-1 表示未设置 |

---

## 公有方法

### 视频控制

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

### 状态获取

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `get_position()` | 无 | `int` | 获取当前播放位置 (ms) |
| `get_duration()` | 无 | `int` | 获取视频总时长 (ms) |
| `is_playing()` | 无 | `bool` | 是否正在播放 |

### 字幕叠加

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `update_subtitle_overlay(text)` | `str` | 无 | 更新字幕叠加（空字符串隐藏） |

### AB 循环

| 方法 | 参数 | 返回 | 说明 |
|------|------|------|------|
| `set_ab_loop_a()` | 无 | 无 | 设置 A 点为当前位置 |
| `set_ab_loop_b()` | 无 | 无 | 设置 B 点为当前位置 |
| `clear_ab_loop()` | 无 | 无 | 清除 AB 循环 |
| `get_ab_loop_points()` | 无 | `tuple[int, int]` | 获取 AB 点位置 |
| `is_ab_loop_enabled()` | 无 | `bool` | AB 循环是否激活 |

---

## 用法示例

```python
from chestnut_studio.ui.cards.player_card import PlayerCard

# 创建卡片
player_card = PlayerCard()

# 连接信号
player_card.position_changed.connect(self.on_position_changed)
player_card.duration_changed.connect(self.on_duration_changed)
player_card.video_opened.connect(self.on_video_opened)
player_card.ab_loop_changed.connect(self.on_ab_loop_changed)

# 打开视频
success = player_card.open_video("video.mp4")

# 播放控制
player_card.play()
player_card.pause()
player_card.stop()
player_card.play_pause()
player_card.set_position(15000)  # 跳转到 15 秒
player_card.set_volume(80)
player_card.set_playback_rate(1.5)

# AB 循环
player_card.set_ab_loop_a()  # 设置 A 点为当前位置
player_card.set_ab_loop_b()  # 设置 B 点为当前位置
player_card.clear_ab_loop()  # 清除循环
a, b = player_card.get_ab_loop_points()  # 获取 AB 点
```

---

## AB 循环机制

### 设置流程

1. 用户按 `[` 或点击 A 按钮 → `PlayerCard.set_ab_loop_a()`
2. 用户按 `]` 或点击 B 按钮 → `PlayerCard.set_ab_loop_b()`
3. `PlayerCard.ab_loop_changed` 发射 → 更新工具栏按钮样式 + 波形图循环区域
4. 播放时 `_on_position_changed` 检测位置 → 超过 B 点自动跳回 A 点
5. 用户按 `\` 或点击 × 按钮 → `PlayerCard.clear_ab_loop()` 清除循环

### 自动交换

- 自动确保 A < B（如果 A > B 则交换）
- 打开新视频时自动清除循环

---

## 内部组件

| 组件 | 类型 | 说明 |
|------|------|------|
| `_scene` | `QGraphicsScene` | 场景容器 |
| `_view` | `VideoView` | 自适应缩放的视图 |
| `_video_item` | `QGraphicsVideoItem` | 视频画面 |
| `_subtitle_item` | `QGraphicsTextItem` | 字幕叠加（z=1） |
| `_hint_label` | `QLabel` | 空状态提示 |
| `_player` | `QMediaPlayer` | 播放器实例 |
| `_audio_output` | `QAudioOutput` | 音频输出 |

---

## VideoView 子类

`VideoView(QGraphicsView)` — 自动 `fitInView` 保持宽高比居中显示：
- `resizeEvent` 时重新适配
- 视频尺寸变化时通过 `nativeSizeChanged` 信号自动调用 `fit_video()`

---

## 空状态

未加载视频时显示居中提示 `拖入视频文件 或 Ctrl+O 打开`，加载后自动隐藏。

---

## 注意事项

### 播放控制

- 播放控制全部由工具栏负责，PlayerCard 只负责渲染
- 不包含播放按钮，只提供播放接口

### 字幕叠加

- 字幕叠加在视频画面上方（z=1）
- 空字符串时隐藏字幕
- 字幕样式可通过 QSS 定制

### 性能考虑

- 使用 `QGraphicsVideoItem` 硬件加速渲染
- `fitInView` 保持宽高比，避免变形
- 避免频繁调用 `set_position()`，使用定时器节流

---

## 依赖

- PySide6: `QDockWidget`, `QGraphicsView`, `QGraphicsScene`, `QMediaPlayer`, `QAudioOutput`
- chestnut_studio.utils.time_utils: `split_time`
