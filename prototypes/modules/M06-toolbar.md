# M06 — 工具栏

> `chestnut_studio/ui/toolbar.py`　｜　Phase 1　｜　播放控制 + 全局操作

---

## 职责

- 打开文件按钮
- 播放控制（播放/暂停、静音、音量）
- 时间显示（当前时间 / 总时长）
- 进度条
- 倍速选择
- 间隔设置
- 导出按钮

---

## 布局

```
┌──────────────────────────────────────────────────────────────────────┐
│  📂打开  │  ▶播放  🔇静音  ━━━●━━━ 音量  │  00:00 / 05:30  │  ───●─── 进度条  │  1.0x▾  │  33ms▾  │  💾导出  │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 类设计

```python
class ToolBar(QToolBar):
    """主工具栏"""
    
    # 信号
    open_clicked = Signal()         # 打开文件
    play_clicked = Signal()         # 播放/暂停
    volume_changed = Signal(int)    # 音量变化
    position_changed = Signal(int)  # 进度条拖拽
    rate_changed = Signal(float)    # 倍速变化
    interval_changed = Signal(float) # 间隔变化
    export_clicked = Signal()       # 导出
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
```

---

## 组件清单

| 组件 | 类型 | 说明 |
|------|------|------|
| `_open_btn` | QPushButton | 打开文件 |
| `_play_btn` | QPushButton | 播放/暂停（图标切换） |
| `_mute_btn` | QPushButton | 静音 |
| `_volume_slider` | QSlider | 音量 0-100 |
| `_time_edit` | QLineEdit | 当前时间（可点击编辑跳转） |
| `_time_label` | QLabel | "/ 总时长" |
| `_progress_slider` | QSlider | 进度条 |
| `_rate_combo` | QComboBox | 倍速：0.1x ~ 2x |
| `_interval_combo` | QComboBox | 间隔：10ms ~ 1s |
| `_export_btn` | QPushButton | 导出字幕 |

---

## 倍速选项

```python
RATE_OPTIONS = [
    ("0.1x", 0.1), ("0.25x", 0.25), ("0.5x", 0.5), ("0.75x", 0.75),
    ("1.0x", 1.0), ("1.25x", 1.25), ("1.5x", 1.5), ("1.75x", 1.75),
    ("2.0x", 2.0),
]
```

---

## 间隔选项

```python
INTERVAL_OPTIONS = [
    ("10ms", 10), ("16ms (60fps)", 16.67), ("20ms", 20),
    ("33ms (30fps)", 33.33), ("50ms", 50), ("100ms", 100),
    ("200ms", 200), ("500ms", 500), ("1s", 1000),
]
```

---

## 方法

```python
def set_duration(self, ms: int):
    """设置视频总时长"""
    self._duration = ms
    self._progress_slider.setMaximum(ms)
    self._time_label.setText(f" / {self._ms_to_str(ms)}")

def update_position(self, ms: int):
    """更新当前播放位置"""
    self._time_edit.setText(self._ms_to_str(ms))
    self._progress_slider.setValue(ms)

def set_playing(self, playing: bool):
    """设置播放状态（切换图标）"""
    if playing:
        self._play_btn.setIcon(self._pause_icon)
    else:
        self._play_btn.setIcon(self._play_icon)
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtWidgets | QToolBar, QSlider, QComboBox |
| PySide6.QtGui | QIcon |
