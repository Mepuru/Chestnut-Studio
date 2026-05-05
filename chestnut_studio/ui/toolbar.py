"""工具栏模块"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QSizePolicy,
    QToolBar,
    QWidget,
)

# 按钮统一样式
BTN_STYLE = """
    QPushButton {
        background: #27272a;
        border: 1px solid #3f3f46;
        color: #e4e4e7;
        font-size: 9pt;
        padding: 2px 8px;
    }
    QPushButton:hover {
        background: #3f3f46;
    }
    QPushButton:pressed {
        background: #18181b;
    }
"""


class ToolBar(QToolBar):
    """主工具栏

    布局：
    [帧号] | [后退5秒] [播放/暂停] [前进5秒] | [倍速]
    """

    # 信号
    play_clicked = Signal()  # 播放/暂停
    skip_forward = Signal(int)  # 前进 ms
    skip_backward = Signal(int)  # 后退 ms
    rate_changed = Signal(float)  # 倍速变化

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0
        self._position = 0
        self._fps = 30.0
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI"""
        self.setMovable(False)
        self.setFloatable(False)

        # --- 最左侧：帧号 ---
        self._frame_label = QLabel("0 | 帧")
        self._frame_label.setFixedWidth(90)
        self._frame_label.setAlignment(Qt.AlignCenter)
        self._frame_label.setStyleSheet(
            "color: #a1a1aa; font-size: 9pt; font-family: Consolas, monospace;"
        )

        # --- 中央：播放控制 ---
        self._skip_back_btn = QPushButton("<<5s")
        self._skip_back_btn.setFixedSize(52, 28)
        self._skip_back_btn.setToolTip("后退 5 秒")
        self._skip_back_btn.setStyleSheet(BTN_STYLE)
        self._skip_back_btn.clicked.connect(lambda: self.skip_backward.emit(5000))

        self._play_btn = QPushButton("播放")
        self._play_btn.setFixedSize(56, 28)
        self._play_btn.setToolTip("播放/暂停 (Space)")
        self._play_btn.setStyleSheet(BTN_STYLE)
        self._play_btn.clicked.connect(self.play_clicked.emit)

        self._skip_fwd_btn = QPushButton("5s>>")
        self._skip_fwd_btn.setFixedSize(52, 28)
        self._skip_fwd_btn.setToolTip("前进 5 秒")
        self._skip_fwd_btn.setStyleSheet(BTN_STYLE)
        self._skip_fwd_btn.clicked.connect(lambda: self.skip_forward.emit(5000))

        # --- 最右侧：倍速 ---
        self._rate_combo = QComboBox()
        self._rate_combo.setFixedWidth(80)
        self._rate_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self._rate_combo.setCurrentText("1.0x")
        self._rate_combo.currentTextChanged.connect(self._on_rate_changed)

        # --- 布局 ---
        self.addWidget(self._frame_label)
        self._add_separator()

        left_spacer = QWidget()
        left_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(left_spacer)

        self.addWidget(self._skip_back_btn)
        self._add_spacing(6)
        self.addWidget(self._play_btn)
        self._add_spacing(6)
        self.addWidget(self._skip_fwd_btn)

        right_spacer = QWidget()
        right_spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.addWidget(right_spacer)

        self._add_separator()
        rate_label = QLabel("倍速")
        rate_label.setStyleSheet("color: #52525b; font-size: 9pt;")
        self.addWidget(rate_label)
        self._add_spacing(4)
        self.addWidget(self._rate_combo)

    def _add_separator(self):
        """添加分隔线"""
        sep = QWidget()
        sep.setFixedSize(1, 20)
        sep.setStyleSheet("background: #27272a; margin: 0 6px;")
        self.addWidget(sep)

    def _add_spacing(self, width: int):
        """添加间距"""
        spacer = QWidget()
        spacer.setFixedSize(width, 1)
        spacer.setStyleSheet("background: transparent;")
        self.addWidget(spacer)

    # ========== 公有方法 ==========

    def set_fps(self, fps: float):
        """设置视频帧率"""
        self._fps = fps if fps > 0 else 30.0

    def set_duration(self, ms: int):
        """设置视频总时长"""
        self._duration = ms

    def update_position(self, ms: int):
        """更新当前播放位置，刷新帧号"""
        self._position = ms
        frame = int(ms * self._fps / 1000) if self._fps > 0 else 0
        self._frame_label.setText(f"{frame} | 帧")

    def set_playing(self, playing: bool):
        """设置播放状态"""
        if playing:
            self._play_btn.setText("暂停")
            self._play_btn.setToolTip("暂停 (Space)")
        else:
            self._play_btn.setText("播放")
            self._play_btn.setToolTip("播放 (Space)")

    def set_playback_rate(self, rate: float):
        """设置倍速"""
        text = f"{rate}x"
        idx = self._rate_combo.findText(text)
        if idx >= 0:
            self._rate_combo.setCurrentIndex(idx)

    # ========== 内部方法 ==========

    def _on_rate_changed(self, text: str):
        """倍速选择变化"""
        try:
            rate = float(text.replace("x", ""))
            self.rate_changed.emit(rate)
        except ValueError:
            pass
