# M07 — 菜单栏

> `chestnut_studio/ui/menubar.py`　｜　Phase 0　｜　应用菜单

---

## 职责

- 文件菜单：打开视频、导入字幕、导出字幕、退出
- 视图菜单：卡片显示/隐藏、布局方案切换
- 帮助菜单：快捷键说明

---

## 菜单结构

```
文件(F)
  ├── 打开视频...          Ctrl+O
  ├── 导入字幕...          Ctrl+I
  ├── 导出字幕...          Ctrl+S
  ├── ────────────
  └── 退出                Ctrl+Q

视图(V)
  ├── 卡片
  │   ├── ☑ 视频预览
  │   ├── ☑ 时间轴
  │   ├── ☑ 波形图
  │   └── ☑ 翻译
  ├── ────────────
  ├── 布局
  │   ├── 默认布局
  │   ├── 打轴优先
  │   ├── 全屏打轴
  │   └── ────────────
  │   └── 保存当前布局
  ├── ────────────
  └── 全屏                F11

帮助(H)
  └── 快捷键说明
```

---

## 类设计

```python
class MenuBar(QMenuBar):
    """主菜单栏"""
    
    # 信号
    open_video = Signal()
    import_subtitle = Signal()
    export_subtitle = Signal()
    toggle_fullscreen = Signal()
    layout_changed = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_file_menu()
        self._setup_view_menu()
        self._setup_help_menu()
    
    def _setup_file_menu(self):
        file_menu = self.addMenu("文件(&F)")
        file_menu.addAction("打开视频...", self.open_video.emit, "Ctrl+O")
        file_menu.addAction("导入字幕...", self.import_subtitle.emit, "Ctrl+I")
        file_menu.addAction("导出字幕...", self.export_subtitle.emit, "Ctrl+S")
        file_menu.addSeparator()
        file_menu.addAction("退出", self.window().close, "Ctrl+Q")
    
    def _setup_view_menu(self):
        view_menu = self.addMenu("视图(&V)")
        # 卡片子菜单
        cards_menu = view_menu.addMenu("卡片")
        # 由 MainWindow 添加 toggleViewAction
        self._cards_menu = cards_menu
        
        view_menu.addSeparator()
        # 布局子菜单
        layout_menu = view_menu.addMenu("布局")
        layout_menu.addAction("默认布局", lambda: self.layout_changed.emit("default"))
        layout_menu.addAction("打轴优先", lambda: self.layout_changed.emit("timeline_focus"))
        layout_menu.addAction("全屏打轴", lambda: self.layout_changed.emit("fullscreen_timeline"))
        layout_menu.addSeparator()
        layout_menu.addAction("保存当前布局", lambda: self.layout_changed.emit("save"))
        
        view_menu.addSeparator()
        view_menu.addAction("全屏", self.toggle_fullscreen.emit, "F11")
    
    def add_card_toggle_action(self, action):
        """添加卡片显示/隐藏的切换动作"""
        self._cards_menu.addAction(action)
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| PySide6.QtWidgets | QMenuBar, QMenu, QAction |
