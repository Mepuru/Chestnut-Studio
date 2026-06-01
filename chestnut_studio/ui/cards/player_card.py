"""视频播放器组件模块

视频播放核心组件，使用 QMediaPlayer + QVideoWidget。
"""

import os

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from chestnut_studio.ui.player_controls import PlayerControls


class PlayerCard(QWidget):
    """视频播放器组件

    纯 QWidget，包含视频画面和播放控制栏。
    无 QDockWidget 依赖，无 AB 循环/字幕叠加等无关功能。
    """

    position_changed = Signal(int)
    duration_changed = Signal(int)
    video_opened = Signal(str)
    playback_state_changed = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._video_path = ""
        self._duration = 0
        self._is_playing = False
        self._volume = 80
        self._muted = False
        self._playback_rate = 1.0

        self._setup_ui()
        self._setup_player()

    def _setup_ui(self):
        self.setObjectName("playerCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── 视频画面 ──
        self._video_widget = QVideoWidget()
        self._video_widget.setObjectName("videoWidget")
        self._video_widget.setStyleSheet("background-color: #000000;")
        layout.addWidget(self._video_widget, 1)

        # ── 空状态提示 ──
        self._hint_label = QLabel("拖入视频文件 或 Ctrl+O 打开")
        self._hint_label.setObjectName("videoHint")
        self._hint_label.setAlignment(Qt.AlignCenter)
        self._hint_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        # 用绝对定位覆盖在视频区域上方
        self._hint_label.setGeometry(0, 0, self.width(), self.height())

        # ── 播放控制栏 ──
        self._controls = PlayerControls(self)
        self._controls.setObjectName("playerControlsBar")
        layout.addWidget(self._controls)

        # 连接控制栏信号
        self._controls.play_pause_clicked.connect(self._toggle_play_pause)
        self._controls.skip_back_clicked.connect(lambda: self._skip(-5000))
        self._controls.skip_forward_clicked.connect(lambda: self._skip(5000))
        self._controls.seek_requested.connect(self.set_position)
        self._controls.volume_changed.connect(self.set_volume)
        self._controls.rate_changed.connect(self.set_playback_rate)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 保持提示标签覆盖在视频区域
        video_height = self._video_widget.height()
        self._hint_label.setGeometry(0, 0, self.width(), video_height)

    def _setup_player(self):
        """初始化 QMediaPlayer"""
        self._audio_output = QAudioOutput()
        self._audio_output.setVolume(self._volume / 100.0)

        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._player.setVideoOutput(self._video_widget)

        # 信号连接
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)
        self._player.positionChanged.connect(self._on_position_changed)

    # ── 公有方法 ──

    def open_video(self, path: str) -> bool:
        """打开视频文件"""
        if not os.path.exists(path):
            return False

        self._video_path = path
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.pause()
        self._hint_label.hide()

        self.video_opened.emit(path)
        return True

    def play(self):
        self._player.play()

    def pause(self):
        self._player.pause()

    def play_pause(self):
        """播放/暂停切换"""
        if self._is_playing:
            self.pause()
        else:
            self.play()

    def stop(self):
        self._player.stop()

    def set_position(self, ms: int):
        self._player.setPosition(ms)

    def set_volume(self, value: int):
        self._volume = max(0, min(100, value))
        self._audio_output.setVolume(self._volume / 100.0)
        self._muted = value == 0
        self._controls.set_muted(self._muted)
        self._controls.set_volume(value)

    def toggle_mute(self):
        self.set_volume(0 if self._volume > 0 else 80)

    def set_playback_rate(self, rate: float):
        self._playback_rate = max(0.1, min(2.0, rate))
        self._player.setPlaybackRate(self._playback_rate)
        self._controls.set_rate(rate)

    def get_position(self) -> int:
        return self._player.position()

    def get_duration(self) -> int:
        return self._duration

    def is_playing(self) -> bool:
        return self._is_playing

    def get_video_path(self) -> str:
        return self._video_path

    # ── 内部方法 ──

    def _toggle_play_pause(self):
        self.play_pause()

    def _skip(self, ms: int):
        new_pos = max(0, min(self._player.position() + ms, self._duration))
        self.set_position(new_pos)

    def _on_position_changed(self, position: int):
        self._controls.set_position(position)
        self.position_changed.emit(position)

    def _on_duration_changed(self, duration: int):
        self._duration = duration
        self._controls.set_duration(duration)
        self.duration_changed.emit(duration)

    def _on_playback_state_changed(self, state):
        self._is_playing = state == QMediaPlayer.PlayingState
        self._controls.set_playing(self._is_playing)
        self.playback_state_changed.emit(self._is_playing)
