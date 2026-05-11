"""调试控制台窗口

使用 LogManager 接收日志，支持日志级别颜色区分和过滤。
"""

from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from chestnut_studio.utils.log_manager import LogLevel, LogManager, LogRecord


class DebugConsole(QDialog):
    """调试控制台窗口

    功能：
    - 显示日志输出（通过 LogManager）
    - 支持日志级别颜色区分
    - 支持清空和复制
    - 支持日志级别过滤
    """

    # 日志级别颜色映射
    LEVEL_COLORS = {
        LogLevel.DEBUG: "#6a9955",
        LogLevel.INFO: "#d4d4d4",
        LogLevel.WARNING: "#dcdcaa",
        LogLevel.ERROR: "#f44747",
    }

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
        btn_clear.clicked.connect(lambda: self.text_edit.clear())
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
        color = self.LEVEL_COLORS.get(record.level, "#d4d4d4")

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
