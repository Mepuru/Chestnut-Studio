# M09 — 主题样式

> `chestnut_studio/resources/style.qss`　｜　Phase 0　｜　暗色主题视觉规范
> **注意：icons/ 目录尚未实现，图标功能暂未启用**

---

## 色彩系统

| 用途 | 色值 | 说明 |
|------|------|------|
| 背景主色 | `#1e1e2e` | 深蓝灰，窗口背景 |
| 背景次色 | `#232629` | 工具栏/状态栏 |
| 卡片背景 | `#2b2d30` | 卡片内容区 |
| 卡片标题栏 | `#313338` | 标题栏背景 |
| 边框 | `#3f4147` | 卡片边框、分割线 |
| 文字主色 | `#e0e0e0` | 主要文字 |
| 文字次色 | `#9ca3af` | 次要文字、提示 |
| 强调色 | `#3daee9` | 选中状态、链接、按钮高亮 |
| 危险色 | `#e74c3c` | 删除、警告 |
| 成功色 | `#2ecc71` | 保存成功 |
| 字幕条蓝 | `#35545d` | 正常持续时间 |
| 字幕条橙 | `#FA8072` | 持续时间 > 4.5s |
| 字幕条红 | `#B22222` | 持续时间异常 |
| 红线 | `#d93c30` | 播放位置指示 |

---

## QSS 样式表

### 主窗口

```css
QMainWindow {
    background: #1e1e2e;
}

QMenuBar {
    background: #232629;
    color: #e0e0e0;
    border-bottom: 1px solid #3f4147;
}

QMenuBar::item:selected {
    background: #3daee9;
}

QMenu {
    background: #2b2d30;
    color: #e0e0e0;
    border: 1px solid #3f4147;
}

QMenu::item:selected {
    background: #3daee9;
}
```

### 卡片（QDockWidget）

```css
QDockWidget {
    background: #2b2d30;
    border: 1px solid #3f4147;
    border-radius: 8px;
    titlebar-close-icon: url(close.svg);
    titlebar-normal-icon: url(float.svg);
}

QDockWidget::title {
    background: #313338;
    padding: 6px 12px;
    border-radius: 8px 8px 0 0;
    text-align: left;
    font-weight: bold;
    color: #e0e0e0;
}

QDockWidget[floating="true"] {
    border: 1px solid #3daee9;
}
```

### 工具栏

```css
QToolBar {
    background: #232629;
    border-bottom: 1px solid #3f4147;
    padding: 4px 8px;
    spacing: 8px;
}

QToolBar::separator {
    width: 1px;
    background: #3f4147;
    margin: 4px 8px;
}
```

### 按钮

```css
QPushButton {
    background: #313338;
    border: 1px solid #3f4147;
    border-radius: 4px;
    padding: 4px 12px;
    color: #e0e0e0;
}

QPushButton:hover {
    background: #3daee9;
    border-color: #3daee9;
}

QPushButton:pressed {
    background: #2d8bb8;
}

QPushButton:disabled {
    background: #2b2d30;
    color: #666;
}
```

### 输入框

```css
QLineEdit, QTextEdit, QPlainTextEdit {
    background: #1e1e2e;
    border: 1px solid #3f4147;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
}

QLineEdit:focus, QTextEdit:focus {
    border-color: #3daee9;
}
```

### 下拉框

```css
QComboBox {
    background: #313338;
    border: 1px solid #3f4147;
    border-radius: 4px;
    padding: 4px 8px;
    color: #e0e0e0;
}

QComboBox:hover {
    border-color: #3daee9;
}

QComboBox::drop-down {
    border: none;
}
```

### 滑块

```css
QSlider::groove:horizontal {
    height: 4px;
    background: #3f4147;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    width: 12px;
    height: 12px;
    margin: -4px 0;
    background: #3daee9;
    border-radius: 6px;
}

QSlider::sub-page:horizontal {
    background: #3daee9;
    border-radius: 2px;
}
```

### 表格

```css
QTableWidget {
    background: #1e1e2e;
    border: 1px solid #3f4147;
    color: #e0e0e0;
    gridline-color: #3f4147;
}

QTableWidget::item {
    padding: 2px;
}

QTableWidget::item:selected {
    background: rgba(61, 174, 233, 0.3);
}

QHeaderView::section {
    background: #313338;
    color: #e0e0e0;
    border: 1px solid #3f4147;
    padding: 4px;
}
```

### 滚动条

```css
QScrollBar:vertical {
    background: #232629;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #3f4147;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #3daee9;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: #232629;
    height: 8px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background: #3f4147;
    border-radius: 4px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #3daee9;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
```

### 状态栏

```css
QStatusBar {
    background: #232629;
    color: #9ca3af;
    border-top: 1px solid #3f4147;
}
```

### 进度条

```css
QProgressBar {
    background: #1e1e2e;
    border: 1px solid #3f4147;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background: #3daee9;
    border-radius: 3px;
}
```

---

## 依赖

| 依赖 | 用途 |
|------|------|
| QSS 文件 | 通过 `app.setStyleSheet()` 加载 |
| SVG 图标 | 卡片标题栏控制按钮 |
