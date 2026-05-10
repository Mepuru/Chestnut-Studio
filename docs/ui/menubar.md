# 菜单栏

> `chestnut_studio/ui/menubar.py`
> `MenuBar(QMenuBar)` — 应用菜单栏，支持自动生成的卡片和布局子菜单。

---

## 职责

- 文件菜单（打开视频、导入/导出字幕、退出）
- 视图菜单（卡片显示/隐藏、布局管理、全屏）— 支持自动生成
- 帮助菜单（快捷键说明）

---

## 自动生成支持

MenuBar 支持自动生成的子菜单：

```python
class MenuBar(QMenuBar):
    def set_card_submenu(self, submenu: QMenu):
        """设置自动生成的卡片子菜单"""
        self._card_submenu = submenu
        self._rebuild_view_menu()

    def set_layout_submenu(self, submenu: QMenu):
        """设置自动生成的布局子菜单"""
        self._layout_submenu = submenu
        self._rebuild_view_menu()
```

---

## 菜单结构

```
文件(F)
  ├── 打开视频(O)...      Ctrl+O
  ├── 导入字幕(I)...      Ctrl+I
  ├── 导出字幕(S)...      Ctrl+S
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
  └── 快捷键说明(K)...
```

---

## 信号

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

## 用法示例

```python
from chestnut_studio.ui.menubar import MenuBar

# 创建菜单栏
menu_bar = MenuBar()

# 连接信号
menu_bar.open_video.connect(self.on_open_video)
menu_bar.open_subtitle.connect(self.on_open_subtitle)
menu_bar.save_subtitle.connect(self.on_save_subtitle)
menu_bar.quit_app.connect(self.close)
menu_bar.toggle_fullscreen.connect(self.toggle_fullscreen)
menu_bar.reset_layout.connect(self.reset_layout)
```

---

## 菜单项详细说明

### 文件菜单

| 菜单项 | 快捷键 | 信号 | 说明 |
|--------|--------|------|------|
| 打开视频 | Ctrl+O | `open_video` | 打开视频文件对话框 |
| 导入字幕 | Ctrl+I | `open_subtitle` | 导入 SRT/ASS 字幕文件 |
| 导出字幕 | Ctrl+S | `save_subtitle` | 导出多轨道 ASS 文件 |
| 退出 | Ctrl+Q | `quit_app` | 退出应用 |

### 视图菜单

#### 卡片子菜单

| 菜单项 | 说明 |
|--------|------|
| 视频预览 | 显示/隐藏 PlayerCard |
| 时间轴 | 显示/隐藏 TimelineCard |
| 波形图 | 显示/隐藏 WaveformCard |
| 翻译 | 显示/隐藏 TranslateCard |

#### 布局子菜单

| 菜单项 | 信号 | 说明 |
|--------|------|------|
| 默认布局 | `reset_layout` | 重置为默认布局 |
| 打印当前布局 | `dump_layout` | 输出布局调试信息到控制台 |

| 菜单项 | 快捷键 | 信号 | 说明 |
|--------|--------|------|------|
| 全屏 | F11 | `toggle_fullscreen` | 切换全屏模式 |

### 帮助菜单

| 菜单项 | 说明 |
|--------|------|
| 快捷键说明 | 显示快捷键说明对话框 |

---

## 卡片显示/隐藏

通过 `QDockWidget.setVisible()` 控制卡片显示：

```python
# 切换卡片显示
self.player_card.setVisible(not self.player_card.isVisible())
```

菜单项会自动同步勾选状态。

---

## 全屏模式

### 进入全屏

- 隐藏菜单栏、工具栏、状态栏
- 隐藏所有卡片标题栏
- 窗口最大化

### 退出全屏

- 恢复菜单栏、工具栏、状态栏
- 恢复所有卡片标题栏
- 窗口恢复原始大小

---

## 注意事项

### 快捷键冲突

- 菜单快捷键会优先于卡片快捷键
- 避免在菜单和卡片中定义相同的快捷键

### 菜单状态同步

- 卡片显示/隐藏菜单项需要与卡片状态同步
- 全屏菜单项需要与全屏状态同步

---

## 依赖

- PySide6: `QMenuBar`, `QMenu`, `QAction`
