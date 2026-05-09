"""全局拖放覆盖层模块

当用户从外部拖拽文件到窗口上时，显示全屏半透明覆盖层，
中央显示一个圆角卡片，根据文件后缀自动识别类型并切换样式。
"""

import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

VIDEO_EXTENSIONS = {".mp4", ".avi", ".flv", ".mkv", ".mov", ".wmv", ".mp3", ".wav", ".aac", ".flac", ".ogg"}
SUBTITLE_EXTENSIONS = {".srt", ".ass", ".vtt", ".lrc"}

_CARD_STYLE = """
    QLabel {{
        background: #18181b;
        border: 3px dashed {border};
        border-radius: 20px;
        color: {color};
        font-size: 16pt;
        padding: 40px 60px;
    }}
"""


class DragOverlay(QWidget):
    """全屏拖放覆盖层

    信号：
        video_dropped(str): 视频文件被放下
        subtitle_dropped(str): 字幕文件被放下
    """

    video_dropped = Signal(str)
    subtitle_dropped = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: rgba(0, 0, 0, 170);")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self._card = QLabel()
        self._card.setAlignment(Qt.AlignCenter)
        self._card.setMinimumSize(360, 200)
        self._card.setStyleSheet(_CARD_STYLE.format(border="#3f3f46", color="#71717a"))
        self._card.setText("拖放文件到此处")
        layout.addWidget(self._card, alignment=Qt.AlignCenter)

    def _apply_style(self, border: str, color: str, text: str):
        self._card.setStyleSheet(_CARD_STYLE.format(border=border, color=color))
        self._card.setText(text)

    def update_for_files(self, paths: list[str]):
        """根据拖入的文件类型切换卡片样式"""
        file_type = "unknown"
        for p in paths:
            ext = os.path.splitext(p)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                file_type = "video"
                break
            if ext in SUBTITLE_EXTENSIONS:
                file_type = "subtitle"
                break

        if file_type == "video":
            self._apply_style("#3b82f6", "#93c5fd", "🎬  放开以加载视频")
        elif file_type == "subtitle":
            self._apply_style("#10b981", "#6ee7b7", "📝  放开以导入字幕")
        else:
            self._apply_style("#ef4444", "#fca5a5", "不支持的文件格式")

    def handle_drop(self, paths: list[str]):
        """处理文件放下事件，根据类型分发信号"""
        for path in paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in VIDEO_EXTENSIONS:
                self.video_dropped.emit(path)
            elif ext in SUBTITLE_EXTENSIONS:
                self.subtitle_dropped.emit(path)
        self.hide()
