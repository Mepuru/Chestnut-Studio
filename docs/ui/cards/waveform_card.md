# 音频波形卡片

> `chestnut_studio/ui/cards/waveform_card.py`
> `WaveformCard(QDockWidget)` — 音频波形显示，支持打轴操作。

---

## 职责

- 音频波形显示（包络线 + 原始波形）
- 打轴操作（标记字幕开始/结束点）
- 缩放和平移操作
- AB 循环区域显示
- 编辑模式（可视化调整字幕起止点）

---

## 信号

| 信号 | 参数 | 说明 |
|------|------|------|
| `position_clicked(ms)` | `int` | 点击波形位置 (ms) |
| `subtitle_created(start_ms, end_ms)` | `int, int` | 打轴完成，创建新字幕 |

---

## 打轴功能

### 打轴流程

1. `I` 键 或 点击 [标记开始] → 标记字幕开始点
2. `O` 键 或 点击 [标记结束] → 标记字幕结束点
3. 标记完成后，字幕条自动添加到时间轴列表

### 编辑模式

- 进入编辑模式：点击时间轴列表的编辑按钮
- 编辑模式下：
  - `I` 键设置起点
  - `O` 键设置终点
  - `Enter` 确认编辑
  - `Escape` 取消编辑

---

## 布局

```
┌─────────────────────────────────────────────┐
│ [1.0x] [0:00 - 0:30]        [滚轮缩放 | Shift+拖动平移] │  ← 信息栏
├─────────────────────────────────────────────┤
│                                             │
│     ░░░░░░░     ░░░░░░░░░                   │  ← 包络线（半透明蓝色）
│    ░░░▓▓▓░░░░░ ░░░░▓▓▓▓░░░░                 │  ← 原始波形（亮蓝色细线）
│   ░░░▓▓▓▓▓░░░░░░░░▓▓▓▓▓▓░░░                 │
│ ─────────────────────────────────────────── │  ← 零线
│   ░░░▓▓▓▓▓░░░░░░░░▓▓▓▓▓▓░░░                 │
│    ░░░▓▓▓░░░░░ ░░░░▓▓▓▓░░░░                 │
│     ░░░░░░░     ░░░░░░░░░                   │
│                                             │
│   0:00  0:05  0:10  0:15  0:20  0:25  0:30  │  ← 时间刻度
├─────────────────────────────────────────────┤
│  [主音轨] [人声] [BGM]     打轴: [开始] [结束] │  ← 切换按钮 + 打轴按钮
└─────────────────────────────────────────────┘
```

---

## 公有方法

### 波形加载

| 方法 | 参数 | 说明 |
|------|------|------|
| `load_waveform(video_path)` | `str` | 加载视频音频波形，返回是否成功 |
| `set_duration(duration_ms)` | `int` | 设置视频总时长 |

### 位置更新

| 方法 | 参数 | 说明 |
|------|------|------|
| `update_position(position_ms)` | `int` | 更新播放位置，移动红线和视窗 |

### 字幕叠加

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_subtitle_regions(regions)` | `dict[int, int]` | 设置字幕条覆盖区域 |
| `clear_subtitle_regions()` | 无 | 清除字幕条覆盖 |
| `update_subtitle_overlay_from_data(subtitle_data)` | `dict` | 从字幕数据更新叠加 |

### AB 循环

| 方法 | 参数 | 说明 |
|------|------|------|
| `set_ab_loop_region(a, b)` | `int, int` | 设置 AB 循环区域显示 |

### 打轴操作

| 方法 | 参数 | 说明 |
|------|------|------|
| `mark_subtitle_start()` | 无 | 标记字幕开始点 |
| `mark_subtitle_end()` | 无 | 标记字幕结束点 |
| `enter_edit_mode(col, start_ms, end_ms)` | `int, int, int` | 进入编辑模式 |
| `exit_edit_mode()` | 无 | 退出编辑模式 |

---

## 用法示例

```python
from chestnut_studio.ui.cards.waveform_card import WaveformCard

# 创建卡片
waveform_card = WaveformCard()

# 连接信号
waveform_card.position_clicked.connect(self.on_position_clicked)
waveform_card.subtitle_created.connect(self.on_subtitle_created)

# 加载波形
success = waveform_card.load_waveform("video.mp4")

# 更新位置
waveform_card.update_position(15000)  # 15 秒

# 设置字幕叠加
waveform_card.set_subtitle_regions({1000: 3000, 5000: 7000})

# 设置 AB 循环区域
waveform_card.set_ab_loop_region(10000, 20000)

# 打轴操作
waveform_card.mark_subtitle_start()  # 标记开始点
waveform_card.mark_subtitle_end()    # 标记结束点

# 编辑模式
waveform_card.enter_edit_mode(1, 1000, 3000)  # 编辑列1的字幕
waveform_card.exit_edit_mode()  # 退出编辑模式
```

---

## 交互操作

| 操作 | 功能 |
|------|------|
| `左键点击` | 跳转到点击位置 |
| `Shift + 左键拖动` | 平移视窗 |
| `滚轮` | 缩放视窗（以鼠标位置为中心） |
| `I` 键 | 标记字幕开始点 / 编辑模式设为起点 |
| `O` 键 | 标记字幕结束点 / 编辑模式设为终点 |
| `Enter` | 确认编辑（编辑模式） |
| `Escape` | 取消编辑（编辑模式） |

---

## 缩放范围

- 默认视窗：30 秒
- 最小视窗：1 秒（约 1000x 放大）
- 最大视窗：10 分钟或视频总时长

---

## 波形显示

### 包络线

- 半透明蓝色填充区域
- 显示音频能量轮廓
- 使用 `compute_envelope()` 计算

### 原始波形

- 亮蓝色细线
- 显示音频细节
- 使用 `downsample_waveform()` 下采样

### 下采样策略

- 数据点限制在 5000 个
- 保留峰值特征
- 提升绘图性能

### Y 轴居中

- 上下各留 15% 空间
- 确保波形始终居中显示

---

## AB 循环区域

- 橙色虚线标记 A 点和 B 点
- 半透明橙色填充区域显示循环区间
- 与包络线和波形叠加显示

---

## 内部组件

| 组件 | 类型 | 说明 |
|------|------|------|
| `_plot_widget` | `WaveformPlotWidget` | pyqtgraph 绘图组件 |
| `_envelope_curve` | `PlotCurveItem` | 包络线曲线 |
| `_waveform_curve` | `PlotCurveItem` | 原始波形曲线 |
| `_red_line` | `InfiniteLine` | 红色播放位置线 |
| `_ab_loop_a_line` | `InfiniteLine` | AB 循环 A 点线 |
| `_ab_loop_b_line` | `InfiniteLine` | AB 循环 B 点线 |
| `_ab_loop_item` | `PlotCurveItem` | AB 循环填充区域 |
| `_zoom_label` | `QLabel` | 缩放倍数显示 |
| `_range_label` | `QLabel` | 视窗范围显示 |

---

## WaveformPlotWidget 子类

`WaveformPlotWidget(pg.PlotWidget)` — 自定义绘图组件：
- 重写 `wheelEvent` 实现滚轮缩放
- 重写 `mousePressEvent` 实现点击跳转和 Shift 拖动
- 重写 `mouseMoveEvent` / `mouseReleaseEvent` 实现拖动平移
- 自定义时间轴格式（mm:ss）
- 隐藏 Auto Range 按钮

---

## 注意事项

### 性能考虑

- 使用 `compute_envelope_fast()` 计算包络线
- 使用 `downsample_waveform()` 下采样波形
- 避免频繁重绘，使用定时器节流

### 打轴操作

- 打轴前确保波形已加载
- 开始点必须早于结束点
- 打轴完成后自动发射信号

### 编辑模式

- 编辑模式下禁用其他操作
- 编辑完成后自动退出编辑模式
- 取消编辑恢复原始状态

---

## 依赖

- PySide6: `QDockWidget`, `QWidget`, `QVBoxLayout`
- pyqtgraph: `PlotWidget`, `PlotCurveItem`, `InfiniteLine`
- chestnut_studio.core.audio: `load_waveform`, `compute_envelope_fast`, `downsample_waveform`
- chestnut_studio.utils.time_utils: `ms_to_time_str`
