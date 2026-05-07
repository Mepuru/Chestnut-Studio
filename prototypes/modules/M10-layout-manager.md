# M10 — 布局管理

> `chestnut_studio/utils/layout_manager.py`　｜　Phase 5　｜　布局保存/恢复/预设
> **注意：此模块尚未实现，布局管理功能目前集成在 MainWindow 中**

---

## 职责

- 布局保存（QSettings）
- 布局恢复
- 预设布局方案
- 全屏切换

---

## 类设计

```python
class LayoutManager:
    """布局管理器"""
    
    def __init__(self, main_window):
        self._main = main_window
        self._settings = QSettings("ChestnutStudio", "KaoRouTool")
    
    def save(self):
        """保存当前布局"""
        self._settings.setValue("geometry", self._main.saveGeometry())
        self._settings.setValue("state", self._main.saveState())
    
    def restore(self) -> bool:
        """恢复上次布局，返回是否成功"""
        if self._settings.contains("geometry"):
            self._main.restoreGeometry(self._settings.value("geometry"))
            self._main.restoreState(self._settings.value("state"))
            return True
        return False
    
    def apply_preset(self, name: str):
        """应用预设布局"""
        method = getattr(self, f"_preset_{name}", None)
        if method:
            method()
    
    def _preset_default(self):
        """默认布局：上左右下"""
        main = self._main
        main.resetLayout()
        main.addDockWidget(Qt.LeftDockWidgetArea, main.player_card)
        main.splitDockWidget(main.player_card, main.timeline_card, Qt.Horizontal)
        main.addDockWidget(Qt.BottomDockWidgetArea, main.waveform_card)
        main.splitDockWidget(main.waveform_card, main.translate_card, Qt.Horizontal)
        # 调整大小比例
        main.resizeDocks(
            [main.player_card, main.timeline_card],
            [int(main.width() * 0.55), int(main.width() * 0.45)],
            Qt.Horizontal
        )
    
    def _preset_timeline_focus(self):
        """打轴优先：视频+打轴左右并列，波形+翻译底部折叠"""
        main = self._main
        main.resetLayout()
        main.addDockWidget(Qt.LeftDockWidgetArea, main.player_card)
        main.splitDockWidget(main.player_card, main.timeline_card, Qt.Horizontal)
        main.addDockWidget(Qt.BottomDockWidgetArea, main.waveform_card)
        main.tabifyDockWidget(main.waveform_card, main.translate_card)
        main.resizeDocks(
            [main.player_card, main.timeline_card],
            [int(main.width() * 0.4), int(main.width() * 0.6)],
            Qt.Horizontal
        )
    
    def _preset_fullscreen_timeline(self):
        """全屏打轴：视频隐藏，时间轴最大化"""
        main = self._main
        main.resetLayout()
        main.player_card.hide()
        main.addDockWidget(Qt.LeftDockWidgetArea, main.timeline_card)
        main.addDockWidget(Qt.BottomDockWidgetArea, main.waveform_card)
        main.tabifyDockWidget(main.waveform_card, main.translate_card)
    
    def toggle_fullscreen(self):
        """切换全屏"""
        if self._main.isFullScreen():
            self._main.showNormal()
        else:
            self._main.showFullScreen()
```

---

## 预设方案

| 名称 | 说明 |
|------|------|
| `default` | 默认布局：视频左上、时间轴右上、波形左下、翻译右下 |
| `timeline_focus` | 打轴优先：视频40%、时间轴60%、波形/翻译底部标签页 |
| `fullscreen_timeline` | 全屏打轴：视频隐藏、时间轴占满 |

---

## QSettings 键值

| 键 | 类型 | 说明 |
|------|------|------|
| `geometry` | QByteArray | 窗口几何信息 |
| `state` | QByteArray | DockWidget 布局状态 |

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtCore | QSettings |
| PySide6.QtWidgets | QMainWindow |
