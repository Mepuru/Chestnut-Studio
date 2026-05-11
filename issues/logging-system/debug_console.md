# 调试控制台改造设计

> `chestnut_studio/ui/dialogs/debug_console.py`
> 调试控制台改造：移除 StreamRedirector，使用 LogManager

---

## 一、职责

- 显示日志输出
- 支持日志级别颜色区分
- 支持清空和复制
- 支持日志过滤（未来扩展）

---

## 二、改造方案

### 2.1 移除 StreamRedirector

```python
# 改造前：重定向 sys.stderr/stdout
class StreamRedirector:
    def __init__(self, signal, original_stream=None):
        self._signal = signal
        self._original = original_stream

    def write(self, text: str):
        if text.strip():
            self._signal.emit(text)
        if self._original:
            self._original.write(text)

    def flush(self):
        if self._original:
            self._original.flush()

# 改造后：使用 LogManager
class DebugConsole(QDialog):
    def _setup_logging(self):
        LogManager.instance().add_handler(self._on_log_record)
```

### 2.2 使用 LogManager 接收日志

```python
from chestnut_studio.utils.log_manager import LogManager, LogRecord, LogLevel

class DebugConsole(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("调试控制台")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)
        
        self._setup_ui()
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志处理"""
        LogManager.instance().add_handler(self._on_log_record)
    
    def _on_log_record(self, record: LogRecord):
        """处理日志记录"""
        # 根据级别设置颜色
        color_map = {
            LogLevel.DEBUG: "#6a9955",
            LogLevel.INFO: "#d4d4d4",
            LogLevel.WARNING: "#dcdcaa",
            LogLevel.ERROR: "#f44747",
        }
        color = color_map.get(record.level, "#d4d4d4")
        
        # 格式化消息
        formatted = f'<span style="color: {color};">[{record.source}] {record.message}</span>'
        
        # 追加到显示区域
        self.text_edit.append(formatted)
        self.text_edit.moveCursor(QTextCursor.End)
```

### 2.3 关闭时移除处理器

```python
class DebugConsole(QDialog):
    def closeEvent(self, event):
        """关闭时移除处理器"""
        LogManager.instance().remove_handler(self._on_log_record)
        super().closeEvent(event)
```

---

## 三、完整实现

```python
"""调试控制台窗口"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QWidget, QComboBox, QLabel
)
from PySide6.QtGui import QTextCursor

from chestnut_studio.utils.log_manager import LogManager, LogRecord, LogLevel


class DebugConsole(QDialog):
    """调试控制台窗口
    
    功能：
    - 显示日志输出
    - 支持日志级别颜色区分
    - 支持清空和复制
    - 支持日志级别过滤
    """
    
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("调试控制台")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)
        
        self._setup_ui()
        self._setup_logging()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 日志级别过滤
        toolbar_layout.addWidget(QLabel("日志级别:"))
        self.level_combo = QComboBox()
        self.level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.level_combo.currentTextChanged.connect(self._on_level_changed)
        toolbar_layout.addWidget(self.level_combo)
        
        toolbar_layout.addStretch()
        
        # 按钮
        btn_clear = QPushButton("清空")
        btn_clear.clicked.connect(self.text_edit.clear)
        toolbar_layout.addWidget(btn_clear)
        
        btn_copy = QPushButton("复制全部")
        btn_copy.clicked.connect(self._copy_all)
        toolbar_layout.addWidget(btn_copy)
        
        layout.addLayout(toolbar_layout)
        
        # 文本显示区域
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFontFamily("Consolas")
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.text_edit)
    
    def _setup_logging(self):
        """设置日志处理"""
        LogManager.instance().add_handler(self._on_log_record)
    
    def _on_log_record(self, record: LogRecord):
        """处理日志记录"""
        # 根据级别设置颜色
        color_map = {
            LogLevel.DEBUG: "#6a9955",
            LogLevel.INFO: "#d4d4d4",
            LogLevel.WARNING: "#dcdcaa",
            LogLevel.ERROR: "#f44747",
        }
        color = color_map.get(record.level, "#d4d4d4")
        
        # 格式化消息
        formatted = f'<span style="color: {color};">[{record.source}] {record.message}</span>'
        
        # 追加到显示区域
        self.text_edit.append(formatted)
        self.text_edit.moveCursor(QTextCursor.End)
    
    def _on_level_changed(self, level_text: str):
        """日志级别过滤变更"""
        level_map = {
            "DEBUG": LogLevel.DEBUG,
            "INFO": LogLevel.INFO,
            "WARNING": LogLevel.WARNING,
            "ERROR": LogLevel.ERROR,
        }
        level = level_map.get(level_text, LogLevel.DEBUG)
        LogManager.instance().set_min_level(level)
    
    def _copy_all(self):
        """复制全部内容"""
        self.text_edit.selectAll()
        self.text_edit.copy()
        cursor = self.text_edit.textCursor()
        cursor.clearSelection()
        self.text_edit.setTextCursor(cursor)
    
    def closeEvent(self, event):
        """关闭时移除处理器"""
        LogManager.instance().remove_handler(self._on_log_record)
        super().closeEvent(event)
```

---

## 四、与现有代码的对比

### 4.1 改造前

```python
# main_window.py
class MainWindow(QMainWindow):
    def _toggle_debug_console(self):
        from chestnut_studio.ui.dialogs.debug_console import DebugConsole
        
        if self._debug_console is None:
            self._debug_console = DebugConsole(self)
            self._debug_console.enable_redirect()  # 重定向 sys.stderr/stdout
            self._debug_console.show()
        elif self._debug_console.isVisible():
            self._debug_console.disable_redirect()
            self._debug_console.hide()
        else:
            self._debug_console.enable_redirect()
            self._debug_console.show()
```

### 4.2 改造后

```python
# main_window.py
class MainWindow(QMainWindow):
    def _toggle_debug_console(self):
        from chestnut_studio.ui.dialogs.debug_console import DebugConsole
        
        if self._debug_console is None:
            self._debug_console = DebugConsole(self)
            self._debug_console.show()
        elif self._debug_console.isVisible():
            self._debug_console.hide()
        else:
            self._debug_console.show()
```

---

## 五、注意事项

### 5.1 处理器注册/注销

- 打开调试控制台时注册处理器
- 关闭调试控制台时注销处理器
- 避免内存泄漏

### 5.2 线程安全

- Qt 信号机制是线程安全的
- 处理器调用在主线程中执行

### 5.3 性能影响

- 日志处理器会引入少量性能开销
- 对于热路径，可以考虑使用日志级别过滤

---

## 六、扩展性

### 6.1 日志搜索

```python
class DebugConsole(QDialog):
    def _setup_ui(self):
        # ...
        
        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索日志...")
        self.search_input.textChanged.connect(self._on_search)
        toolbar_layout.addWidget(self.search_input)
    
    def _on_search(self, text: str):
        """搜索日志"""
        # 高亮匹配的文本
        # ...
```

### 6.2 日志导出

```python
class DebugConsole(QDialog):
    def _setup_ui(self):
        # ...
        
        # 导出按钮
        btn_export = QPushButton("导出")
        btn_export.clicked.connect(self._export_log)
        toolbar_layout.addWidget(btn_export)
    
    def _export_log(self):
        """导出日志"""
        path, _ = QFileDialog.getSaveFileName(
            self, "导出日志", "", "日志文件 (*.log)"
        )
        if path:
            with open(path, "w") as f:
                f.write(self.text_edit.toPlainText())
```

### 6.3 日志自动滚动

```python
class DebugConsole(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        # ...
        self._auto_scroll = True
    
    def _on_log_record(self, record: LogRecord):
        """处理日志记录"""
        # ...
        
        # 自动滚动
        if self._auto_scroll:
            self.text_edit.moveCursor(QTextCursor.End)
    
    def _on_scroll(self):
        """滚动事件"""
        # 如果用户手动滚动，停止自动滚动
        scrollbar = self.text_edit.verticalScrollBar()
        if scrollbar.value() < scrollbar.maximum():
            self._auto_scroll = False
        else:
            self._auto_scroll = True
```
