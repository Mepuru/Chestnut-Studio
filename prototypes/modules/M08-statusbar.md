# M08 — 状态栏

> `src/ui/statusbar.py`　｜　Phase 0　｜　状态信息展示

---

## 职责

- 显示应用状态（就绪/加载中/导出中...）
- 显示视频参数（分辨率·帧率·码率）
- 显示当前播放时间（精确到毫秒）

---

## 布局

```
┌──────────────────────────────────────────────────────────────────────┐
│  就绪  │  1920×1080 · 60fps · 2000kbps  │  当前: 00:01:32.450        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 类设计

```python
class StatusBar(QStatusBar):
    """主状态栏"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        # 左：状态
        self._status_label = QLabel("就绪")
        self.addWidget(self._status_label, 1)
        
        # 中：视频参数
        self._info_label = QLabel("")
        self.addWidget(self._info_label, 1)
        
        # 右：当前时间
        self._time_label = QLabel("")
        self.addPermanentWidget(self._time_label)
    
    def set_status(self, text: str):
        """设置状态文本"""
        self._status_label.setText(text)
    
    def set_video_info(self, width: int, height: int, fps: float, bitrate: int):
        """设置视频参数"""
        self._info_label.setText(f"{width}×{height} · {fps:.1f}fps · {bitrate}kbps")
    
    def set_current_time(self, ms: int):
        """设置当前播放时间"""
        h, r = divmod(ms, 3600000)
        m, r = divmod(r, 60000)
        s, ms = divmod(r, 1000)
        self._time_label.setText(f"当前: {h:02d}:{m:02d}:{s:02d}.{ms:03d}")
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtWidgets | QStatusBar, QLabel |
