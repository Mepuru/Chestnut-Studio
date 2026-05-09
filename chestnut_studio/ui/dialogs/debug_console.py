"""调试控制台窗口"""

import sys
from io import StringIO

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class DebugConsole(QDialog):
    """调试控制台窗口

    功能：
    - 捕获 stderr/stdout 输出
    - 显示 FFmpeg 错误信息
    - 支持清空和复制
    """

    # 自定义流，用于捕获输出
    class StreamRedirector:
        """重定向流到信号"""

        def __init__(self, signal: Signal, original_stream=None):
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

    # 信号：输出文本
    output_received = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("调试控制台")
        self.setMinimumSize(600, 400)
        self.resize(700, 500)

        self._setup_ui()
        self._setup_redirect()

        # 存储原始流
        self._original_stderr = sys.stderr
        self._original_stdout = sys.stdout

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

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

        # 按钮栏
        btn_layout = QHBoxLayout()

        self.btn_clear = QPushButton("清空")
        self.btn_clear.clicked.connect(self.text_edit.clear)
        btn_layout.addWidget(self.btn_clear)

        self.btn_copy = QPushButton("复制全部")
        self.btn_copy.clicked.connect(self._copy_all)
        btn_layout.addWidget(self.btn_copy)

        btn_layout.addStretch()

        self.btn_close = QPushButton("关闭")
        self.btn_close.clicked.connect(self.close)
        btn_layout.addWidget(self.btn_close)

        layout.addLayout(btn_layout)

    def _setup_redirect(self):
        """设置输出重定向"""
        self.output_received.connect(self._append_text)

    def _append_text(self, text: str):
        """追加文本到显示区域"""
        self.text_edit.moveCursor(QTextCursor.End)
        self.text_edit.insertPlainText(text + "\n")
        self.text_edit.moveCursor(QTextCursor.End)

    def _copy_all(self):
        """复制全部内容"""
        self.text_edit.selectAll()
        self.text_edit.copy()
        # 取消选择
        cursor = self.text_edit.textCursor()
        cursor.clearSelection()
        self.text_edit.setTextCursor(cursor)

    def enable_redirect(self):
        """启用 stderr/stdout 重定向"""
        sys.stderr = self.StreamRedirector(self.output_received, self._original_stderr)
        sys.stdout = self.StreamRedirector(self.output_received, self._original_stdout)

    def disable_redirect(self):
        """禁用重定向，恢复原始流"""
        sys.stderr = self._original_stderr
        sys.stdout = self._original_stdout

    def log(self, text: str):
        """直接输出日志"""
        self.output_received.emit(text)

    def closeEvent(self, event):
        """关闭时恢复原始流"""
        self.disable_redirect()
        super().closeEvent(event)