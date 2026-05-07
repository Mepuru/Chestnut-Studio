# M01 — 主窗口框架

> `chestnut_studio/ui/main_window.py`　｜　Phase 0　｜　所有卡片的容器

---

## 职责

- 继承 `QMainWindow`，作为应用主窗口
- 管理四张 QDockWidget 卡片的创建、布局、停靠
- 承载菜单栏、工具栏、状态栏
- 布局保存/恢复（QSettings）
- 全局快捷键分发

---

## 类设计

```python
class MainWindow(QMainWindow):
    """主窗口"""
    
    # 信号
    video_opened = Signal(str)      # 视频已打开
    position_changed = Signal(int)  # 播放位置变化
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chestnut Studio")
        self._init_docks()
        self._init_menubar()
        self._init_toolbar()
        self._init_statusbar()
        self._restore_layout()
    
    def _init_docks(self):
        """创建四张卡片"""
        self.player_card = PlayerCard(self)
        self.timeline_card = TimelineCard(self)
        self.waveform_card = WaveformCard(self)
        self.translate_card = TranslateCard(self)
        
        # 设置停靠区域
        self.addDockWidget(Qt.LeftDockWidgetArea, self.player_card)
        self.addDockWidget(Qt.RightDockWidgetArea, self.timeline_card)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.waveform_card)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.translate_card)
        
        # 标签页合并（波形图 + 翻译）
        self.tabifyDockWidget(self.waveform_card, self.translate_card)
    
    def _restore_layout(self):
        """恢复上次布局"""
        settings = QSettings("ChestnutStudio", "KaoRouTool")
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
            self.restoreState(settings.value("state"))
        else:
            self._apply_default_layout()
    
    def _save_layout(self):
        """保存当前布局"""
        settings = QSettings("ChestnutStudio", "KaoRouTool")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
    
    def closeEvent(self, event):
        """关闭时保存布局"""
        self._save_layout()
        super().closeEvent(event)
```

---

## 卡片间信号连接

```python
def _connect_signals(self):
    # 播放器 → 波形图
    self.player_card.position_changed.connect(
        self.waveform_card.update_position
    )
    
    # 播放器 → 时间轴
    self.player_card.position_changed.connect(
        self.timeline_card.highlight_row
    )
    
    # 波形图 → 播放器
    self.waveform_card.position_clicked.connect(
        self.player_card.set_position
    )
    
    # 时间轴 → 翻译面板
    self.timeline_card.subtitle_selected.connect(
        self.translate_card.show_subtitle
    )
    
    # 视频打开后
    self.player_card.video_opened.connect(
        self._on_video_opened
    )
```

---

## 预设布局方案

```python
def apply_layout_default(self):
    """默认布局：上左右下"""
    self.resetLayout()
    self.addDockWidget(Qt.LeftDockWidgetArea, self.player_card)
    self.splitDockWidget(self.player_card, self.timeline_card, Qt.Horizontal)
    self.addDockWidget(Qt.BottomDockWidgetArea, self.waveform_card)
    self.splitDockWidget(self.waveform_card, self.translate_card, Qt.Horizontal)

def apply_layout_timeline_focus(self):
    """打轴优先：视频最小化，时间轴最大化"""
    ...

def apply_layout_fullscreen_timeline(self):
    """全屏打轴：视频隐藏，时间轴占满"""
    ...
```

---

## 依赖

| 组件 | 来源 |
|------|------|
| PlayerCard | `chestnut_studio/ui/cards/player_card.py` |
| TimelineCard | `chestnut_studio/ui/cards/timeline_card.py` |
| WaveformCard | `chestnut_studio/ui/cards/waveform_card.py` |
| TranslateCard | `chestnut_studio/ui/cards/translate_card.py` |
| MenuBar | `chestnut_studio/ui/menubar.py` |
| ToolBar | `chestnut_studio/ui/toolbar.py` |
| StatusBar | `chestnut_studio/ui/statusbar.py` |
