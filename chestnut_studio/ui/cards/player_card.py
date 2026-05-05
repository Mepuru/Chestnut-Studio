"""视频播放卡片模块"""

import os

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QFont, QResizeEvent
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QGraphicsVideoItem
from PySide6.QtWidgets import (
    QDockWidget,
    QGraphicsScene,
    QGraphicsTextItem,
    QGraphicsView,
    QLabel,
    QVBoxLayout,
    QWidget,
)

VIDEO_EXTENSIONS = {".mp4", ".avi", ".flv", ".mkv", ".mov", ".wmv", ".mp3", ".wav", ".aac", ".flac", ".ogg"}
SUBTITLE_EXTENSIONS = {".srt", ".ass", ".vtt", ".lrc"}


class VideoView(QGraphicsView):
    """视频视图，自动 fitInView 保持宽高比居中显示"""

    def __init__(self, scene, video_item, parent=None):
        super().__init__(scene, parent)
        self._video_item = video_item

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._fit_video()

    def _fit_video(self):
        """视频画面居中铺满，保持宽高比"""
        bounds = self._video_item.boundingRect()
        if bounds.width() <= 0 or bounds.height() <= 0:
            return
        self.fitInView(self._video_item, Qt.KeepAspectRatio)


class PlayerCard(QDockWidget):
    """视频播放卡片

    功能：
    - 视频渲染（QGraphicsVideoItem）+ 字幕叠加预览（QGraphicsTextItem）
    - 右下角时间标签（当前时间 / 总时长）
    - 拖放打开文件
    - 播放控制全部由工具栏负责
    """

    # 信号
    position_changed = Signal(int)
    duration_changed = Signal(int)
    video_opened = Signal(str)
    playback_state_changed = Signal(bool)
    subtitle_dropped = Signal(str)

    default_area = Qt.LeftDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("视频预览", parent)
        self._video_path = ""
        self._duration = 0
        self._is_playing = False
        self._volume = 80
        self._playback_rate = 1.0

        self._setup_ui()
        self._setup_player()
        self._connect_signals()

        self.setAcceptDrops(True)

    def _setup_ui(self):
        """初始化 UI"""
        content = QWidget()
        content.setStyleSheet("""
            QWidget {
                background: #000000;
                border: 1px solid #27272a;
                border-top: none;
            }
        """)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        self._scene = QGraphicsScene(self)

        self._video_item = QGraphicsVideoItem()
        self._scene.addItem(self._video_item)

        self._subtitle_item = QGraphicsTextItem()
        self._subtitle_item.setDefaultTextColor(QColor("#FFFFFF"))
        self._subtitle_item.setFont(QFont("Microsoft YaHei", 24, QFont.Bold))
        self._subtitle_item.setZValue(1)
        self._subtitle_item.setVisible(False)
        self._scene.addItem(self._subtitle_item)

        self._view = VideoView(self._scene, self._video_item)
        self._view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._view.setStyleSheet("QGraphicsView { background: #000000; border: none; }")

        layout.addWidget(self._view)

        # 时间标签（叠加在视频右下角）
        self._time_label = QLabel("00:00 / 00:00", content)
        self._time_label.setStyleSheet("""
            QLabel {
                color: #cccccc;
                font-size: 10pt;
                font-family: Consolas, monospace;
                background: rgba(0, 0, 0, 120);
                padding: 2px 8px;
            }
        """)
        self._time_label.adjustSize()

        self.setWidget(content)

    def _setup_player(self):
        """初始化 QMediaPlayer"""
        self._audio_output = QAudioOutput()
        self._audio_output.setVolume(self._volume / 100.0)

        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio_output)
        self._player.setVideoOutput(self._video_item)

    def _connect_signals(self):
        self._player.positionChanged.connect(self._on_position_changed)
        self._player.durationChanged.connect(self._on_duration_changed)
        self._player.playbackStateChanged.connect(self._on_playback_state_changed)

    def resizeEvent(self, event: QResizeEvent):
        """保持时间标签在右下角"""
        super().resizeEvent(event)
        self._reposition_time_label()

    def _reposition_time_label(self):
        """将时间标签定位到右下角"""
        parent_size = self.widget().size()
        label_size = self._time_label.sizeHint()
        x = parent_size.width() - label_size.width() - 8
        y = parent_size.height() - label_size.height() - 8
        self._time_label.move(x, y)

    # ========== 公有方法 ==========

    def open_video(self, path: str) -> bool:
        """打开视频文件"""
        if not os.path.exists(path):
            return False

        self._video_path = path
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.pause()
        self.video_opened.emit(path)
        return True

    def play(self):
        self._player.play()

    def pause(self):
        self._player.pause()

    def stop(self):
        self._player.stop()
        self._player.setPosition(0)

    def play_pause(self):
        if self._is_playing:
            self.pause()
        else:
            self.play()

    def set_position(self, ms: int):
        self._player.setPosition(ms)

    def set_volume(self, value: int):
        self._volume = max(0, min(100, value))
        self._audio_output.setVolume(self._volume / 100.0)

    def set_playback_rate(self, rate: float):
        self._playback_rate = max(0.1, min(2.0, rate))
        self._player.setPlaybackRate(self._playback_rate)

    def set_muted(self, muted: bool):
        self._audio_output.setMuted(muted)

    def update_subtitle_overlay(self, text: str) -> None:
        """更新字幕叠加显示"""
        if not text:
            self._subtitle_item.setVisible(False)
            return

        self._subtitle_item.setPlainText(text)
        self._subtitle_item.setVisible(True)

        view_size = self._view.viewport().size()
        text_rect = self._subtitle_item.boundingRect()
        x = (view_size.width() - text_rect.width()) / 2
        y = view_size.height() - text_rect.height() - 20
        self._subtitle_item.setPos(x, y)

    def get_position(self) -> int:
        return self._player.position()

    def get_duration(self) -> int:
        return self._duration

    def is_playing(self) -> bool:
        return self._is_playing

    # ========== 内部事件 ==========

    def _on_position_changed(self, position: int):
        self._time_label.setText(f"{self._ms_to_str(position)} / {self._ms_to_str(self._duration)}")
        self.position_changed.emit(position)

    def _on_duration_changed(self, duration: int):
        self._duration = duration
        self._time_label.setText(f"00:00 / {self._ms_to_str(duration)}")
        self.duration_changed.emit(duration)

    def _on_playback_state_changed(self, state):
        self._is_playing = state == QMediaPlayer.PlayingState
        self.playback_state_changed.emit(self._is_playing)

    # ========== 拖放 ==========

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            ext = os.path.splitext(path)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                self.open_video(path)
                return
            elif ext in SUBTITLE_EXTENSIONS:
                self.subtitle_dropped.emit(path)
                return

    # ========== 工具方法 ==========

    @staticmethod
    def _ms_to_str(ms: int) -> str:
        """毫秒 -> MM:SS 格式"""
        if ms < 0:
            ms = 0
        total_seconds = ms // 1000
        m, s = divmod(total_seconds, 60)
        return f"{m:02d}:{s:02d}"
