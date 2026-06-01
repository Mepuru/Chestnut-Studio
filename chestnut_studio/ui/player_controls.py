"""播放控制栏模块

视频播放器下方的控制栏：进度条、播放/暂停、音量、倍速等。
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QSlider,
    QWidget,
)

from chestnut_studio.resources import get_icon_path
from chestnut_studio.utils.time_utils import ms_to_time_str


class PlayerControls(QWidget):
    """播放控制栏

    提供播放/暂停、进度跳转、音量控制、倍速切换等功能。
    发出用户交互信号供 PlayerCard 或 MainWindow 消费。
    """

    # ── 信号 ──
    play_pause_clicked = Signal()
    skip_back_clicked = Signal()
    skip_forward_clicked = Signal()
    seek_requested = Signal(int)  # 拖动进度条到指定毫秒
    volume_changed = Signal(int)  # 0-100
    rate_changed = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_playing = False
        self._duration = 0
        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("playerControls")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)
        layout.setSpacing(6)

        # ── 播放/暂停 ──
        self._play_btn = QPushButton()
        self._play_btn.setObjectName("playBtn")
        self._play_btn.setIcon(QIcon(str(get_icon_path("play"))))
        self._play_btn.setIconSize(self._play_btn.sizeHint() * 1.5)
        self._play_btn.setToolTip("播放/暂停 (Space)")
        self._play_btn.setCursor(Qt.PointingHandCursor)
        self._play_btn.clicked.connect(self.play_pause_clicked.emit)
        layout.addWidget(self._play_btn)

        # ── 后退 ──
        self._skip_back_btn = QPushButton()
        self._skip_back_btn.setObjectName("skipBackBtn")
        self._skip_back_btn.setIcon(QIcon(str(get_icon_path("skip_back"))))
        self._skip_back_btn.setIconSize(self._skip_back_btn.sizeHint() * 1.4)
        self._skip_back_btn.setToolTip("后退 5 秒")
        self._skip_back_btn.setCursor(Qt.PointingHandCursor)
        self._skip_back_btn.clicked.connect(self.skip_back_clicked.emit)
        layout.addWidget(self._skip_back_btn)

        # ── 前进 ──
        self._skip_forward_btn = QPushButton()
        self._skip_forward_btn.setObjectName("skipForwardBtn")
        self._skip_forward_btn.setIcon(QIcon(str(get_icon_path("skip_forward"))))
        self._skip_forward_btn.setIconSize(self._skip_forward_btn.sizeHint() * 1.4)
        self._skip_forward_btn.setToolTip("前进 5 秒")
        self._skip_forward_btn.setCursor(Qt.PointingHandCursor)
        self._skip_forward_btn.clicked.connect(self.skip_forward_clicked.emit)
        layout.addWidget(self._skip_forward_btn)

        # ── 当前时间 ──
        self._current_time = QLabel("00:00")
        self._current_time.setObjectName("currentTime")
        self._current_time.setFixedWidth(44)
        layout.addWidget(self._current_time)

        # ── 进度条 ──
        self._seek_slider = QSlider(Qt.Horizontal)
        self._seek_slider.setObjectName("seekSlider")
        self._seek_slider.setRange(0, 0)
        self._seek_slider.setTracking(False)
        self._seek_slider.sliderMoved.connect(self._on_seek)
        self._seek_slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        layout.addWidget(self._seek_slider, 1)

        # ── 总时长 ──
        self._total_time = QLabel("00:00")
        self._total_time.setObjectName("totalTime")
        self._total_time.setFixedWidth(44)
        layout.addWidget(self._total_time)

        # ── 音量按钮 ──
        self._volume_btn = QPushButton()
        self._volume_btn.setObjectName("volumeBtn")
        self._volume_btn.setIcon(QIcon(str(get_icon_path("volume"))))
        self._volume_btn.setIconSize(self._volume_btn.sizeHint() * 1.3)
        self._volume_btn.setToolTip("静音切换")
        self._volume_btn.setCursor(Qt.PointingHandCursor)
        self._volume_btn.clicked.connect(self._toggle_mute)
        layout.addWidget(self._volume_btn)

        # ── 音量滑块 ──
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setObjectName("volumeSlider")
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setFixedWidth(80)
        self._volume_slider.valueChanged.connect(self.volume_changed.emit)
        layout.addWidget(self._volume_slider)

        # ── 倍速 ──
        self._rate_combo = QComboBox()
        self._rate_combo.setObjectName("rateCombo")
        rates = ["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"]
        for r in rates:
            self._rate_combo.addItem(r)
        self._rate_combo.setCurrentIndex(2)  # 1.0x
        self._rate_combo.currentIndexChanged.connect(self._on_rate_changed)
        self._rate_combo.setFixedWidth(64)
        layout.addWidget(self._rate_combo)

    # ── 公有方法 ──

    def set_playing(self, playing: bool):
        """更新播放状态图标"""
        self._is_playing = playing
        icon_name = "pause" if playing else "play"
        self._play_btn.setIcon(QIcon(str(get_icon_path(icon_name))))

    def set_duration(self, ms: int):
        """设置视频总时长"""
        self._duration = ms
        self._seek_slider.setRange(0, ms)
        self._total_time.setText(ms_to_time_str(ms))

    def set_position(self, ms: int):
        """更新进度条位置和当前时间"""
        self._seek_slider.blockSignals(True)
        self._seek_slider.setValue(ms)
        self._seek_slider.blockSignals(False)
        self._current_time.setText(ms_to_time_str(ms))

    def set_volume(self, value: int):
        """设置音量"""
        self._volume_slider.blockSignals(True)
        self._volume_slider.setValue(value)
        self._volume_slider.blockSignals(False)

    def set_muted(self, muted: bool):
        """更新静音图标"""
        icon_name = "volume_mute" if muted else "volume"
        self._volume_btn.setIcon(QIcon(str(get_icon_path(icon_name))))

    def set_rate(self, rate: float):
        """设置倍速"""
        rate_str = f"{rate:.2f}x".replace(".00", ".0")
        for i in range(self._rate_combo.count()):
            if self._rate_combo.itemText(i) == rate_str:
                self._rate_combo.setCurrentIndex(i)
                return

    # ── 内部方法 ──

    def _on_seek(self, value: int):
        """进度条拖动"""
        self._current_time.setText(ms_to_time_str(value))
        self.seek_requested.emit(value)

    def _toggle_mute(self):
        """静音切换"""
        muted = self._volume_slider.value() == 0
        self.volume_changed.emit(0 if not muted else 80)

    def _on_rate_changed(self, index: int):
        """倍速切换"""
        text = self._rate_combo.itemText(index)
        rate = float(text.replace("x", ""))
        self.rate_changed.emit(rate)
