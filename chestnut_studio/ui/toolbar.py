"""工具栏模块"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QPushButton,
    QSlider,
    QToolBar,
    QWidget,
)


class ToolBar(QToolBar):
    """主工具栏

    功能：
    - 打开文件按钮
    - 播放控制（播放/暂停、静音、音量）
    - 时间显示（当前时间 / 总时长）
    - 进度条
    - 倍速选择
    """

    # 信号
    play_clicked = Signal()  # 播放/暂停
    mute_clicked = Signal()  # 静音切换
    volume_changed = Signal(int)  # 音量变化 0-100
    position_changed = Signal(int)  # 进度条拖拽 (ms)
    rate_changed = Signal(float)  # 倍速变化

    def __init__(self, parent=None):
        super().__init__(parent)
        self._duration = 0
        self._is_muted = False
        self._slider_pressed = False
        self._setup_ui()

    def _setup_ui(self):
        """初始化 UI"""
        self.setMovable(False)
        self.setFloatable(False)

        # 播放/暂停按钮
        self._play_btn = QPushButton("播放")
        self._play_btn.setFixedWidth(56)
        self._play_btn.setToolTip("播放/暂停 (Space)")
        self._play_btn.clicked.connect(self.play_clicked.emit)

        # 静音按钮
        self._mute_btn = QPushButton("静音")
        self._mute_btn.setFixedWidth(56)
        self._mute_btn.setToolTip("静音/取消静音")
        self._mute_btn.clicked.connect(self._on_mute_clicked)

        # 音量滑块
        self._volume_slider = QSlider(Qt.Horizontal)
        self._volume_slider.setRange(0, 100)
        self._volume_slider.setValue(80)
        self._volume_slider.setFixedWidth(80)
        self._volume_slider.setToolTip("音量: 80%")
        self._volume_slider.valueChanged.connect(self._on_volume_changed)

        # 进度条
        self._progress_slider = QSlider(Qt.Horizontal)
        self._progress_slider.setRange(0, 0)
        self._progress_slider.setMinimumWidth(120)
        self._progress_slider.setMaximumWidth(360)
        self._progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self._progress_slider.sliderReleased.connect(self._on_slider_released)
        self._progress_slider.valueChanged.connect(self._on_slider_value_changed)

        # 时间标签
        self._time_label = QLabel("00:00 / 00:00")
        self._time_label.setFixedWidth(110)
        self._time_label.setAlignment(Qt.AlignCenter)
        self._time_label.setStyleSheet("color: #a1a1aa; font-size: 9pt;")

        # 倍速选择
        self._rate_combo = QComboBox()
        self._rate_combo.setFixedWidth(80)
        self._rate_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self._rate_combo.setCurrentText("1.0x")
        self._rate_combo.currentTextChanged.connect(self._on_rate_changed)

        # 添加到工具栏
        self.addWidget(self._play_btn)
        self._add_spacing(4)
        self.addWidget(self._mute_btn)
        self._add_spacing(4)
        self.addWidget(self._volume_slider)
        self._add_separator()
        self.addWidget(self._progress_slider)
        self._add_separator()
        self.addWidget(self._time_label)
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
        sep.setStyleSheet("background: #27272a; margin: 0 4px;")
        self.addWidget(sep)

    def _add_spacing(self, width: int):
        """添加间距"""
        spacer = QWidget()
        spacer.setFixedSize(width, 1)
        spacer.setStyleSheet("background: transparent;")
        self.addWidget(spacer)

    # ========== 公有方法 ==========

    def set_duration(self, ms: int):
        """设置视频总时长

        Args:
            ms: 总时长（毫秒）
        """
        self._duration = ms
        self._progress_slider.setMaximum(ms)
        self._time_label.setText(f"00:00 / {self._ms_to_str(ms)}")

    def update_position(self, ms: int):
        """更新当前播放位置

        Args:
            ms: 当前位置（毫秒）
        """
        if not self._slider_pressed:
            self._progress_slider.blockSignals(True)
            self._progress_slider.setValue(ms)
            self._progress_slider.blockSignals(False)
        self._time_label.setText(f"{self._ms_to_str(ms)} / {self._ms_to_str(self._duration)}")

    def set_playing(self, playing: bool):
        """设置播放状态

        Args:
            playing: 是否正在播放
        """
        if playing:
            self._play_btn.setText("暂停")
            self._play_btn.setToolTip("暂停 (Space)")
        else:
            self._play_btn.setText("播放")
            self._play_btn.setToolTip("播放 (Space)")

    def set_volume(self, value: int):
        """设置音量值

        Args:
            value: 音量 0-100
        """
        self._volume_slider.blockSignals(True)
        self._volume_slider.setValue(value)
        self._volume_slider.blockSignals(False)
        self._volume_slider.setToolTip(f"音量: {value}%")

    def set_muted(self, muted: bool):
        """设置静音状态

        Args:
            muted: 是否静音
        """
        self._is_muted = muted
        if muted:
            self._mute_btn.setText("取消静音")
        else:
            self._mute_btn.setText("静音")

    def set_playback_rate(self, rate: float):
        """设置倍速

        Args:
            rate: 倍速值
        """
        text = f"{rate}x"
        idx = self._rate_combo.findText(text)
        if idx >= 0:
            self._rate_combo.setCurrentIndex(idx)

    # ========== 内部方法 ==========

    def _on_mute_clicked(self):
        """静音按钮点击"""
        self._is_muted = not self._is_muted
        self.set_muted(self._is_muted)
        self.mute_clicked.emit()

    def _on_volume_changed(self, value: int):
        """音量滑块变化"""
        self._volume_slider.setToolTip(f"音量: {value}%")
        self.volume_changed.emit(value)

    def _on_slider_pressed(self):
        """进度条按下"""
        self._slider_pressed = True

    def _on_slider_released(self):
        """进度条释放"""
        self._slider_pressed = False
        self.position_changed.emit(self._progress_slider.value())

    def _on_slider_value_changed(self, value: int):
        """进度条值变化"""
        if self._slider_pressed:
            self._time_label.setText(f"{self._ms_to_str(value)} / {self._ms_to_str(self._duration)}")

    def _on_rate_changed(self, text: str):
        """倍速选择变化"""
        try:
            rate = float(text.replace("x", ""))
            self.rate_changed.emit(rate)
        except ValueError:
            pass

    @staticmethod
    def _ms_to_str(ms: int) -> str:
        """毫秒 -> MM:SS 格式"""
        if ms < 0:
            ms = 0
        total_seconds = ms // 1000
        m, s = divmod(total_seconds, 60)
        return f"{m:02d}:{s:02d}"
