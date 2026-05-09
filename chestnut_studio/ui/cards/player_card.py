"""视频播放卡片模块"""

import os

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QColor, QFont, QResizeEvent
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


class VideoView(QGraphicsView):
    """视频视图，自动 fitInView 保持宽高比居中显示"""

    def __init__(self, scene, video_item, parent=None):
        super().__init__(scene, parent)
        self._video_item = video_item

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self._fit_video()

    def wheelEvent(self, event):
        event.ignore()

    def fit_video(self):
        """公开方法：视频画面居中铺满，保持宽高比"""
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
    ab_loop_changed = Signal(int, int)  # AB 循环状态变化 (a_point, b_point)，-1 表示未设置

    default_area = Qt.LeftDockWidgetArea

    def __init__(self, parent=None):
        super().__init__("视频预览", parent)
        self._video_path = ""
        self._duration = 0
        self._is_playing = False
        self._volume = 80
        self._playback_rate = 1.0

        # AB 循环状态
        self._ab_loop_a = -1  # A 点位置（ms），-1 表示未设置
        self._ab_loop_b = -1  # B 点位置（ms），-1 表示未设置
        self._ab_loop_enabled = False  # AB 循环是否激活

        self._setup_ui()
        self._setup_player()
        self._connect_signals()

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

        # 空状态提示（视频加载后隐藏）
        self._hint_label = QLabel("拖入视频文件 或 Ctrl+O 打开", content)
        self._hint_label.setAlignment(Qt.AlignCenter)
        self._hint_label.setStyleSheet("""
            QLabel {
                color: #52525b;
                font-size: 11pt;
                background: transparent;
            }
        """)

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
        # 监听视频尺寸变化，自动适配画面
        self._video_item.nativeSizeChanged.connect(self._on_video_size_changed)

    def resizeEvent(self, event):
        """保持提示标签居中"""
        super().resizeEvent(event)
        if self._hint_label.isVisible():
            parent_size = self.widget().size()
            self._hint_label.setGeometry(0, 0, parent_size.width(), parent_size.height())

    # ========== 公有方法 ==========

    def open_video(self, path: str) -> bool:
        """打开视频文件"""
        if not os.path.exists(path):
            return False

        self._video_path = path
        self._player.setSource(QUrl.fromLocalFile(path))
        self._player.pause()
        self._hint_label.hide()

        # 清除 AB 循环
        self.clear_ab_loop()

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

    # ========== AB 循环 ==========

    def set_ab_loop_a(self):
        """设置 A 点为当前播放位置"""
        self._ab_loop_a = self._player.position()
        self._check_ab_loop()
        self.ab_loop_changed.emit(self._ab_loop_a, self._ab_loop_b)

    def set_ab_loop_b(self):
        """设置 B 点为当前播放位置"""
        self._ab_loop_b = self._player.position()
        self._check_ab_loop()
        self.ab_loop_changed.emit(self._ab_loop_a, self._ab_loop_b)

    def clear_ab_loop(self):
        """清除 AB 循环"""
        self._ab_loop_a = -1
        self._ab_loop_b = -1
        self._ab_loop_enabled = False
        self.ab_loop_changed.emit(-1, -1)

    def get_ab_loop_points(self) -> tuple[int, int]:
        """获取 AB 循环点"""
        return self._ab_loop_a, self._ab_loop_b

    def is_ab_loop_enabled(self) -> bool:
        """AB 循环是否激活"""
        return self._ab_loop_enabled

    def _check_ab_loop(self):
        """检查 AB 循环是否可以激活"""
        if self._ab_loop_a >= 0 and self._ab_loop_b >= 0:
            # 确保 A < B
            if self._ab_loop_a > self._ab_loop_b:
                self._ab_loop_a, self._ab_loop_b = self._ab_loop_b, self._ab_loop_a
            # 如果 A == B，不激活循环
            if self._ab_loop_a == self._ab_loop_b:
                self._ab_loop_enabled = False
            else:
                self._ab_loop_enabled = True

    # ========== 内部事件 ==========

    def _on_position_changed(self, position: int):
        # AB 循环：如果播放位置超过 B 点，跳回 A 点
        if self._ab_loop_enabled and position >= self._ab_loop_b:
            self._player.setPosition(self._ab_loop_a)
            return  # 不发射 position_changed，等待下一帧

        self.position_changed.emit(position)

    def _on_duration_changed(self, duration: int):
        self._duration = duration
        self.duration_changed.emit(duration)

    def _on_playback_state_changed(self, state):
        self._is_playing = state == QMediaPlayer.PlayingState
        self.playback_state_changed.emit(self._is_playing)

    def _on_video_size_changed(self, size):
        """视频尺寸变化时自动适配画面"""
        # 延迟一帧调用 fitInView，确保布局已完成
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, self._view.fit_video)
