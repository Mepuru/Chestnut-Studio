"""输入栏模块

视频播放器下方的输入栏，用于添加笔记。
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from chestnut_studio.core.note_manager import NOTE_TYPES
from chestnut_studio.resources import get_icon_path
from chestnut_studio.utils.time_utils import ms_to_time_str


class InputBar(QWidget):
    """输入栏组件"""

    note_sent = Signal(str, int, str)  # (type, timestamp_ms, text)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timestamp_ms: int = 0
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("inputBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # ── 类型选择 ──
        self._type_combo = QComboBox()
        self._type_combo.setObjectName("typeCombo")
        for t in NOTE_TYPES:
            self._type_combo.addItem(t)
        self._type_combo.setFixedWidth(84)
        layout.addWidget(self._type_combo)

        # ── 输入框 ──
        self._input = QLineEdit()
        self._input.setObjectName("noteInput")
        self._input.setPlaceholderText("输入翻译或笔记...")
        self._input.returnPressed.connect(self._send)
        layout.addWidget(self._input, 1)

        # ── 时间戳显示 ──
        self._time_label = QLabel("00:00.00")
        self._time_label.setObjectName("timeLabel")
        layout.addWidget(self._time_label)

        # ── 发送按钮 ──
        self._send_btn = QPushButton("发送")
        self._send_btn.setObjectName("sendBtn")
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.clicked.connect(self._send)
        layout.addWidget(self._send_btn)

    def set_timestamp(self, ms: int):
        """更新当前视频时间戳显示"""
        self._timestamp_ms = ms
        self._time_label.setText(ms_to_time_str(ms))

    def set_current_track(self, track: int):
        """用 Ctrl+数字 切换轨道（1-4）"""
        if 1 <= track <= len(NOTE_TYPES):
            self._type_combo.setCurrentIndex(track - 1)

    def load_for_edit(self, note_type: str, text: str):
        """载入笔记到输入框方便修改"""
        if note_type in NOTE_TYPES:
            self._type_combo.setCurrentText(note_type)
        self._input.setText(text)
        self._input.setFocus()
        self._input.selectAll()

    def _send(self):
        """发送笔记"""
        text = self._input.text().strip()
        if not text:
            return
        note_type = self._type_combo.currentText()
        self.note_sent.emit(note_type, self._timestamp_ms, text)
        self._input.clear()
        self._input.setFocus()
