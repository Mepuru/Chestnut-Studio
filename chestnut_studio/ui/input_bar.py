"""输入栏模块

视频播放器下方的输入栏，用于添加笔记。
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
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
    """输入栏组件

    包含笔记类型选择（字幕/画面）、文本输入框、发送按钮。
    发送时发出 note_sent 信号。
    """

    note_sent = Signal(str, int, str)  # (type, timestamp_ms, text)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_type: str = NOTE_TYPES[0]  # 默认"字幕"
        self._timestamp_ms: int = 0
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("inputBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # ── 类型选择（分段按钮） ──
        self._type_btns = {}
        type_group = QHBoxLayout()
        type_group.setSpacing(0)
        for i, t in enumerate(NOTE_TYPES):
            btn = QPushButton(t)
            btn.setObjectName(f"typeBtn_{t}")
            btn.setCheckable(True)
            btn.setChecked(t == self._current_type)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, t=t: self._set_type(t))
            if i == 0:
                btn.setProperty("class", "typeBtnFirst")
            elif i == len(NOTE_TYPES) - 1:
                btn.setProperty("class", "typeBtnLast")
            else:
                btn.setProperty("class", "typeBtnMid")
            self._type_btns[t] = btn
            type_group.addWidget(btn)
        layout.addLayout(type_group)

        # ── 时间戳显示 ──
        self._time_label = QLabel("00:00")
        self._time_label.setObjectName("timeLabel")
        self._time_label.setFixedWidth(56)
        layout.addWidget(self._time_label)

        # ── 输入框 ──
        self._input = QLineEdit()
        self._input.setObjectName("noteInput")
        self._input.setPlaceholderText("输入翻译或笔记...")
        self._input.returnPressed.connect(self._send)
        layout.addWidget(self._input, 1)

        # ── 发送按钮 ──
        self._send_btn = QPushButton()
        self._send_btn.setObjectName("sendBtn")
        self._send_btn.setIcon(QIcon(str(get_icon_path("send"))))
        self._send_btn.setIconSize(self._send_btn.sizeHint() * 1.2)
        self._send_btn.setToolTip("发送笔记")
        self._send_btn.setCursor(Qt.PointingHandCursor)
        self._send_btn.clicked.connect(self._send)
        layout.addWidget(self._send_btn)

    def _set_type(self, t: str):
        """切换笔记类型"""
        if t == self._current_type:
            return
        self._current_type = t
        for type_name, btn in self._type_btns.items():
            btn.setChecked(type_name == t)

    def set_timestamp(self, ms: int):
        """更新当前视频时间戳显示"""
        self._timestamp_ms = ms
        self._time_label.setText(ms_to_time_str(ms))

    def _send(self):
        """发送笔记"""
        text = self._input.text().strip()
        if not text:
            return
        self.note_sent.emit(self._current_type, self._timestamp_ms, text)
        self._input.clear()
        self._input.setFocus()

    def get_current_type(self) -> str:
        return self._current_type
