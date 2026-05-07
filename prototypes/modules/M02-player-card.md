# M02 — 视频播放卡片

> `chestnut_studio/ui/cards/player_card.py`　｜　Phase 1　｜　视频渲染 + 播放控制

---

## 职责

- 视频文件播放（QMediaPlayer）
- 视频画面渲染（QGraphicsVideoItem）
- 字幕叠加预览（QGraphicsTextItem）
- 播放控制（播放/暂停/停止/音量/倍速）
- 进度条 + 时间显示
- 滚轮缩放视频窗口
- 拖放打开文件

---

## 类设计

```python
class PlayerCard(QDockWidget):
    """视频播放卡片"""
    
    # 信号
    position_changed = Signal(int)     # 播放位置变化 (ms)
    duration_changed = Signal(int)     # 视频时长变化 (ms)
    video_opened = Signal(str)         # 视频已打开 (path)
    
    def __init__(self, parent=None):
        super().__init__("视频预览", parent)
        self._video_path = ""
        self._duration = 0
        self._play_status = False
        self._volume = 100
        self._playback_rate = 1.0
        self._setup_ui()
        self._connect_signals()
    
    def _setup_ui(self):
        """初始化 UI"""
        # QGraphicsView + QGraphicsScene
        # QGraphicsVideoItem (视频画面)
        # QGraphicsTextItem (字幕叠加)
        # 进度条 + 时间标签
        # 播放控制按钮
        ...
    
    def open_video(self, path: str) -> bool:
        """打开视频文件"""
        ...
    
    def play(self):
        """播放"""
        ...
    
    def pause(self):
        """暂停"""
        ...
    
    def play_pause(self):
        """切换播放/暂停"""
        ...
    
    def set_position(self, ms: int):
        """设置播放位置"""
        ...
    
    def set_volume(self, value: int):
        """设置音量 0-100"""
        ...
    
    def set_playback_rate(self, rate: float):
        """设置倍速 0.1-2.0"""
        ...
    
    def update_subtitle_overlay(self, text: str, style: dict):
        """更新字幕叠加显示"""
        ...
```

---

## 内部组件

| 组件 | 类型 | 说明 |
|------|------|------|
| `_scene` | QGraphicsScene | 场景容器 |
| `_view` | QGraphicsView | 视图容器 |
| `_video_item` | QGraphicsVideoItem | 视频画面 |
| `_subtitle_item` | QGraphicsTextItem | 字幕叠加 |
| `_player` | QMediaPlayer | 播放器实例 |
| `_progress_slider` | QSlider | 进度条 |
| `_time_label` | QLabel | 时间显示 "00:00 / 05:30" |
| `_play_btn` | QPushButton | 播放/暂停按钮 |
| `_volume_slider` | QSlider | 音量滑块 |
| `_rate_combo` | QComboBox | 倍速选择 |

---

## 视频缩放

```python
# 8档预设分辨率
SIZE_PRESETS = {
    0: (640, 360),   1: (800, 450),   2: (1176, 664),   3: (1280, 720),
    4: (1366, 768),  5: (1600, 900),  6: (1920, 1080),  7: (2560, 1600),
}

def wheelEvent(self, event):
    delta = event.angleDelta().y()
    if delta > 0:
        self._size_index = min(self._size_index + 1, 7)
    else:
        self._size_index = max(self._size_index - 1, 0)
    self._apply_size()
```

---

## 拖放

```python
def dragEnterEvent(self, event):
    if event.mimeData().hasUrls():
        event.acceptProposedAction()

def dropEvent(self, event):
    path = event.mimeData().urls()[0].toLocalFile()
    ext = os.path.splitext(path)[1].lower()
    if ext in ['.mp4', '.avi', '.flv', '.mkv', '.mp3', '.wav', '.aac']:
        self.open_video(path)
    elif ext in ['.srt', '.ass', '.vtt', '.lrc']:
        # 发射信号，由 MainWindow 转发给 TimelineCard
        self.subtitle_dropped.emit(path)
```

---

## FFmpeg 视频信息解析

```python
def _parse_video_info(self, path: str) -> dict:
    """解析视频信息"""
    # 调用 chestnut_studio/core/ffmpeg.py
    return {
        'duration': 330000,      # ms
        'width': 1920,
        'height': 1080,
        'fps': 60.0,
        'bitrate': 2000,         # kbps
    }
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtMultimedia | QMediaPlayer |
| PySide6.QtMultimediaWidgets | QGraphicsVideoItem |
| chestnut_studio/core/ffmpeg.py | 视频信息解析 |
