"""输入栏模块

视频播放器下方的输入栏，用于添加笔记。
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from chestnut_studio.core.track_config import NOTE_TYPES
from chestnut_studio.core.track_config import get_track_color
from chestnut_studio.utils.time_utils import ms_to_time_str


class InputBar(QWidget):
    """输入栏组件"""

    note_sent = Signal(str, int, str)  # (type, timestamp_ms, text)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._timestamp_ms: int = 0
        self._current_track_idx: int = 0  # 默认轨道1
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("inputBar")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # ── 轨道指示器（色块 + 轨道名） ──
        self._color_dot = QLabel()
        self._color_dot.setFixedSize(10, 10)
        self._color_dot.setObjectName("colorDot")
        layout.addWidget(self._color_dot)

        self._track_label = QLabel("轨道1")
        self._track_label.setObjectName("trackLabel")
        layout.addWidget(self._track_label)

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

        self._update_badge()

    def _update_badge(self):
        """更新轨道色块和名称"""
        track_num = self._current_track_idx + 1
        color = get_track_color(track_num)
        self._color_dot.setStyleSheet(
            f"background: {color}; border-radius: 5px;"
        )
        self._track_label.setText(NOTE_TYPES[self._current_track_idx])
        self._track_label.setStyleSheet(f"color: {color};")

    def set_timestamp(self, ms: int):
        """更新当前视频时间戳显示"""
        self._timestamp_ms = ms
        self._time_label.setText(ms_to_time_str(ms))

    def set_current_track(self, track: int):
        """用 Ctrl+数字 切换轨道（1~9=轨道1~9, 0=轨道10）"""
        idx = 9 if track == 0 else track - 1
        if 0 <= idx < len(NOTE_TYPES):
            self._current_track_idx = idx
            self._update_badge()

    def get_current_track_type(self) -> str:
        return NOTE_TYPES[self._current_track_idx]

    term_added = Signal(str, str, str, str)  # (source, translation, origin, note)

    def _add_term(self):
        """打开术语对话框"""
        from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit,
                                       QTextEdit, QPushButton, QHBoxLayout)

        dialog = QDialog(self)
        dialog.setWindowTitle("积累")
        dialog.setMinimumSize(450, 400)
        layout = QVBoxLayout(dialog)
        layout.setSpacing(6)

        layout.addWidget(QLabel("原文（日语）:"))
        source_edit = QLineEdit()
        source_edit.setPlaceholderText("遇到不会的日语词/句...")
        layout.addWidget(source_edit)

        layout.addWidget(QLabel("译文（中文）:"))
        trans_edit = QLineEdit()
        trans_edit.setPlaceholderText("对应的中文翻译...")
        layout.addWidget(trans_edit)

        layout.addWidget(QLabel("出处:"))
        origin_edit = QLineEdit()
        origin_edit.setPlaceholderText("出自哪部作品/哪一集/时间...")
        layout.addWidget(origin_edit)

        layout.addWidget(QLabel("备注:"))
        note_edit = QTextEdit()
        note_edit.setPlaceholderText("语法说明、用法注意、相关词汇...")
        note_edit.setMinimumHeight(100)
        layout.addWidget(note_edit)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(dialog.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

        source_edit.setFocus()
        if dialog.exec() == QDialog.Accepted:
            source = source_edit.text().strip()
            trans = trans_edit.text().strip()
            origin = origin_edit.text().strip()
            note = note_edit.text().strip()
            if source and trans:
                self.term_added.emit(source, trans, origin, note)

    def load_for_edit(self, note_type: str, text: str):
        """载入笔记到输入框方便修改"""
        if note_type in NOTE_TYPES:
            self._current_track_idx = NOTE_TYPES.index(note_type)
            self._update_badge()
        self._input.setText(text)
        self._input.setFocus()
        self._input.selectAll()

    def _send(self):
        """发送笔记"""
        text = self._input.text().strip()
        if not text:
            return
        note_type = self.get_current_track_type()
        self.note_sent.emit(note_type, self._timestamp_ms, text)
        self._input.clear()
        self._input.setFocus()
